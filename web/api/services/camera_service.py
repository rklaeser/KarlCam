"""
Camera service containing business logic for camera operations
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add parent directory to path for db imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.manager import DatabaseManager
from ..core.config import settings
from ..utils.exceptions import (
    CameraNotFoundException,
    NoImagesFoundError,
    DatabaseConnectionError,
    DataProcessingError
)

logger = logging.getLogger(__name__)


class CameraService:
    """Service class for camera-related operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_latest_camera_data(self) -> List[Dict]:
        """Get latest camera data from database"""
        try:
            # Get recent images with labels (configurable days to get latest)
            recent_images = self.db_manager.get_recent_images(days=settings.RECENT_IMAGES_DAYS)
            
            # Group by webcam_id and get latest LABELED image per camera
            latest_per_camera = {}
            for img in recent_images:
                webcam_id = img['webcam_id']
                # Only consider images that have labels
                if img.get('labels') and len(img['labels']) > 0:
                    # Keep the most recent labeled image per camera
                    if (webcam_id not in latest_per_camera or 
                        img['timestamp'] > latest_per_camera[webcam_id]['timestamp']):
                        latest_per_camera[webcam_id] = img
            
            cameras = []
            webcams = self.db_manager.get_active_webcams()
            
            # Create camera data with latest conditions
            for webcam in webcams:
                latest_img = latest_per_camera.get(webcam.id)
                
                if latest_img and latest_img.get('labels'):
                    # Use first label for fog data
                    label = latest_img['labels'][0]
                    fog_score = label.get('fog_score', 0) or 0
                    confidence = label.get('confidence', 0) or 0
                    fog_detected = fog_score > settings.FOG_DETECTION_THRESHOLD
                    
                    cameras.append({
                        "id": webcam.id,
                        "name": webcam.name,
                        "lat": webcam.latitude or settings.DEFAULT_LATITUDE,
                        "lon": webcam.longitude or settings.DEFAULT_LONGITUDE,
                        "description": webcam.description or "",
                        "fog_score": fog_score,
                        "fog_level": label.get('fog_level', 'Unknown'),
                        "confidence": confidence * 100,  # Convert 0-1 to 0-100
                        "weather_detected": fog_detected,
                        "weather_confidence": confidence * 100,
                        "timestamp": latest_img['timestamp'].isoformat() if latest_img['timestamp'] else None,
                        "active": webcam.active
                    })
            
            return cameras
                    
        except Exception as e:
            logger.error(f"Error fetching camera data: {e}")
            raise DataProcessingError("Failed to fetch camera data")
    
    def get_webcam_list(self) -> List[Dict]:
        """Get all webcams from database"""
        try:
            webcams = self.db_manager.get_active_webcams()
            
            return [
                {
                    "id": webcam.id,
                    "name": webcam.name,
                    "lat": webcam.latitude,
                    "lon": webcam.longitude,
                    "url": webcam.url,
                    "video_url": webcam.video_url or "",
                    "description": webcam.description or "",
                    "active": webcam.active
                }
                for webcam in webcams
            ]
                    
        except Exception as e:
            logger.error(f"Error fetching webcams: {e}")
            raise DataProcessingError("Failed to fetch webcam list")
    
    def get_camera_history(self, camera_id: str, hours: int = None) -> List[Dict]:
        """Get historical data for a specific camera"""
        try:
            if hours is None:
                hours = settings.DEFAULT_HISTORY_HOURS
            days = max(1, hours / 24)  # Convert hours to days, minimum 1 day
            
            # Get recent images for this specific camera
            recent_images = self.db_manager.get_recent_images(webcam_id=camera_id, days=days)
            
            history = []
            for img in recent_images:
                if img.get('labels'):
                    # Use first label for fog data
                    label = img['labels'][0]
                    
                    history.append({
                        "fog_score": label.get('fog_score', 0),
                        "fog_level": label.get('fog_level', 'Unknown'),
                        "confidence": label.get('confidence', 0),
                        "timestamp": img['timestamp'].isoformat() if img['timestamp'] else None,
                        "reasoning": ""  # Not available in aggregated query
                    })
            
            # Sort by timestamp descending
            history.sort(key=lambda x: x['timestamp'] or '', reverse=True)
            return history
                    
        except Exception as e:
            logger.error(f"Error fetching camera history: {e}")
            raise DataProcessingError(f"Failed to fetch camera history for {camera_id}")
    
    def get_latest_image_info(self, camera_id: str) -> Dict:
        """Get the latest collected image info for a camera"""
        try:
            # Get recent images for this camera (limit 1 for latest)
            recent_images = self.db_manager.get_recent_images(webcam_id=camera_id, days=settings.CAMERA_HISTORY_DAYS)
            
            if not recent_images:
                raise NoImagesFoundError(camera_id)
            
            # Get the most recent image (it's a dictionary, not a model object)
            latest_image = recent_images[0]
            
            # Convert GCS path to direct public URL
            gcs_path = latest_image['cloud_storage_path']
            if gcs_path.startswith('gs://'):
                # Convert gs://bucket/path to https://storage.googleapis.com/bucket/path
                direct_image_url = gcs_path.replace('gs://', 'https://storage.googleapis.com/')
            else:
                direct_image_url = gcs_path
            
            return {
                "camera_id": camera_id,
                "image_url": direct_image_url,
                "filename": latest_image['image_filename'],
                "timestamp": latest_image['timestamp'].isoformat(),
                "age_hours": (datetime.now().replace(tzinfo=latest_image['timestamp'].tzinfo) - latest_image['timestamp']).total_seconds() / 3600
            }
                    
        except NoImagesFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching latest image for {camera_id}: {e}")
            raise DataProcessingError(f"Failed to fetch latest image for {camera_id}")