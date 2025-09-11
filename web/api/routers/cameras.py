"""
Camera endpoints for KarlCam Fog API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from ..services.camera_service import CameraService
from ..core.dependencies import get_db_manager

router = APIRouter(prefix="/public", tags=["cameras"])


@router.get("/cameras")
async def get_cameras(db_manager=Depends(get_db_manager)):
    """Get latest fog assessment for all cameras"""
    service = CameraService(db_manager)
    camera_data = service.get_latest_camera_data()
    return {
        "cameras": camera_data,
        "timestamp": datetime.now().isoformat(),
        "count": len(camera_data)
    }


@router.get("/webcams")
async def get_webcams(db_manager=Depends(get_db_manager)):
    """Get all webcam locations for the map"""
    service = CameraService(db_manager)
    webcam_data = service.get_webcam_list()
    return {
        "webcams": webcam_data,
        "timestamp": datetime.now().isoformat(),
        "count": len(webcam_data)
    }


@router.get("/cameras/{camera_id}/latest-image")
async def get_latest_image_url(camera_id: str, db_manager=Depends(get_db_manager)):
    """Get the latest collected image URL for a camera"""
    try:
        service = CameraService(db_manager)
        image_info = service.get_latest_image_info(camera_id)
        return image_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch latest image")


@router.get("/cameras/{camera_id}")
async def get_camera_detail(
    camera_id: str, 
    hours: Optional[int] = 24,
    db_manager=Depends(get_db_manager)
):
    """Get detailed information and history for a specific camera"""
    service = CameraService(db_manager)
    
    # Get current camera data
    camera_data = service.get_latest_camera_data()
    current_camera = next((c for c in camera_data if c["id"] == camera_id), None)
    
    if not current_camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    # Get historical data
    history = service.get_camera_history(camera_id, hours)
    
    return {
        "camera": current_camera,
        "history": history,
        "history_hours": hours,
        "history_count": len(history)
    }