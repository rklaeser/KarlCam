"""
Camera endpoints for KarlCam Fog API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from ..services.camera_service import CameraService
from ..core.dependencies import get_db_manager
from ..core.config import settings
from ..schemas.common import (
    CamerasListResponse,
    CameraResponse,
    WebcamsListResponse,
    WebcamResponse,
    ImageInfoResponse,
    CameraDetailResponse,
    HistoryItemResponse
)

router = APIRouter(prefix="/public", tags=["cameras"])


@router.get("/cameras", response_model=CamerasListResponse)
async def get_cameras(db_manager=Depends(get_db_manager)):
    """Get latest fog assessment for all cameras"""
    service = CameraService(db_manager)
    camera_data = service.get_latest_camera_data()
    
    cameras = [CameraResponse(**camera) for camera in camera_data]
    
    return CamerasListResponse(
        cameras=cameras,
        timestamp=datetime.now().isoformat(),
        count=len(cameras)
    )


@router.get("/webcams", response_model=WebcamsListResponse)
async def get_webcams(db_manager=Depends(get_db_manager)):
    """Get all webcam locations for the map"""
    service = CameraService(db_manager)
    webcam_data = service.get_webcam_list()
    
    webcams = [WebcamResponse(**webcam) for webcam in webcam_data]
    
    return WebcamsListResponse(
        webcams=webcams,
        timestamp=datetime.now().isoformat(),
        count=len(webcams)
    )


@router.get("/cameras/{camera_id}/latest-image", response_model=ImageInfoResponse)
async def get_latest_image_url(camera_id: str, db_manager=Depends(get_db_manager)):
    """Get the latest collected image URL for a camera"""
    try:
        service = CameraService(db_manager)
        image_info = service.get_latest_image_info(camera_id)
        return ImageInfoResponse(**image_info)
    except Exception as e:
        # Let global exception handlers handle custom exceptions
        raise


@router.get("/cameras/{camera_id}", response_model=CameraDetailResponse)
async def get_camera_detail(
    camera_id: str, 
    hours: Optional[int] = None,
    db_manager=Depends(get_db_manager)
):
    """Get detailed information and history for a specific camera"""
    service = CameraService(db_manager)
    
    # Get current camera data
    camera_data = service.get_latest_camera_data()
    current_camera = next((c for c in camera_data if c["id"] == camera_id), None)
    
    if not current_camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    # Get historical data (use default from settings if not provided)
    hours_to_use = hours if hours is not None else settings.DEFAULT_HISTORY_HOURS
    history_data = service.get_camera_history(camera_id, hours_to_use)
    
    camera = CameraResponse(**current_camera)
    history = [HistoryItemResponse(**item) for item in history_data]
    
    return CameraDetailResponse(
        camera=camera,
        history=history,
        history_hours=hours_to_use,
        history_count=len(history)
    )