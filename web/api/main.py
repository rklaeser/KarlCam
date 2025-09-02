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
CACHE_DURATION = 300  # 5 minutes cache

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# In-memory cache
cache = {
    "latest_data": None,
    "webcams": None,
    "last_update": None
}

# Initialize DatabaseManager
db_manager = DatabaseManager()

def get_latest_camera_data() -> List[Dict]:
    """Get latest camera data from database"""
    try:
        db_manager = DatabaseManager()
        
        # Get recent images with labels (last 1 day to get latest)
        recent_images = db_manager.get_recent_images(days=1)
        
        # Group by webcam_id and get latest per camera
        latest_per_camera = {}
        for img in recent_images:
            webcam_id = img['webcam_id']
            # Keep the most recent image per camera
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

def should_refresh_cache() -> bool:
    """Check if cache needs refresh"""
    if not cache["last_update"]:
        return True
    return datetime.now() - cache["last_update"] > timedelta(seconds=CACHE_DURATION)

def refresh_cache():
    """Refresh cached data from database"""
    if not should_refresh_cache():
        return
    
    logger.info("Refreshing cache from database")
    
    # Get latest camera data
    camera_data = get_latest_camera_data()
    cache["latest_data"] = {
        "cameras": camera_data,
        "timestamp": datetime.now().isoformat(),
        "count": len(camera_data)
    }
    
    # Get webcam list
    webcam_data = get_webcam_list()
    cache["webcams"] = {
        "webcams": webcam_data
    }
    
    cache["last_update"] = datetime.now()

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
    refresh_cache()
    
    if cache["latest_data"]:
        return cache["latest_data"]
    else:
        # Fallback to fresh data
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
    
# For deployment: uvicorn main:app --host 0.0.0.0 --port 8002