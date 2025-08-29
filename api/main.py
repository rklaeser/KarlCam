#!/usr/bin/env python3
"""
KarlCam Fog API
FastAPI server that reads historical camera data assessed by Gemini from Cloud SQL database
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import logging

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

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    except psycopg.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def get_latest_camera_data() -> List[Dict]:
    """Get latest camera data from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get the most recent collection for each webcam
                cur.execute("""
                    SELECT DISTINCT ON (ic.webcam_id)
                        ic.webcam_id,
                        w.name,
                        w.latitude as lat,
                        w.longitude as lon,
                        w.description,
                        ic.fog_score,
                        ic.fog_level,
                        ic.confidence,
                        ic.timestamp,
                        w.active
                    FROM image_collections ic
                    LEFT JOIN webcams w ON ic.webcam_id = w.id
                    WHERE ic.status = 'success'
                    ORDER BY ic.webcam_id, ic.timestamp DESC
                """)
                
                results = cur.fetchall()
                cameras = []
                
                for row in results:
                    # Map our data to frontend expectations
                    fog_score = row['fog_score'] or 0
                    confidence = row['confidence'] or 0
                    fog_detected = fog_score > 20  # Consider fog detected if score > 20
                    
                    # Handle null lat/lon values
                    lat = row['lat'] if row['lat'] is not None else 37.7749  # Default to SF
                    lon = row['lon'] if row['lon'] is not None else -122.4194  # Default to SF
                    
                    cameras.append({
                        "id": row['webcam_id'],
                        "name": row['name'] or f"Camera {row['webcam_id']}",
                        "lat": lat,
                        "lon": lon,
                        "description": row['description'] or "",
                        "fog_score": fog_score,
                        "fog_level": row['fog_level'] or "Unknown",
                        "confidence": confidence * 100,  # Convert 0-1 to 0-100 for frontend
                        "weather_detected": fog_detected,
                        "weather_confidence": confidence * 100,  # Same as confidence
                        "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                        "active": row['active'] if row['active'] is not None else True
                    })
                
                return cameras
                
    except Exception as e:
        logger.error(f"Error fetching camera data: {e}")
        return []

def get_webcam_list() -> List[Dict]:
    """Get all webcams from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, latitude as lat, longitude as lon, description, active
                    FROM webcams
                    ORDER BY name
                """)
                
                results = cur.fetchall()
                webcams = []
                
                for row in results:
                    webcams.append({
                        "id": row['id'],
                        "name": row['name'],
                        "lat": row['lat'],
                        "lon": row['lon'],
                        "description": row['description'] or "",
                        "active": row['active']
                    })
                
                return webcams
                
    except Exception as e:
        logger.error(f"Error fetching webcams: {e}")
        return []

def get_camera_history(camera_id: str, hours: int = 24) -> List[Dict]:
    """Get historical data for a specific camera"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        ic.fog_score,
                        ic.fog_level,
                        ic.confidence,
                        ic.timestamp,
                        ic.reasoning
                    FROM image_collections ic
                    WHERE ic.webcam_id = %s 
                        AND ic.status = 'success'
                        AND ic.timestamp >= NOW() - INTERVAL %s
                    ORDER BY ic.timestamp DESC
                """, (camera_id, f'{hours} hours'))
                
                results = cur.fetchall()
                history = []
                
                for row in results:
                    history.append({
                        "fog_score": row['fog_score'],
                        "fog_level": row['fog_level'],
                        "confidence": row['confidence'],
                        "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                        "reasoning": row['reasoning']
                    })
                
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