"""
FastAPI Review Backend for KarlCam
Handles review workflow for Gemini-labeled images using Cloud Storage and SQL Database
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import logging
import os
import sys
from pathlib import Path
from google.cloud import storage
from dotenv import load_dotenv

# Add parent directory to path to import db module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.manager import DatabaseManager
from db.connection import get_db_connection, execute_query
from psycopg2.extras import RealDictCursor

# Load environment variables from .env file only in development
# In Cloud Run, environment variables are set directly
if os.environ.get('GAE_ENV', '').startswith('standard') or not os.environ.get('K_SERVICE'):
    # Only load .env if not running in Cloud Run
    load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="KarlCam Review API",
    description="Backend for reviewing Gemini-labeled fog detection images",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "error_code": "VALIDATION_ERROR",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'karlcam-fog-data')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Initialize Cloud Storage client
storage_client = storage.Client()

# Pydantic models
class FogLevel(str, Enum):
    none = "none"
    light = "light"
    moderate = "moderate"  
    heavy = "heavy"

class ReviewAction(str, Enum):
    approve = "approve"
    reject = "reject"
    correct = "correct"

class GeminiLabel(BaseModel):
    fog_score: float = Field(ge=0, le=100)
    fog_level: str
    confidence: float = Field(ge=0, le=1.0)
    reasoning: Optional[str] = None
    visibility_estimate: Optional[str] = None
    weather_conditions: Optional[List[str]] = []

class WebcamInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""

class ImageForReview(BaseModel):
    id: str
    filename: str
    timestamp: Optional[str]
    webcam_info: WebcamInfo
    gemini_label: GeminiLabel
    image_url: str
    status: str = "pending"

class ReviewDecision(BaseModel):
    action: ReviewAction
    corrected_label: Optional[GeminiLabel] = None
    reviewer_notes: Optional[str] = None
    confidence_override: Optional[float] = None

class BulkReviewRequest(BaseModel):
    image_ids: List[str]
    action: ReviewAction
    reviewer_notes: Optional[str] = None

class ReviewStats(BaseModel):
    total_pending: int
    total_reviewed: int
    total_approved: int
    total_rejected: int
    avg_confidence: float
    low_confidence_count: int
    fog_detected_count: int

# Database Backend
class ReviewBackend:
    """Cloud Storage and Database based review backend"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.bucket_name = BUCKET_NAME
    
    def get_pending_images(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None,
        confidence_filter: Optional[str] = None,
        cameras: Optional[str] = None,
        time_range: Optional[str] = None,
        fog_levels: Optional[str] = None
    ) -> List[ImageForReview]:
        """Get images from database for review"""
        try:
            # Calculate days from time_range
            days = 7  # default
            if time_range:
                if time_range == '1h':
                    days = 1/24
                elif time_range == '24h':
                    days = 1
                elif time_range == '3d':
                    days = 3
                elif time_range == '7d':
                    days = 7
                elif time_range == '30d':
                    days = 30
                elif time_range == 'all':
                    days = 365  # Use a large number for "all"
            
            # Get recent images with labels using DatabaseManager
            all_images = self.db_manager.get_recent_images(days=days)
            
            # Filter by cameras if provided
            if cameras:
                camera_list = cameras.split(',')
                all_images = [img for img in all_images if img.get('webcam_name') in camera_list]
            
            # Filter by fog levels if provided
            if fog_levels:
                fog_level_list = fog_levels.split(',')
                filtered_images = []
                for img in all_images:
                    labels = img.get('labels', [])
                    if labels and any(label.get('fog_level') in fog_level_list for label in labels):
                        filtered_images.append(img)
                all_images = filtered_images
            
            # Filter by confidence if provided
            if confidence_filter:
                confidence_filters = confidence_filter.split(',')
                filtered_images = []
                for img in all_images:
                    labels = img.get('labels', [])
                    if not labels:
                        continue
                    label = labels[0]  # Use first label
                    conf = label.get('confidence', 0)
                    
                    for cf in confidence_filters:
                        if cf == 'low' and conf < 0.7:
                            filtered_images.append(img)
                            break
                        elif cf == 'medium' and 0.7 <= conf < 0.9:
                            filtered_images.append(img)
                            break
                        elif cf == 'high' and conf >= 0.9:
                            filtered_images.append(img)
                            break
                all_images = filtered_images
            
            # Apply pagination
            start = offset or 0
            end = start + (limit or 50)
            paginated_images = all_images[start:end]
            
            # Convert to the expected format
            images = []
            for img in paginated_images:
                labels = img.get('labels', []) or []
                # Filter out null labels and handle multiple labelers
                valid_labels = [label for label in labels if label is not None]
                
                if valid_labels:
                    # Image has labels - create an entry for each labeler or use primary label
                    # For now, prefer Gemini labels, then fall back to others
                    primary_label = None
                    for label in valid_labels:
                        if label.get('labeler') and 'gemini' in label.get('labeler', '').lower():
                            primary_label = label
                            break
                    
                    # If no Gemini label, use first available label
                    if not primary_label:
                        primary_label = valid_labels[0]
                    
                    gemini_label = GeminiLabel(
                        fog_score=primary_label.get('fog_score', 0),
                        fog_level=primary_label.get('fog_level', 'Unknown'), 
                        confidence=primary_label.get('confidence', 0),
                        reasoning='',  # Not included in aggregated query
                        visibility_estimate='',  # Not included in aggregated query
                        weather_conditions=[]  # Not included in aggregated query
                    )
                    status = "pending"
                else:
                    # Image has no labels - show placeholder values
                    gemini_label = GeminiLabel(
                        fog_score=0,
                        fog_level='Not Labeled', 
                        confidence=0,
                        reasoning='',
                        visibility_estimate='',
                        weather_conditions=[]
                    )
                    status = "unlabeled"
                
                images.append(ImageForReview(
                    id=str(img['id']),
                    filename=img['image_filename'],
                    timestamp=img['timestamp'].isoformat() if img['timestamp'] else None,
                    webcam_info=WebcamInfo(
                        id=img['webcam_id'] or 'unknown',
                        name=img.get('webcam_name') or f"Camera {img['webcam_id']}" or 'Unknown Camera',
                        description=''  # Not included in aggregated query
                    ),
                    gemini_label=gemini_label,
                    image_url=f"/api/images/{img['image_filename']}",
                    status=status,
                    # Store all labels for potential future use
                    # all_labels=valid_labels  # Could add this if the model supports it
                ))
            
            return images
                    
        except Exception as e:
            logger.error(f"Error fetching pending images: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch images")
    
    def get_image_by_id(self, image_id: str) -> Optional[ImageForReview]:
        """Get specific image by ID"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            ic.id,
                            ic.image_filename,
                            ic.timestamp,
                            ic.webcam_id,
                            il.fog_score,
                            il.fog_level,
                            il.confidence,
                            il.reasoning,
                            il.visibility_estimate,
                            il.weather_conditions,
                            w.name as webcam_name,
                            w.description as webcam_description
                        FROM image_collections ic
                        LEFT JOIN webcams w ON ic.webcam_id = w.id
                        LEFT JOIN image_labels il ON ic.id = il.image_id
                        WHERE ic.id = %s
                    """, (image_id,))
                    
                    row = cur.fetchone()
                    if not row:
                        return None
                    
                    return ImageForReview(
                        id=str(row['id']),
                        filename=row['image_filename'],
                        timestamp=row['timestamp'].isoformat() if row['timestamp'] else None,
                        webcam_info=WebcamInfo(
                            id=row['webcam_id'] or 'unknown',
                            name=row.get('webcam_name') or f"Camera {row['webcam_id']}" or 'Unknown Camera',
                            description=row.get('webcam_description') or ''
                        ),
                        gemini_label=GeminiLabel(
                            fog_score=row['fog_score'],
                            fog_level=row['fog_level'], 
                            confidence=row['confidence'],
                            reasoning=row['reasoning'],
                            visibility_estimate=row['visibility_estimate'],
                            weather_conditions=row['weather_conditions'] or []
                        ),
                        image_url=f"/api/images/{row['image_filename']}",
                        status="pending"
                    )
                    
        except Exception as e:
            logger.error(f"Error fetching image {image_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch image")
    
    def process_review_decision(self, image_id: str, decision: ReviewDecision) -> bool:
        """Process a review decision by updating database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create review record
                    cur.execute("""
                        INSERT INTO image_reviews (
                            image_collection_id,
                            review_action,
                            reviewer_notes,
                            confidence_override,
                            corrected_fog_score,
                            corrected_fog_level,
                            corrected_reasoning,
                            review_timestamp
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        image_id,
                        decision.action.value,
                        decision.reviewer_notes,
                        decision.confidence_override,
                        decision.corrected_label.fog_score if decision.corrected_label else None,
                        decision.corrected_label.fog_level if decision.corrected_label else None,
                        decision.corrected_label.reasoning if decision.corrected_label else None,
                        datetime.now()
                    ))
                    
                    # Update image collection status based on review
                    if decision.action == ReviewAction.approve:
                        new_status = 'approved'
                    elif decision.action == ReviewAction.reject:
                        new_status = 'rejected'
                    else:  # correct
                        new_status = 'corrected'
                        # Update the corrected values in image_collections if provided
                        if decision.corrected_label:
                            cur.execute("""
                                UPDATE image_collections SET
                                    fog_score = %s,
                                    fog_level = %s,
                                    reasoning = %s,
                                    confidence = %s,
                                    status = %s
                                WHERE id = %s
                            """, (
                                decision.corrected_label.fog_score,
                                decision.corrected_label.fog_level,
                                decision.corrected_label.reasoning,
                                decision.corrected_label.confidence,
                                new_status,
                                image_id
                            ))
                        else:
                            cur.execute("""
                                UPDATE image_collections SET status = %s WHERE id = %s
                            """, (new_status, image_id))
                    
                    if decision.action != ReviewAction.correct:
                        cur.execute("""
                            UPDATE image_collections SET status = %s WHERE id = %s
                        """, (new_status, image_id))
                    
                    conn.commit()
                    logger.info(f"Processed {decision.action.value} for image {image_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error processing review for {image_id}: {e}")
            return False
    
    def get_review_stats(self) -> ReviewStats:
        """Get review statistics from database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get overall stats
                    cur.execute("""
                        SELECT 
                            COUNT(CASE WHEN ic.status = 'success' THEN 1 END) as total_pending,
                            COUNT(CASE WHEN ic.status IN ('approved', 'rejected', 'corrected') THEN 1 END) as total_reviewed,
                            COUNT(CASE WHEN ic.status = 'approved' THEN 1 END) as total_approved,
                            COUNT(CASE WHEN ic.status = 'rejected' THEN 1 END) as total_rejected,
                            AVG(CASE WHEN ic.status = 'success' THEN ic.confidence END) as avg_confidence,
                            COUNT(CASE WHEN ic.status = 'success' AND ic.confidence < 0.7 THEN 1 END) as low_confidence_count,
                            COUNT(CASE WHEN ic.status = 'success' AND ic.fog_score > 50 THEN 1 END) as fog_detected_count
                        FROM image_collections ic
                    """)
                    
                    stats = cur.fetchone()
                    return ReviewStats(
                        total_pending=stats['total_pending'] or 0,
                        total_reviewed=stats['total_reviewed'] or 0,
                        total_approved=stats['total_approved'] or 0,
                        total_rejected=stats['total_rejected'] or 0,
                        avg_confidence=float(stats['avg_confidence'] or 0),
                        low_confidence_count=stats['low_confidence_count'] or 0,
                        fog_detected_count=stats['fog_detected_count'] or 0
                    )
                    
        except Exception as e:
            logger.error(f"Error fetching review stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch statistics")

# Initialize the backend
review_backend = ReviewBackend()

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "KarlCam Review API",
        "version": "1.0.0",
        "description": "Backend for reviewing Gemini-labeled images"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        stats = review_backend.get_review_stats()
        return {
            "status": "healthy",
            "pending_count": stats.total_pending,
            "database_connected": True,
            "cloud_storage_configured": BUCKET_NAME is not None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "pending_count": 0,
            "database_connected": False,
            "cloud_storage_configured": BUCKET_NAME is not None
        }

@app.get("/api/cameras")
async def get_cameras():
    """Get all available cameras from the database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, description, url, video_url, latitude, longitude, active, created_at
                    FROM webcams
                    ORDER BY name
                """)
                cameras = cur.fetchall()
                result = [
                {
                    "id": cam['id'],
                    "name": cam['name'],
                    "description": cam['description'],
                    "url": cam['url'],
                    "video_url": cam.get('video_url', ''),
                    "latitude": float(cam['latitude']) if cam['latitude'] else 37.7749,
                    "longitude": float(cam['longitude']) if cam['longitude'] else -122.4194,
                    "active": cam.get('active', True),
                    "created_at": cam['created_at'].isoformat() if cam['created_at'] else None
                }
                for cam in cameras
            ]
            conn.close()
            return result
    except Exception as e:
        logger.error(f"Error fetching cameras: {e}")
        # Return empty list if database not connected
        return []

@app.post("/api/cameras")
async def create_camera(camera_data: dict):
    """Create a new camera"""
    try:
        # Generate a unique ID for the camera
        import uuid
        camera_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO webcams (id, name, description, url, video_url, latitude, longitude, active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, name, description, url, video_url, latitude, longitude, active, created_at
                """, (
                    camera_id,
                    camera_data['name'], 
                    camera_data['description'], 
                    camera_data['url'], 
                    camera_data.get('video_url', ''),
                    camera_data.get('latitude', 37.7749),
                    camera_data.get('longitude', -122.4194),
                    camera_data.get('active', True)
                ))
                camera = cur.fetchone()
                conn.commit()
                return {
                    "id": camera['id'],
                    "name": camera['name'],
                    "description": camera['description'],
                    "url": camera['url'],
                    "video_url": camera.get('video_url', ''),
                    "latitude": float(camera['latitude']) if camera['latitude'] else 37.7749,
                    "longitude": float(camera['longitude']) if camera['longitude'] else -122.4194,
                    "active": camera.get('active', True),
                    "created_at": camera['created_at'].isoformat() if camera['created_at'] else None
                }
    except Exception as e:
        logger.error(f"Error creating camera: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create camera: {str(e)}")

@app.put("/api/cameras/{camera_id}")
async def update_camera(camera_id: str, camera_data: dict):
    """Update a camera"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE webcams 
                    SET name = %s, description = %s, url = %s, video_url = %s, latitude = %s, longitude = %s, active = %s
                    WHERE id = %s
                    RETURNING id, name, description, url, video_url, latitude, longitude, active, created_at
                """, (
                    camera_data['name'], 
                    camera_data['description'], 
                    camera_data['url'], 
                    camera_data.get('video_url', ''),
                    camera_data.get('latitude', 37.7749),
                    camera_data.get('longitude', -122.4194),
                    camera_data.get('active', True),
                    camera_id
                ))
                camera = cur.fetchone()
                if not camera:
                    raise HTTPException(status_code=404, detail="Camera not found")
                conn.commit()
                return {
                    "id": camera['id'],
                    "name": camera['name'],
                    "description": camera['description'],
                    "url": camera['url'],
                    "video_url": camera.get('video_url', ''),
                    "latitude": float(camera['latitude']) if camera['latitude'] else 37.7749,
                    "longitude": float(camera['longitude']) if camera['longitude'] else -122.4194,
                    "active": camera.get('active', True),
                    "created_at": camera['created_at'].isoformat() if camera['created_at'] else None
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update camera: {str(e)}")

@app.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """Delete a camera"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("DELETE FROM webcams WHERE id = %s RETURNING id", (camera_id,))
                deleted_camera = cur.fetchone()
                if not deleted_camera:
                    raise HTTPException(status_code=404, detail="Camera not found")
                conn.commit()
                return {"message": "Camera deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting camera: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete camera")

@app.patch("/api/cameras/{camera_id}/toggle-active")
async def toggle_camera_active(camera_id: str):
    """Toggle camera active status"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get current active status
                cur.execute("SELECT active FROM webcams WHERE id = %s", (camera_id,))
                camera = cur.fetchone()
                if not camera:
                    raise HTTPException(status_code=404, detail="Camera not found")
                
                # Toggle the active status
                new_active = not camera['active']
                cur.execute("""
                    UPDATE webcams 
                    SET active = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, name, active
                """, (new_active, camera_id))
                
                updated_camera = cur.fetchone()
                conn.commit()
                
                return {
                    "id": updated_camera['id'],
                    "name": updated_camera['name'],
                    "active": updated_camera['active'],
                    "message": f"Camera {'activated' if new_active else 'deactivated'} successfully"
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling camera active status: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle camera active status")

@app.get("/api/images", response_model=List[ImageForReview])
async def get_images_for_review(
    limit: Optional[int] = Query(50, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    confidence_filter: Optional[str] = Query(None, description="Filter by confidence: low, medium, high"),
    cameras: Optional[str] = Query(None, description="Comma-separated list of camera names"),
    time_range: Optional[str] = Query(None, description="Time range: 1h, 24h, 3d, 7d, 30d, all"),
    fog_levels: Optional[str] = Query(None, description="Comma-separated list of fog levels")
):
    """Get images for review with filtering and pagination"""
    return review_backend.get_pending_images(
        limit=limit, 
        offset=offset,
        confidence_filter=confidence_filter,
        cameras=cameras,
        time_range=time_range,
        fog_levels=fog_levels
    )


@app.get("/api/images/{filename}")
async def serve_image(filename: str):
    """Redirect to direct Cloud Storage image URL"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"raw_images/{filename}")
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Return direct public GCS URL instead of proxying
        direct_url = f"https://storage.googleapis.com/{BUCKET_NAME}/raw_images/{filename}"
        
        # Redirect to direct GCS URL to eliminate bandwidth doubling
        return RedirectResponse(
            url=direct_url,
            status_code=302,
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
        
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image")

@app.post("/api/review/{image_id}")
async def submit_review(image_id: str, decision: ReviewDecision):
    """Submit review decision for an image"""
    success = review_backend.process_review_decision(image_id, decision)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process review")
    
    return {
        "message": f"Review {decision.action.value} processed successfully",
        "image_id": image_id,
        "action": decision.action.value
    }

@app.post("/api/review/bulk")
async def submit_bulk_review(request: BulkReviewRequest):
    """Submit bulk review decisions"""
    results = []
    
    for image_id in request.image_ids:
        decision = ReviewDecision(
            action=request.action,
            reviewer_notes=request.reviewer_notes
        )
        
        success = review_backend.process_review_decision(image_id, decision)
        results.append({
            "image_id": image_id,
            "success": success,
            "action": request.action.value
        })
    
    successful = sum(1 for r in results if r["success"])
    
    return {
        "message": f"Processed {successful}/{len(request.image_ids)} reviews",
        "results": results
    }

@app.get("/api/stats", response_model=ReviewStats)
async def get_review_statistics():
    """Get review statistics"""
    return review_backend.get_review_stats()

@app.post("/api/export")
async def export_training_data():
    """Trigger export of training data"""
    # This could trigger a training pipeline or export process
    return {"message": "Training data export triggered"}


# ============= LABELER MANAGEMENT ENDPOINTS =============

class LabelerConfig(BaseModel):
    """Labeler configuration model"""
    name: str
    mode: str = Field(..., regex="^(production|shadow|experimental|deprecated)$")
    enabled: bool = True
    version: str = "1.0"
    config: Dict = {}

class LabelerUpdate(BaseModel):
    """Model for updating labeler configuration"""
    mode: Optional[str] = Field(None, regex="^(production|shadow|experimental|deprecated)$")
    enabled: Optional[bool] = None
    version: Optional[str] = None
    config: Optional[Dict] = None

class LabelerPerformance(BaseModel):
    """Labeler performance metrics model"""
    labeler_name: str
    labeler_mode: str
    total_executions: int
    avg_execution_time_ms: Optional[float]
    avg_confidence: Optional[float]
    avg_fog_score: Optional[float]
    total_cost_cents: Optional[float]
    executions_last_24h: int

class LabelerComparison(BaseModel):
    """Model for labeler comparison data"""
    image_id: int
    webcam_id: str
    image_timestamp: datetime
    primary_labeler: Optional[str]
    primary_fog_score: Optional[float]
    primary_fog_level: Optional[str]
    fog_score_disagreement: Optional[float]
    total_labelers_run: int

@app.get("/api/labelers", response_model=List[LabelerConfig])
async def get_all_labelers():
    """Get all labeler configurations"""
    try:
        query = """
            SELECT name, mode, enabled, version, config
            FROM labeler_config
            ORDER BY name
        """
        rows = execute_query(query)
        
        labelers = []
        for row in rows:
            labelers.append(LabelerConfig(
                name=row[0],
                mode=row[1],
                enabled=row[2],
                version=row[3] or "1.0",
                config=row[4] or {}
            ))
        
        return labelers
        
    except Exception as e:
        logger.error(f"Failed to get labelers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve labelers")

@app.get("/api/labelers/{labeler_name}", response_model=LabelerConfig)
async def get_labeler(labeler_name: str):
    """Get specific labeler configuration"""
    try:
        query = """
            SELECT name, mode, enabled, version, config
            FROM labeler_config
            WHERE name = %s
        """
        rows = execute_query(query, (labeler_name,))
        
        if not rows:
            raise HTTPException(status_code=404, detail="Labeler not found")
        
        row = rows[0]
        return LabelerConfig(
            name=row[0],
            mode=row[1],
            enabled=row[2],
            version=row[3] or "1.0",
            config=row[4] or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get labeler {labeler_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve labeler")

@app.get("/api/labelers/by-mode/{mode}")
async def get_labelers_by_mode(mode: str):
    """Get labelers filtered by mode"""
    if mode not in ["production", "shadow", "experimental", "deprecated"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    try:
        query = """
            SELECT name, mode, enabled, version, config
            FROM labeler_config
            WHERE mode = %s AND enabled = true
            ORDER BY name
        """
        rows = execute_query(query, (mode,))
        
        labelers = []
        for row in rows:
            labelers.append(LabelerConfig(
                name=row[0],
                mode=row[1],
                enabled=row[2],
                version=row[3] or "1.0",
                config=row[4] or {}
            ))
        
        return labelers
        
    except Exception as e:
        logger.error(f"Failed to get labelers by mode {mode}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve labelers")

@app.put("/api/labelers/{labeler_name}")
async def update_labeler(labeler_name: str, update: LabelerUpdate):
    """Update labeler configuration"""
    try:
        # Check if labeler exists
        check_query = "SELECT name FROM labeler_config WHERE name = %s"
        existing = execute_query(check_query, (labeler_name,))
        
        if not existing:
            raise HTTPException(status_code=404, detail="Labeler not found")
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if update.mode is not None:
            update_fields.append("mode = %s")
            update_values.append(update.mode)
        
        if update.enabled is not None:
            update_fields.append("enabled = %s")
            update_values.append(update.enabled)
        
        if update.version is not None:
            update_fields.append("version = %s")
            update_values.append(update.version)
        
        if update.config is not None:
            update_fields.append("config = %s")
            update_values.append(update.config)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = NOW()")
        update_values.append(labeler_name)
        
        query = f"""
            UPDATE labeler_config 
            SET {', '.join(update_fields)}
            WHERE name = %s
        """
        
        execute_query(query, update_values)
        
        logger.info(f"Updated labeler {labeler_name}: {update.dict(exclude_none=True)}")
        return {"message": f"Labeler {labeler_name} updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update labeler {labeler_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update labeler")

@app.post("/api/labelers")
async def create_labeler(labeler: LabelerConfig):
    """Create new labeler configuration"""
    try:
        # Check if labeler already exists
        check_query = "SELECT name FROM labeler_config WHERE name = %s"
        existing = execute_query(check_query, (labeler.name,))
        
        if existing:
            raise HTTPException(status_code=400, detail="Labeler already exists")
        
        query = """
            INSERT INTO labeler_config (name, mode, enabled, version, config)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        execute_query(query, (
            labeler.name,
            labeler.mode,
            labeler.enabled,
            labeler.version,
            labeler.config
        ))
        
        logger.info(f"Created new labeler: {labeler.name}")
        return {"message": f"Labeler {labeler.name} created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create labeler {labeler.name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create labeler")

@app.delete("/api/labelers/{labeler_name}")
async def delete_labeler(labeler_name: str):
    """Delete labeler configuration"""
    try:
        # Check if labeler exists
        check_query = "SELECT name FROM labeler_config WHERE name = %s"
        existing = execute_query(check_query, (labeler_name,))
        
        if not existing:
            raise HTTPException(status_code=404, detail="Labeler not found")
        
        query = "DELETE FROM labeler_config WHERE name = %s"
        execute_query(query, (labeler_name,))
        
        logger.info(f"Deleted labeler: {labeler_name}")
        return {"message": f"Labeler {labeler_name} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete labeler {labeler_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete labeler")

@app.post("/api/labelers/{labeler_name}/enable")
async def enable_labeler(labeler_name: str):
    """Enable a labeler"""
    try:
        query = "UPDATE labeler_config SET enabled = true, updated_at = NOW() WHERE name = %s"
        result = execute_query(query, (labeler_name,))
        
        # Check if any rows were affected
        check_query = "SELECT name FROM labeler_config WHERE name = %s"
        existing = execute_query(check_query, (labeler_name,))
        
        if not existing:
            raise HTTPException(status_code=404, detail="Labeler not found")
        
        logger.info(f"Enabled labeler: {labeler_name}")
        return {"message": f"Labeler {labeler_name} enabled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable labeler {labeler_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable labeler")

@app.post("/api/labelers/{labeler_name}/disable")
async def disable_labeler(labeler_name: str):
    """Disable a labeler"""
    try:
        query = "UPDATE labeler_config SET enabled = false, updated_at = NOW() WHERE name = %s"
        execute_query(query, (labeler_name,))
        
        # Check if any rows were affected
        check_query = "SELECT name FROM labeler_config WHERE name = %s"
        existing = execute_query(check_query, (labeler_name,))
        
        if not existing:
            raise HTTPException(status_code=404, detail="Labeler not found")
        
        logger.info(f"Disabled labeler: {labeler_name}")
        return {"message": f"Labeler {labeler_name} disabled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable labeler {labeler_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable labeler")

@app.post("/api/labelers/{labeler_name}/set-mode")
async def set_labeler_mode(labeler_name: str, mode_data: Dict[str, str]):
    """Change labeler mode"""
    mode = mode_data.get("mode")
    if not mode or mode not in ["production", "shadow", "experimental", "deprecated"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    try:
        query = "UPDATE labeler_config SET mode = %s, updated_at = NOW() WHERE name = %s"
        execute_query(query, (mode, labeler_name))
        
        # Check if any rows were affected
        check_query = "SELECT name FROM labeler_config WHERE name = %s"
        existing = execute_query(check_query, (labeler_name,))
        
        if not existing:
            raise HTTPException(status_code=404, detail="Labeler not found")
        
        logger.info(f"Set labeler {labeler_name} mode to {mode}")
        return {"message": f"Labeler {labeler_name} mode set to {mode}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set mode for labeler {labeler_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to set labeler mode")

# ============= PERFORMANCE MONITORING ENDPOINTS =============

@app.get("/api/labelers/performance/summary", response_model=List[LabelerPerformance])
async def get_labeler_performance():
    """Get performance metrics for all labelers"""
    try:
        query = """
            SELECT 
                labeler_name,
                labeler_mode,
                total_executions,
                avg_execution_time_ms,
                avg_confidence,
                avg_fog_score,
                total_cost_cents,
                executions_last_24h
            FROM labeler_performance_summary
            ORDER BY labeler_name
        """
        rows = execute_query(query)
        
        performance_data = []
        for row in rows:
            performance_data.append(LabelerPerformance(
                labeler_name=row[0],
                labeler_mode=row[1],
                total_executions=row[2] or 0,
                avg_execution_time_ms=row[3],
                avg_confidence=row[4],
                avg_fog_score=row[5],
                total_cost_cents=row[6],
                executions_last_24h=row[7] or 0
            ))
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Failed to get labeler performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance data")

@app.get("/api/labelers/{labeler_name}/performance")
async def get_labeler_specific_performance(labeler_name: str):
    """Get performance metrics for specific labeler"""
    try:
        query = """
            SELECT 
                labeler_name,
                labeler_mode,
                total_executions,
                avg_execution_time_ms,
                median_execution_time_ms,
                min_execution_time_ms,
                max_execution_time_ms,
                avg_confidence,
                avg_fog_score,
                total_cost_cents,
                avg_cost_cents,
                clear_count,
                light_fog_count,
                moderate_fog_count,
                heavy_fog_count,
                very_heavy_fog_count,
                first_execution,
                last_execution,
                executions_last_24h
            FROM labeler_performance_summary
            WHERE labeler_name = %s
        """
        rows = execute_query(query, (labeler_name,))
        
        if not rows:
            raise HTTPException(status_code=404, detail="Labeler performance data not found")
        
        row = rows[0]
        return {
            "labeler_name": row[0],
            "labeler_mode": row[1],
            "execution_metrics": {
                "total_executions": row[2] or 0,
                "avg_execution_time_ms": row[3],
                "median_execution_time_ms": row[4],
                "min_execution_time_ms": row[5],
                "max_execution_time_ms": row[6],
                "executions_last_24h": row[18] or 0
            },
            "quality_metrics": {
                "avg_confidence": row[7],
                "avg_fog_score": row[8]
            },
            "cost_metrics": {
                "total_cost_cents": row[9],
                "avg_cost_cents": row[10]
            },
            "fog_distribution": {
                "clear": row[11] or 0,
                "light_fog": row[12] or 0,
                "moderate_fog": row[13] or 0,
                "heavy_fog": row[14] or 0,
                "very_heavy_fog": row[15] or 0
            },
            "time_range": {
                "first_execution": row[16],
                "last_execution": row[17]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance for labeler {labeler_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve labeler performance")

@app.get("/api/labelers/performance/comparison", response_model=List[LabelerComparison])
async def get_labeler_comparison(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """Get labeler comparison data for agreement analysis"""
    try:
        query = """
            SELECT 
                image_id,
                webcam_id,
                image_timestamp,
                primary_labeler,
                primary_fog_score,
                primary_fog_level,
                fog_score_disagreement,
                total_labelers_run
            FROM labeler_agreement_analysis
            WHERE image_timestamp >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY fog_score_disagreement DESC NULLS LAST
            LIMIT %s
        """
        rows = execute_query(query, (days, limit))
        
        comparison_data = []
        for row in rows:
            comparison_data.append(LabelerComparison(
                image_id=row[0],
                webcam_id=row[1],
                image_timestamp=row[2],
                primary_labeler=row[3],
                primary_fog_score=row[4],
                primary_fog_level=row[5],
                fog_score_disagreement=row[6],
                total_labelers_run=row[7] or 0
            ))
        
        return comparison_data
        
    except Exception as e:
        logger.error(f"Failed to get labeler comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comparison data")

@app.get("/api/labelers/performance/daily")
async def get_daily_performance(
    days: int = Query(30, ge=1, le=90, description="Number of days to retrieve"),
    labeler_name: Optional[str] = Query(None, description="Filter by specific labeler")
):
    """Get daily performance trends"""
    try:
        if labeler_name:
            query = """
                SELECT 
                    execution_date,
                    labeler_name,
                    labeler_mode,
                    daily_executions,
                    avg_execution_time_ms,
                    avg_cost_cents,
                    avg_confidence,
                    total_daily_cost_cents
                FROM labeler_daily_performance
                WHERE labeler_name = %s
                AND execution_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY execution_date DESC
            """
            rows = execute_query(query, (labeler_name, days))
        else:
            query = """
                SELECT 
                    execution_date,
                    labeler_name,
                    labeler_mode,
                    daily_executions,
                    avg_execution_time_ms,
                    avg_cost_cents,
                    avg_confidence,
                    total_daily_cost_cents
                FROM labeler_daily_performance
                WHERE execution_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY execution_date DESC, labeler_name
            """
            rows = execute_query(query, (days,))
        
        daily_data = []
        for row in rows:
            daily_data.append({
                "date": row[0],
                "labeler_name": row[1],
                "labeler_mode": row[2],
                "daily_executions": row[3] or 0,
                "avg_execution_time_ms": row[4],
                "avg_cost_cents": row[5],
                "avg_confidence": row[6],
                "total_daily_cost_cents": row[7]
            })
        
        return daily_data
        
    except Exception as e:
        logger.error(f"Failed to get daily performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve daily performance")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )