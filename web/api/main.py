#!/usr/bin/env python3
"""
KarlCam Fog API
FastAPI server that reads historical camera data assessed by Gemini from Cloud SQL database
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# Add parent directory to path to import db module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.manager import DatabaseManager
from db.connection import get_db_connection, execute_query
from psycopg2.extras import RealDictCursor
from google.cloud import storage
from fastapi.responses import StreamingResponse
import io

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="KarlCam Fog API", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
BUCKET_NAME = os.getenv("BUCKET_NAME", "karlcam-fog-data")

logger.info(f"DATABASE_URL loaded: {DATABASE_URL}")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Initialize Google Cloud Storage client
storage_client = storage.Client()


# Initialize DatabaseManager
db_manager = DatabaseManager()

def get_latest_camera_data() -> List[Dict]:
    """Get latest camera data from database"""
    try:
        db_manager = DatabaseManager()
        
        # Get recent images with labels (last 1 day to get latest)
        recent_images = db_manager.get_recent_images(days=1)
        
        # Group by webcam_id and get latest LABELED image per camera
        latest_per_camera = {}
        for img in recent_images:
            webcam_id = img['webcam_id']
            # Only consider images that have labels
            if img.get('labels') and len(img['labels']) > 0:
                # Keep the most recent labeled image per camera
                if (webcam_id not in latest_per_camera or 
                    img['timestamp'] > latest_per_camera[webcam_id]['timestamp']):
                    latest_per_camera[webcam_id] = img
        
        cameras = []
        webcams = db_manager.get_active_webcams()
        
        # Create camera data with latest conditions
        for webcam in webcams:
            latest_img = latest_per_camera.get(webcam.id)
            
            if latest_img and latest_img.get('labels'):
                # Use first label for fog data
                label = latest_img['labels'][0]
                fog_score = label.get('fog_score', 0) or 0
                confidence = label.get('confidence', 0) or 0
                fog_detected = fog_score > 20
                
                cameras.append({
                    "id": webcam.id,
                    "name": webcam.name,
                    "lat": webcam.latitude or 37.7749,
                    "lon": webcam.longitude or -122.4194,
                    "description": webcam.description or "",
                    "fog_score": fog_score,
                    "fog_level": label.get('fog_level', 'Unknown'),
                    "confidence": confidence * 100,  # Convert 0-1 to 0-100
                    "weather_detected": fog_detected,
                    "weather_confidence": confidence * 100,
                    "timestamp": latest_img['timestamp'].isoformat() if latest_img['timestamp'] else None,
                    "active": webcam.active
                })
        
        return cameras
                
    except Exception as e:
        logger.error(f"Error fetching camera data: {e}")
        return []

def get_webcam_list() -> List[Dict]:
    """Get all webcams from database"""
    try:
        db_manager = DatabaseManager()
        webcams = db_manager.get_active_webcams()
        
        return [
            {
                "id": webcam.id,
                "name": webcam.name,
                "lat": webcam.latitude,
                "lon": webcam.longitude,
                "url": webcam.url,
                "video_url": webcam.video_url or "",
                "description": webcam.description or "",
                "active": webcam.active
            }
            for webcam in webcams
        ]
                
    except Exception as e:
        logger.error(f"Error fetching webcams: {e}")
        return []

def get_camera_history(camera_id: str, hours: int = 24) -> List[Dict]:
    """Get historical data for a specific camera"""
    try:
        db_manager = DatabaseManager()
        days = max(1, hours / 24)  # Convert hours to days, minimum 1 day
        
        # Get recent images for this specific camera
        recent_images = db_manager.get_recent_images(webcam_id=camera_id, days=days)
        
        history = []
        for img in recent_images:
            if img.get('labels'):
                # Use first label for fog data
                label = img['labels'][0]
                
                history.append({
                    "fog_score": label.get('fog_score', 0),
                    "fog_level": label.get('fog_level', 'Unknown'),
                    "confidence": label.get('confidence', 0),
                    "timestamp": img['timestamp'].isoformat() if img['timestamp'] else None,
                    "reasoning": ""  # Not available in aggregated query
                })
        
        # Sort by timestamp descending
        history.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        return history
                
    except Exception as e:
        logger.error(f"Error fetching camera history: {e}")
        return []


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "KarlCam Fog API", "version": "2.0.0"}

@app.get("/health")
async def health():
    """Health check with database status"""
    try:
        # Test database connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        return {
            "status": "healthy", 
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database": "disconnected", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/public/cameras")
async def get_cameras():
    """Get latest fog assessment for all cameras"""
    camera_data = get_latest_camera_data()
    return {
        "cameras": camera_data,
        "timestamp": datetime.now().isoformat(),
        "count": len(camera_data)
    }

@app.get("/api/public/webcams")
async def get_webcams():
    """Get all webcam locations for the map"""
    webcam_data = get_webcam_list()
    return {
        "webcams": webcam_data,
        "timestamp": datetime.now().isoformat(),
        "count": len(webcam_data)
    }

@app.get("/api/public/cameras/{camera_id}/latest-image")
async def get_latest_image_url(camera_id: str):
    """Get the latest collected image URL for a camera"""
    try:
        db_manager = DatabaseManager()
        
        # Get recent images for this camera (limit 1 for latest)
        recent_images = db_manager.get_recent_images(webcam_id=camera_id, days=30)
        
        if not recent_images:
            raise HTTPException(status_code=404, detail=f"No collected images found for camera {camera_id}")
        
        # Get the most recent image (it's a dictionary, not a model object)
        latest_image = recent_images[0]
        
        # Convert GCS path to direct public URL
        gcs_path = latest_image['cloud_storage_path']
        if gcs_path.startswith('gs://'):
            # Convert gs://bucket/path to https://storage.googleapis.com/bucket/path
            direct_image_url = gcs_path.replace('gs://', 'https://storage.googleapis.com/')
        else:
            direct_image_url = gcs_path
        
        return {
            "camera_id": camera_id,
            "image_url": direct_image_url,
            "filename": latest_image['image_filename'],
            "timestamp": latest_image['timestamp'].isoformat(),
            "age_hours": (datetime.now().replace(tzinfo=latest_image['timestamp'].tzinfo) - latest_image['timestamp']).total_seconds() / 3600
        }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest image for {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest image")

@app.get("/api/images/{filename}")
async def serve_image(filename: str):
    """Serve image from Cloud Storage"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"raw_images/{filename}")
        
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
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
        
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image")

@app.get("/api/public/cameras/{camera_id}")
async def get_camera_detail(camera_id: str, hours: Optional[int] = 24):
    """Get detailed information and history for a specific camera"""
    # Get current camera data
    camera_data = get_latest_camera_data()
    current_camera = next((c for c in camera_data if c["id"] == camera_id), None)
    
    if not current_camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    # Get historical data
    history = get_camera_history(camera_id, hours)
    
    return {
        "camera": current_camera,
        "history": history,
        "history_hours": hours,
        "history_count": len(history)
    }

@app.get("/api/stats")
async def get_stats():
    """Get overall fog statistics"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_assessments,
                        COUNT(DISTINCT webcam_id) as active_cameras,
                        AVG(fog_score) as avg_fog_score,
                        AVG(confidence) as avg_confidence,
                        COUNT(CASE WHEN fog_score > 50 THEN 1 END) as foggy_conditions,
                        MAX(timestamp) as last_update
                    FROM image_collections 
                    WHERE status = 'success'
                        AND timestamp >= NOW() - INTERVAL '24 hours'
                """)
                
                stats = cur.fetchone()
                
                return {
                    "total_assessments": stats['total_assessments'],
                    "active_cameras": stats['active_cameras'], 
                    "avg_fog_score": round(stats['avg_fog_score'] or 0, 2),
                    "avg_confidence": round(stats['avg_confidence'] or 0, 2),
                    "foggy_conditions": stats['foggy_conditions'],
                    "last_update": stats['last_update'].isoformat() if stats['last_update'] else None,
                    "period": "24 hours"
                }
                
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {
            "error": "Failed to fetch statistics",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/system/status")
async def get_system_status():
    """Get system status including karlcam mode"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT status_key, status_value, description, updated_at, updated_by
                    FROM system_status 
                    WHERE status_key = 'karlcam_mode'
                """)
                
                status = cur.fetchone()
                if not status:
                    return {"karlcam_mode": 0, "description": "Default mode"}
                
                return {
                    "karlcam_mode": status['status_value'],
                    "description": status['description'],
                    "updated_at": status['updated_at'].isoformat() if status['updated_at'] else None,
                    "updated_by": status['updated_by']
                }
                
    except Exception as e:
        logger.error(f"Error fetching system status: {e}")
        return {"karlcam_mode": 0, "description": "Default mode (error)"}

@app.post("/api/system/status")
async def set_system_status(request: dict):
    """Set system status - for internal use by labeler"""
    try:
        karlcam_mode = request.get('karlcam_mode', 0)
        updated_by = request.get('updated_by', 'api')
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO system_status (status_key, status_value, updated_by, updated_at)
                    VALUES ('karlcam_mode', %s, %s, NOW())
                    ON CONFLICT (status_key) 
                    DO UPDATE SET 
                        status_value = EXCLUDED.status_value,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = NOW()
                """, (karlcam_mode, updated_by))
                
                conn.commit()
                
                return {
                    "success": True,
                    "karlcam_mode": karlcam_mode,
                    "updated_by": updated_by,
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"Error setting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update system status")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
    
# For deployment: uvicorn main:app --host 0.0.0.0 --port 8002