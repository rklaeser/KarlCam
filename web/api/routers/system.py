"""
System and stats endpoints for KarlCam Fog API

This module provides endpoints for system-wide statistics, status monitoring,
and administrative operations.
"""
from fastapi import APIRouter, HTTPException, Body
from datetime import datetime

from ..services.stats_service import StatsService
from ..schemas.common import (
    StatsResponse,
    SystemStatusResponse,
    SystemStatusUpdateRequest,
    SystemStatusUpdateResponse
)

router = APIRouter(
    tags=["System"],
    responses={
        500: {
            "description": "Internal server error", 
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        }
    }
)


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get system-wide fog detection statistics",
    description="""
    Returns comprehensive statistics about fog detection performance across all
    cameras in the KarlCam network over the last 24 hours.
    
    This endpoint provides key performance indicators and aggregate metrics for
    monitoring system health and understanding fog patterns across the San Francisco
    Bay Area.
    
    ## Metrics Included
    
    * **Total Assessments**: Number of fog assessments performed in the period
    * **Active Cameras**: Count of cameras currently operational
    * **Average Fog Score**: Mean fog intensity across all assessments (0-100)
    * **Average Confidence**: Mean AI confidence in assessments (0.0-1.0)
    * **Foggy Conditions**: Number of assessments above the fog threshold
    * **Last Update**: Timestamp of the most recent assessment
    
    ## Statistical Period
    
    Statistics cover a **24-hour rolling window** from the current time, providing
    up-to-date insights into system performance and fog detection patterns.
    
    ## Use Cases
    
    * System health monitoring dashboards
    * Performance analytics and reporting  
    * Fog pattern analysis and research
    * Service level agreement monitoring
    * Operational metrics for system administrators
    
    ## Data Quality
    
    Statistics are calculated in real-time from the latest assessment data,
    ensuring accuracy and freshness for monitoring applications.
    """,
    response_description="System-wide fog detection statistics and performance metrics",
    responses={
        200: {
            "description": "Successful response with system statistics",
            "content": {
                "application/json": {
                    "example": {
                        "total_assessments": 1440,
                        "active_cameras": 12,
                        "avg_fog_score": 32.5,
                        "avg_confidence": 0.89,
                        "foggy_conditions": 425,
                        "last_update": "2024-01-10T08:30:00Z",
                        "period": "24 hours",
                        "error": None
                    }
                }
            }
        }
    }
)
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


@router.post(
    "/system/status",
    response_model=SystemStatusUpdateResponse,
    summary="Update system status mode",
    description="""
    Updates the KarlCam system status mode for special operations or maintenance.
    
    This endpoint allows authorized services (primarily the labeling system) to
    update the operational mode of the KarlCam system. Different modes can trigger
    special behaviors in image collection, processing, or display.
    
    ## System Modes
    
    * **Mode 0**: Normal operation - standard fog detection and processing
    * **Mode 1**: Special mode - enhanced processing or special event handling
    
    ## Access Control
    
    This endpoint is primarily intended for internal system use by the labeling
    service and administrative tools. It does not require authentication but should
    be used responsibly.
    
    ## Use Cases
    
    * Coordinating special events or processing modes
    * System maintenance and testing
    * Administrative control of system behavior
    * Integration with external monitoring systems
    
    ## Response
    
    Returns confirmation of the status update with timestamp and updated mode.
    """,
    response_description="Confirmation of system status update",
    responses={
        200: {
            "description": "System status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "karlcam_mode": 1,
                        "updated_by": "labeling-service",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        },
        500: {
            "description": "Failed to update system status",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to update system status",
                        "error_code": "UPDATE_FAILED",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        }
    }
)
async def set_system_status(
    request: SystemStatusUpdateRequest = Body(
        ...,
        example={
            "karlcam_mode": 1,
            "updated_by": "labeling-service"
        },
        examples={
            "activate_special_mode": {
                "summary": "Activate special processing mode",
                "description": "Enable special mode for enhanced processing",
                "value": {
                    "karlcam_mode": 1,
                    "updated_by": "admin-panel"
                }
            },
            "normal_operation": {
                "summary": "Return to normal operation",
                "description": "Disable special mode and return to standard processing",
                "value": {
                    "karlcam_mode": 0,
                    "updated_by": "admin-panel"
                }
            }
        }
    )
):
    """Set system status - for internal use by labeler"""
    try:
        service = StatsService()
        result = service.set_system_status(request.dict())
        return SystemStatusUpdateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update system status")