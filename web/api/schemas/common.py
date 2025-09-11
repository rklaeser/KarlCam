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