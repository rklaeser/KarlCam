"""
System and stats endpoints for KarlCam Fog API
"""
from fastapi import APIRouter, HTTPException

from ..services.stats_service import StatsService
from ..schemas.common import (
    StatsResponse,
    SystemStatusResponse,
    SystemStatusUpdateRequest,
    SystemStatusUpdateResponse
)

router = APIRouter(tags=["system"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get overall fog statistics"""
    service = StatsService()
    stats_data = service.get_overall_stats()
    return StatsResponse(**stats_data)


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system status including karlcam mode"""
    service = StatsService()
    status_data = service.get_system_status()
    return SystemStatusResponse(**status_data)


@router.post("/system/status", response_model=SystemStatusUpdateResponse)
async def set_system_status(request: SystemStatusUpdateRequest):
    """Set system status - for internal use by labeler"""
    try:
        service = StatsService()
        result = service.set_system_status(request.dict())
        return SystemStatusUpdateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update system status")