"""
Camera endpoints for KarlCam Fog API

This module provides endpoints for accessing fog detection data from cameras
positioned around the San Francisco Bay Area.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from typing import Optional
from datetime import datetime

from ..services.camera_service import CameraService
from ..services.on_demand_service import OnDemandService
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

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/public", 
    tags=["Cameras"],
    responses={
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                        "timestamp": "2024-01-10T08:30:00Z",
                        "path": "/api/public/cameras"
                    }
                }
            }
        },
        503: {
            "description": "Service temporarily unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Database connection unavailable",
                        "error_code": "SERVICE_UNAVAILABLE", 
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        }
    }
)


@router.get(
    "/cameras",
    response_model=CamerasListResponse,
    summary="Get all cameras with current fog status",
    description="""
    Returns a list of all active cameras with their current fog detection status.
    
    This endpoint provides real-time fog assessments from strategically positioned
    cameras around the San Francisco Bay Area. Each camera includes:
    
    * **Geographic coordinates** for mapping and visualization
    * **Current fog score** (0-100) with AI-generated assessment
    * **Qualitative fog level** (Clear, Light Fog, Moderate Fog, Heavy Fog, Very Heavy Fog)
    * **Confidence score** indicating AI certainty in the assessment
    * **Weather detection** status and additional metadata
    * **Timestamp** of the most recent assessment
    
    ## Data Freshness
    
    Fog assessments are updated approximately every **10 minutes** during daylight hours.
    The system continuously monitors weather conditions and provides fresh data for
    real-time applications.
    
    ## Use Cases
    
    * Weather monitoring dashboards
    * Transportation planning systems
    * Photography and tourism applications
    * Academic research on fog patterns
    * Maritime and aviation weather services
    
    ## Performance
    
    This endpoint is **cached for 60 seconds** to improve response times while maintaining
    data freshness for high-traffic applications.
    """,
    response_description="List of cameras with current fog detection data and metadata",
    responses={
        200: {
            "description": "Successful response with camera data",
            "content": {
                "application/json": {
                    "example": {
                        "cameras": [
                            {
                                "id": "golden-gate-north",
                                "name": "Golden Gate Bridge - North View", 
                                "lat": 37.8199,
                                "lon": -122.4783,
                                "description": "Camera positioned on the north side of Golden Gate Bridge",
                                "fog_score": 75,
                                "fog_level": "Heavy Fog",
                                "confidence": 0.92,
                                "weather_detected": True,
                                "weather_confidence": 0.88,
                                "timestamp": "2024-01-10T08:30:00Z",
                                "active": True
                            },
                            {
                                "id": "alcatraz-view",
                                "name": "Alcatraz Island View",
                                "lat": 37.8270,
                                "lon": -122.4230,
                                "description": "View of Alcatraz Island and surrounding bay",
                                "fog_score": 15,
                                "fog_level": "Clear",
                                "confidence": 0.95,
                                "weather_detected": False,
                                "weather_confidence": 0.82,
                                "timestamp": "2024-01-10T08:28:00Z",
                                "active": True
                            }
                        ],
                        "timestamp": "2024-01-10T08:30:15Z",
                        "count": 2
                    }
                }
            }
        }
    }
)
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


@router.get(
    "/cameras/{camera_id}",
    response_model=CameraDetailResponse,
    summary="Get camera details with historical fog data",
    description="""
    Returns detailed information about a specific camera including current fog status
    and historical fog detection data over a specified time period.
    
    This endpoint combines the current fog assessment with historical trends to provide
    comprehensive fog pattern analysis for a single camera location.
    
    ## Historical Data
    
    * **Default period**: 24 hours of history
    * **Maximum period**: 168 hours (1 week)
    * **Data points**: Individual fog assessments over time
    * **Resolution**: Approximately one assessment every 10 minutes
    
    ## Use Cases
    
    * Trend analysis for specific locations
    * Historical fog pattern research  
    * Time-series data for weather applications
    * Location-specific fog forecasting
    * Detailed camera performance monitoring
    
    ## Performance Notes
    
    Large history requests may take longer to process. For applications requiring
    extensive historical data, consider making multiple smaller requests or using
    the paginated history endpoints.
    """,
    response_description="Camera details with current status and historical fog data",
    responses={
        404: {
            "description": "Camera not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Camera golden-gate-south not found",
                        "error_code": "CAMERA_NOT_FOUND",
                        "timestamp": "2024-01-10T08:30:00Z",
                        "path": "/api/public/cameras/golden-gate-south"
                    }
                }
            }
        },
        200: {
            "description": "Successful response with camera details and history",
            "content": {
                "application/json": {
                    "example": {
                        "camera": {
                            "id": "golden-gate-north",
                            "name": "Golden Gate Bridge - North View",
                            "lat": 37.8199,
                            "lon": -122.4783,
                            "fog_score": 75,
                            "fog_level": "Heavy Fog",
                            "confidence": 0.92,
                            "timestamp": "2024-01-10T08:30:00Z"
                        },
                        "history": [
                            {
                                "fog_score": 65,
                                "fog_level": "Moderate Fog",
                                "confidence": 0.89,
                                "timestamp": "2024-01-10T08:20:00Z",
                                "reasoning": "Moderate fog visible across the Golden Gate with some clear patches"
                            }
                        ],
                        "history_hours": 24,
                        "history_count": 144
                    }
                }
            }
        }
    }
)
async def get_camera_detail(
    camera_id: str = Path(
        ...,
        description="Unique camera identifier",
        example="golden-gate-north"
    ), 
    hours: Optional[int] = Query(
        None,
        ge=1,
        le=168,
        description="Hours of historical data to include (default: 24, max: 168)",
        example=24
    ),
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


@router.get(
    "/cameras/{camera_id}/latest",
    summary="Get latest camera data with on-demand refresh",
    description="""
    Returns the latest fog detection data for a specific camera.
    
    **On-Demand Processing**: If the cached data is older than 30 minutes,
    this endpoint will automatically fetch a fresh image from the webcam
    and analyze it using AI before returning the results.
    
    ## Behavior
    
    * **Fresh data (<30 min)**: Returns immediately from cache (~100ms)
    * **Stale data (>30 min)**: Fetches and analyzes new image (~3-5 seconds)
    * **Error handling**: Returns stale data if refresh fails
    
    ## Response includes
    
    * Current fog score and level
    * AI confidence in the assessment
    * Reasoning for the fog detection
    * Visibility estimate
    * Weather conditions observed
    * Image URL and timestamp
    
    This endpoint implements the cost-optimized on-demand architecture,
    only processing images when users actually need fresh data.
    """,
    responses={
        404: {
            "description": "Camera not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Camera not found"}
                }
            }
        }
    }
)
async def get_camera_latest(
    camera_id: str = Path(..., description="Unique camera identifier"),
    db_manager=Depends(get_db_manager)
):
    """Get latest camera data with automatic refresh if stale"""
    try:
        service = OnDemandService(db_manager)
        result = service.get_latest_with_refresh(camera_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest data for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")