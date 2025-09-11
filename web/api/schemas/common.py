"""
Common response schemas for KarlCam Fog API
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    service: Optional[str] = None
    version: Optional[str] = None
    database: Optional[str] = None
    error: Optional[str] = None
    timestamp: str


class CameraResponse(BaseModel):
    """Individual camera response schema"""
    id: str
    name: str
    lat: float
    lon: float
    description: str
    fog_score: int
    fog_level: str
    confidence: float
    weather_detected: bool
    weather_confidence: float
    timestamp: Optional[str]
    active: bool


class CamerasListResponse(BaseModel):
    """Cameras list response schema"""
    cameras: List[CameraResponse]
    timestamp: str
    count: int


class WebcamResponse(BaseModel):
    """Individual webcam response schema"""
    id: str
    name: str
    lat: float
    lon: float
    url: str
    video_url: str
    description: str
    active: bool


class WebcamsListResponse(BaseModel):
    """Webcams list response schema"""
    webcams: List[WebcamResponse]
    timestamp: str
    count: int


class ImageInfoResponse(BaseModel):
    """Latest image info response schema"""
    camera_id: str
    image_url: str
    filename: str
    timestamp: str
    age_hours: float


class HistoryItemResponse(BaseModel):
    """Individual history item response schema"""
    fog_score: int
    fog_level: str
    confidence: float
    timestamp: Optional[str]
    reasoning: str


class CameraDetailResponse(BaseModel):
    """Camera detail response schema"""
    camera: CameraResponse
    history: List[HistoryItemResponse]
    history_hours: int
    history_count: int


class StatsResponse(BaseModel):
    """Statistics response schema"""
    total_assessments: int
    active_cameras: int
    avg_fog_score: float
    avg_confidence: float
    foggy_conditions: int
    last_update: Optional[str]
    period: str
    error: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """System status response schema"""
    karlcam_mode: int
    description: str
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class SystemStatusUpdateRequest(BaseModel):
    """System status update request schema"""
    karlcam_mode: int
    updated_by: Optional[str] = "api"


class SystemStatusUpdateResponse(BaseModel):
    """System status update response schema"""
    success: bool
    karlcam_mode: int
    updated_by: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    detail: str
    error_code: str
    timestamp: datetime = Field(default_factory=datetime.now)
    path: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response schema"""
    detail: str = "Validation error"
    error_code: str = "VALIDATION_ERROR"
    errors: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.now)


class DefaultLocationResponse(BaseModel):
    """Default location configuration schema"""
    name: str
    latitude: float
    longitude: float


class PublicConfigResponse(BaseModel):
    """Public configuration response schema"""
    app_name: str
    version: str
    environment: str
    fog_detection_threshold: int
    foggy_conditions_threshold: int
    default_location: DefaultLocationResponse
    default_history_hours: int
    stats_period_hours: int
    api_prefix: str


class FullConfigResponse(BaseModel):
    """Full configuration response schema (admin only)"""
    # Application settings
    app_name: str
    version: str
    environment: str
    debug: bool
    
    # Server settings
    api_prefix: str
    
    # Fog detection settings
    fog_detection_threshold: int
    foggy_conditions_threshold: int
    
    # Location settings
    default_latitude: float
    default_longitude: float
    default_location_name: str
    
    # Time settings
    recent_images_days: int
    camera_history_days: int
    default_history_hours: int
    stats_period_hours: int
    
    # Database settings (without sensitive data)
    db_pool_min_conn: int
    db_pool_max_conn: int
    db_pool_timeout: int
    
    # GCS settings
    bucket_name: str
    gcs_timeout: int
    
    # CORS settings
    cors_origins: List[str]
    cors_allow_credentials: bool
    cors_allowed_methods: List[str]
    cors_allowed_headers: List[str]