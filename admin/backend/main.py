"""
FastAPI Review Backend for KarlCam
Handles review workflow for Gemini-labeled images using Cloud Storage and SQL Database
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
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
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                        SELECT 
                            ic.id,
                            ic.image_filename,
                            ic.timestamp,
                            ic.webcam_id,
                            ic.fog_score,
                            ic.fog_level,
                            ic.confidence,
                            ic.reasoning,
                            ic.visibility_estimate,
                            ic.weather_conditions,
                            w.name as webcam_name,
                            w.description as webcam_description
                        FROM image_collections ic
                        LEFT JOIN webcams w ON ic.webcam_id = w.id
                        WHERE ic.status = 'success'
                    """
                    params = []
                    
                    # Add camera filtering
                    if cameras:
                        camera_list = cameras.split(',')
                        placeholders = ','.join(['%s'] * len(camera_list))
                        query += f" AND w.name IN ({placeholders})"
                        params.extend(camera_list)
                    
                    # Add time range filtering
                    if time_range and time_range != 'all':
                        if time_range == '1h':
                            query += " AND ic.timestamp >= NOW() - INTERVAL '1 hour'"
                        elif time_range == '24h':
                            query += " AND ic.timestamp >= NOW() - INTERVAL '1 day'"
                        elif time_range == '3d':
                            query += " AND ic.timestamp >= NOW() - INTERVAL '3 days'"
                        elif time_range == '7d':
                            query += " AND ic.timestamp >= NOW() - INTERVAL '7 days'"
                        elif time_range == '30d':
                            query += " AND ic.timestamp >= NOW() - INTERVAL '30 days'"
                    
                    # Add confidence filtering
                    if confidence_filter:
                        confidence_filters = confidence_filter.split(',')
                        confidence_conditions = []
                        for cf in confidence_filters:
                            if cf == 'low':
                                confidence_conditions.append("ic.confidence < 0.7")
                            elif cf == 'medium':  
                                confidence_conditions.append("(ic.confidence >= 0.7 AND ic.confidence < 0.9)")
                            elif cf == 'high':
                                confidence_conditions.append("ic.confidence >= 0.9")
                        if confidence_conditions:
                            query += f" AND ({' OR '.join(confidence_conditions)})"
                    
                    # Add fog level filtering
                    if fog_levels:
                        fog_level_list = fog_levels.split(',')
                        placeholders = ','.join(['%s'] * len(fog_level_list))
                        query += f" AND ic.fog_level IN ({placeholders})"
                        params.extend(fog_level_list)
                    
                    query += " ORDER BY ic.timestamp DESC"
                    
                    if limit:
                        query += " LIMIT %s"
                        params.append(limit)
                    
                    if offset:
                        query += " OFFSET %s"
                        params.append(offset)
                    
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    
                    # Convert to the expected format
                    images = []
                    for row in rows:
                        images.append(ImageForReview(
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
                            image_url=f"/api/images/cloud/{row['image_filename']}",
                            status="pending"
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
                            ic.fog_score,
                            ic.fog_level,
                            ic.confidence,
                            ic.reasoning,
                            ic.visibility_estimate,
                            ic.weather_conditions,
                            w.name as webcam_name,
                            w.description as webcam_description
                        FROM image_collections ic
                        LEFT JOIN webcams w ON ic.webcam_id = w.id
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
                        image_url=f"/api/images/cloud/{row['image_filename']}",
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
                    SELECT id, name, description, url, created_at
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
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO webcams (name, description, url)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, description, url, created_at
                """, (camera_data['name'], camera_data['description'], camera_data['url']))
                camera = cur.fetchone()
                conn.commit()
                return {
                    "id": camera['id'],
                    "name": camera['name'],
                    "description": camera['description'],
                    "url": camera['url'],
                    "created_at": camera['created_at'].isoformat() if camera['created_at'] else None
                }
    except Exception as e:
        logger.error(f"Error creating camera: {e}")
        raise HTTPException(status_code=500, detail="Failed to create camera")

@app.put("/api/cameras/{camera_id}")
async def update_camera(camera_id: int, camera_data: dict):
    """Update a camera"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE webcams 
                    SET name = %s, description = %s, url = %s
                    WHERE id = %s
                    RETURNING id, name, description, url, created_at
                """, (camera_data['name'], camera_data['description'], camera_data['url'], camera_id))
                camera = cur.fetchone()
                if not camera:
                    raise HTTPException(status_code=404, detail="Camera not found")
                conn.commit()
                return {
                    "id": camera['id'],
                    "name": camera['name'],
                    "description": camera['description'],
                    "url": camera['url'],
                    "created_at": camera['created_at'].isoformat() if camera['created_at'] else None
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera: {e}")
        raise HTTPException(status_code=500, detail="Failed to update camera")

@app.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id: int):
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

@app.get("/api/images/{image_id}", response_model=ImageForReview)
async def get_image(image_id: str):
    """Get specific image for review"""
    image = review_backend.get_image_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    return image

@app.get("/api/images/cloud/{filename}")
async def serve_cloud_image(filename: str):
    """Serve image from Cloud Storage"""
    from fastapi.responses import StreamingResponse
    import io
    
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"images/review/pending/{filename}")
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Download the image data
        image_data = blob.download_as_bytes()
        
        # Determine content type based on file extension
        content_type = "image/jpeg"  # Default
        if filename.lower().endswith('.png'):
            content_type = "image/png"
        elif filename.lower().endswith('.gif'):
            content_type = "image/gif"
        elif filename.lower().endswith('.webp'):
            content_type = "image/webp"
        
        # Return the image data as a streaming response
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except Exception as e:
        logger.error(f"Failed to serve image {filename}: {e}")
        raise HTTPException(status_code=404, detail="Image not found")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )