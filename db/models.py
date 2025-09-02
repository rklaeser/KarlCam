"""
Data models for KarlCam database
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class FogLevel(str, Enum):
    """Fog level classifications"""
    CLEAR = "Clear"
    LIGHT = "Light Fog"
    MODERATE = "Moderate Fog"
    HEAVY = "Heavy Fog"
    VERY_HEAVY = "Very Heavy Fog"
    UNKNOWN = "Unknown"


@dataclass
class Webcam:
    """Webcam configuration"""
    id: str
    name: str
    url: str
    latitude: float
    longitude: float
    video_url: Optional[str] = None
    description: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'video_url': self.video_url,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'active': self.active
        }


@dataclass
class CollectionRun:
    """Collection run tracking"""
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    total_images: int = 0
    successful_images: int = 0
    failed_images: int = 0
    summary_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class ImageCollection:
    """Raw collected image (without labels)"""
    webcam_id: str
    timestamp: datetime
    image_filename: str
    cloud_storage_path: str
    collection_run_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return {
            'collection_run_id': self.collection_run_id,
            'webcam_id': self.webcam_id,
            'timestamp': self.timestamp,
            'image_filename': self.image_filename,
            'cloud_storage_path': self.cloud_storage_path
        }


@dataclass
class ImageLabel:
    """Label for an image from a specific labeler"""
    image_id: int
    labeler_name: str
    labeler_version: str = "1.0"
    
    # Core labeling results
    fog_score: Optional[float] = None
    fog_level: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    visibility_estimate: Optional[str] = None
    weather_conditions: Optional[List[str]] = field(default_factory=list)
    
    # Full label data for flexibility
    label_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return {
            'image_id': self.image_id,
            'labeler_name': self.labeler_name,
            'labeler_version': self.labeler_version,
            'fog_score': self.fog_score,
            'fog_level': self.fog_level,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'visibility_estimate': self.visibility_estimate,
            'weather_conditions': self.weather_conditions,
            'label_data': self.label_data
        }
    
    def validate(self) -> bool:
        """Validate label data"""
        if self.fog_score is not None:
            if not (0 <= self.fog_score <= 100):
                return False
        
        if self.confidence is not None:
            if not (0 <= self.confidence <= 1.0):
                return False
        
        if self.fog_level and self.fog_level not in [e.value for e in FogLevel]:
            return False
        
        return True


@dataclass
class ImageSummary:
    """Summary view of image with label counts"""
    image_id: int
    webcam_id: str
    timestamp: datetime
    image_filename: str
    cloud_storage_path: str
    label_count: int
    labelers: List[str]


@dataclass
class LabelComparison:
    """Comparison of labels from different labelers"""
    image_filename: str
    webcam_id: str
    timestamp: datetime
    labeler_name: str
    labeler_version: str
    fog_score: float
    fog_level: str
    confidence: float
    labeled_at: datetime