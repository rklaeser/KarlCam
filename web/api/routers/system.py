"""
System and stats endpoints for KarlCam Fog API
"""
from fastapi import APIRouter, HTTPException

from ..services.stats_service import StatsService

router = APIRouter(tags=["system"])


@router.get("/stats")
async def get_stats():
    """Get overall fog statistics"""
    service = StatsService()
    return service.get_overall_stats()


@router.get("/system/status")
async def get_system_status():
    """Get system status including karlcam mode"""
    service = StatsService()
    return service.get_system_status()


@router.post("/system/status")
async def set_system_status(request: dict):
    """Set system status - for internal use by labeler"""
    try:
        service = StatsService()
        return service.set_system_status(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update system status")