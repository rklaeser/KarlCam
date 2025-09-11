"""
Configuration endpoints for KarlCam Fog API
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..core.config import settings
from ..schemas.common import (
    PublicConfigResponse,
    FullConfigResponse,
    DefaultLocationResponse
)

router = APIRouter(prefix="/config", tags=["configuration"])


@router.get("/public", response_model=PublicConfigResponse)
async def get_public_config():
    """Get public configuration settings (non-sensitive)"""
    return PublicConfigResponse(
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        fog_detection_threshold=settings.FOG_DETECTION_THRESHOLD,
        foggy_conditions_threshold=settings.FOGGY_CONDITIONS_THRESHOLD,
        default_location=DefaultLocationResponse(
            name=settings.DEFAULT_LOCATION_NAME,
            latitude=settings.DEFAULT_LATITUDE,
            longitude=settings.DEFAULT_LONGITUDE
        ),
        default_history_hours=settings.DEFAULT_HISTORY_HOURS,
        stats_period_hours=settings.STATS_PERIOD_HOURS,
        api_prefix=settings.API_PREFIX
    )


@router.get("/full", response_model=FullConfigResponse)
async def get_full_config():
    """Get full configuration (admin only - no authentication implemented yet)"""
    # NOTE: In a production system, this would require admin authentication
    # For now, we'll only expose in development environment
    if settings.is_production:
        raise HTTPException(
            status_code=403, 
            detail="Full configuration access not available in production"
        )
    
    return FullConfigResponse(
        # Application settings
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        
        # Server settings
        api_prefix=settings.API_PREFIX,
        
        # Fog detection settings
        fog_detection_threshold=settings.FOG_DETECTION_THRESHOLD,
        foggy_conditions_threshold=settings.FOGGY_CONDITIONS_THRESHOLD,
        
        # Location settings
        default_latitude=settings.DEFAULT_LATITUDE,
        default_longitude=settings.DEFAULT_LONGITUDE,
        default_location_name=settings.DEFAULT_LOCATION_NAME,
        
        # Time settings
        recent_images_days=settings.RECENT_IMAGES_DAYS,
        camera_history_days=settings.CAMERA_HISTORY_DAYS,
        default_history_hours=settings.DEFAULT_HISTORY_HOURS,
        stats_period_hours=settings.STATS_PERIOD_HOURS,
        
        # Database settings (without sensitive data)
        db_pool_min_conn=settings.DB_POOL_MIN_CONN,
        db_pool_max_conn=settings.DB_POOL_MAX_CONN,
        db_pool_timeout=settings.DB_POOL_TIMEOUT,
        
        # GCS settings
        bucket_name=settings.BUCKET_NAME,
        gcs_timeout=settings.GCS_TIMEOUT,
        
        # CORS settings
        cors_origins=settings.CORS_ORIGINS,
        cors_allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        cors_allowed_methods=settings.CORS_ALLOWED_METHODS,
        cors_allowed_headers=settings.CORS_ALLOWED_HEADERS
    )