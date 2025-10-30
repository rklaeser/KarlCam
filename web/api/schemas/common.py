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
    """Individual camera response schema with current fog detection data"""
    id: str = Field(
        ...,
        description="Unique camera identifier",
        example="golden-gate-north"
    )
    name: str = Field(
        ...,
        description="Human-readable camera name",
        example="Golden Gate Bridge - North View"
    )
    lat: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Camera latitude coordinate in decimal degrees",
        example=37.8199
    )
    lon: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Camera longitude coordinate in decimal degrees", 
        example=-122.4783
    )
    description: str = Field(
        ...,
        description="Detailed camera location description",
        example="Camera positioned on the north side of Golden Gate Bridge with clear view of the bay"
    )
    fog_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="AI-generated fog intensity score (0=clear, 100=very heavy fog)",
        example=75
    )
    fog_level: str = Field(
        ...,
        description="Qualitative fog assessment level",
        example="Heavy Fog"
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="AI confidence in fog assessment (0.0 to 1.0)",
        example=0.92
    )
    weather_detected: bool = Field(
        ...,
        description="Whether any weather conditions were detected in the image",
        example=True
    )
    weather_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="AI confidence in weather detection (0.0 to 1.0)",
        example=0.88
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO timestamp of the fog assessment",
        example="2024-01-10T08:30:00Z"
    )
    active: bool = Field(
        ...,
        description="Whether this camera is currently active and collecting data",
        example=True
    )

    class Config:
        schema_extra = {
            "example": {
                "id": "golden-gate-north",
                "name": "Golden Gate Bridge - North View",
                "lat": 37.8199,
                "lon": -122.4783,
                "description": "Camera positioned on the north side of Golden Gate Bridge with clear view of the bay",
                "fog_score": 75,
                "fog_level": "Heavy Fog",
                "confidence": 0.92,
                "weather_detected": True,
                "weather_confidence": 0.88,
                "timestamp": "2024-01-10T08:30:00Z",
                "active": True
            }
        }


class CamerasListResponse(BaseModel):
    """Cameras list response schema with metadata"""
    cameras: List[CameraResponse] = Field(
        ...,
        description="List of cameras with current fog detection data"
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp when this response was generated",
        example="2024-01-10T08:30:15Z"
    )
    count: int = Field(
        ...,
        description="Total number of cameras in the response",
        example=12
    )


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
    """Individual history item response schema for fog detection timeline"""
    fog_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Historical fog intensity score (0=clear, 100=very heavy fog)",
        example=45
    )
    fog_level: str = Field(
        ...,
        description="Historical qualitative fog assessment",
        example="Moderate Fog"
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="AI confidence in historical fog assessment",
        example=0.87
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO timestamp of this historical assessment",
        example="2024-01-10T07:45:00Z"
    )
    reasoning: str = Field(
        ...,
        description="AI-generated explanation for the fog assessment decision",
        example="Moderate fog visible across the bay area with reduced visibility on the bridge structure. Some patches of clear areas visible in the distance."
    )


class CameraDetailResponse(BaseModel):
    """Camera detail response schema"""
    camera: CameraResponse
    history: List[HistoryItemResponse]
    history_hours: int
    history_count: int


class StatsResponse(BaseModel):
    """Statistics response schema for system-wide fog detection metrics"""
    total_assessments: int = Field(
        ...,
        description="Total number of fog assessments in the period",
        example=1440
    )
    active_cameras: int = Field(
        ...,
        description="Number of cameras currently active and collecting data",
        example=12
    )
    avg_fog_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Average fog score across all assessments in the period",
        example=32.5
    )
    avg_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Average AI confidence across all assessments",
        example=0.89
    )
    foggy_conditions: int = Field(
        ...,
        description="Number of assessments indicating foggy conditions (score > threshold)",
        example=425
    )
    last_update: Optional[str] = Field(
        None,
        description="ISO timestamp of the most recent fog assessment",
        example="2024-01-10T08:30:00Z"
    )
    period: str = Field(
        ...,
        description="Time period covered by these statistics",
        example="24 hours"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if statistics calculation failed"
    )


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
    """Standard error response schema for API error handling"""
    detail: str = Field(
        ...,
        description="Human-readable error message",
        example="Camera with id golden-gate-south not found"
    )
    error_code: str = Field(
        ...,
        description="Machine-readable error code for programmatic handling",
        example="CAMERA_NOT_FOUND"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="ISO timestamp when the error occurred"
    )
    path: Optional[str] = Field(
        None,
        description="API path that generated the error",
        example="/api/public/cameras/golden-gate-south"
    )

    class Config:
        schema_extra = {
            "example": {
                "detail": "Camera with id golden-gate-south not found",
                "error_code": "CAMERA_NOT_FOUND", 
                "timestamp": "2024-01-10T08:30:00Z",
                "path": "/api/public/cameras/golden-gate-south"
            }
        }


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