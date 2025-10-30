"""
On-demand image collection and labeling service
"""

import os
import logging
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from io import BytesIO
import sys
from pathlib import Path

# Add parent directory to path for db imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.manager import DatabaseManager
from db.models import ImageCollection, ImageLabel
from .gemini_service import get_gemini_service
from ..core.config import settings
from google.cloud import storage

logger = logging.getLogger(__name__)


class OnDemandService:
    """Service for on-demand image collection and fog labeling"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.gemini_service = get_gemini_service()
        self.cache_threshold_minutes = 30
        
        # Initialize Cloud Storage client if enabled
        self.storage_client = None
        self.bucket = None
        use_cloud_storage = os.getenv("USE_CLOUD_STORAGE", "true").lower() == "true"
        if use_cloud_storage:
            try:
                self.storage_client = storage.Client()
                self.bucket = self.storage_client.bucket(settings.BUCKET_NAME)
                logger.info(f"Initialized Cloud Storage with bucket: {settings.BUCKET_NAME}")
            except Exception as e:
                logger.warning(f"Cloud Storage initialization failed: {e}")
    
    def get_latest_with_refresh(self, webcam_id: str) -> Dict:
        """
        Get latest image and labels for a webcam, refreshing if data is stale
        
        Args:
            webcam_id: ID of the webcam
            
        Returns:
            Dictionary with latest image and label data
        """
        try:
            # Get webcam configuration
            webcam = self.db_manager.get_webcam(webcam_id)
            if not webcam:
                logger.error(f"Webcam {webcam_id} not found")
                return None
            
            # Check for recent data
            recent_images = self.db_manager.get_recent_images(
                webcam_id=webcam_id, 
                days=1
            )
            
            # Check if we have fresh enough data
            now = datetime.now()
            if recent_images:
                latest = recent_images[0]
                age_minutes = (now - latest['timestamp'].replace(tzinfo=None)).total_seconds() / 60
                
                if age_minutes < self.cache_threshold_minutes and latest.get('labels'):
                    logger.info(f"Returning cached data for {webcam_id} (age: {age_minutes:.1f} minutes)")
                    return self._format_response(latest, webcam)
            
            # Data is stale or missing - fetch fresh
            logger.info(f"Fetching fresh data for {webcam_id}")
            return self._fetch_and_label(webcam)
            
        except Exception as e:
            logger.error(f"Error in get_latest_with_refresh for {webcam_id}: {e}")
            # Return stale data if available
            if recent_images:
                logger.warning(f"Returning stale data for {webcam_id} due to error")
                return self._format_response(recent_images[0], webcam)
            raise
    
    def _fetch_and_label(self, webcam) -> Dict:
        """
        Fetch fresh image from webcam and label it
        
        Args:
            webcam: Webcam model object
            
        Returns:
            Dictionary with fresh image and label data
        """
        try:
            # Fetch image from webcam URL
            logger.info(f"Fetching image from {webcam.url}")
            response = requests.get(webcam.url, timeout=10)
            response.raise_for_status()
            image_data = response.content
            
            # Generate filename and storage path
            timestamp = datetime.now()
            filename = f"{webcam.id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            
            # Save to Cloud Storage if enabled
            cloud_storage_path = None
            if self.storage_client and self.bucket:
                try:
                    blob_path = f"raw_images/{filename}"
                    blob = self.bucket.blob(blob_path)
                    blob.upload_from_string(image_data, content_type='image/jpeg')
                    cloud_storage_path = f"gs://{settings.BUCKET_NAME}/{blob_path}"
                    logger.info(f"Saved image to Cloud Storage: {cloud_storage_path}")
                except Exception as e:
                    logger.warning(f"Failed to save to Cloud Storage: {e}")
                    # Continue even if cloud storage fails
                    cloud_storage_path = f"local://{filename}"
            else:
                cloud_storage_path = f"local://{filename}"
            
            # Save image metadata to database
            image_collection = ImageCollection(
                webcam_id=webcam.id,
                timestamp=timestamp,
                image_filename=filename,
                cloud_storage_path=cloud_storage_path
            )
            image_id = self.db_manager.save_image_collection(image_collection)
            
            # Analyze image with Gemini
            logger.info(f"Analyzing image with Gemini for {webcam.id}")
            analysis = self.gemini_service.analyze_image(image_data, webcam.name)
            
            # Save label to database
            if not analysis.get('error'):
                label = ImageLabel(
                    image_id=image_id,
                    labeler_name=analysis['labeler_name'],
                    labeler_version=analysis['labeler_version'],
                    fog_score=analysis.get('fog_score'),
                    fog_level=analysis.get('fog_level'),
                    confidence=analysis.get('confidence'),
                    reasoning=analysis.get('reasoning'),
                    visibility_estimate=analysis.get('visibility_estimate'),
                    weather_conditions=analysis.get('weather_conditions', []),
                    label_data=analysis
                )
                self.db_manager.save_image_label(label)
                logger.info(f"Saved label for image {image_id}")
            else:
                logger.error(f"Gemini analysis failed: {analysis.get('error')}")
            
            # Format and return response
            result = {
                'image_id': image_id,
                'webcam_id': webcam.id,
                'timestamp': timestamp,
                'image_filename': filename,
                'cloud_storage_path': cloud_storage_path,
                'labels': [analysis] if not analysis.get('error') else []
            }
            
            return self._format_response(result, webcam)
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch image from {webcam.url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in _fetch_and_label for {webcam.id}: {e}")
            raise
    
    def _format_response(self, image_data: Dict, webcam) -> Dict:
        """
        Format the response with image and label data
        
        Args:
            image_data: Dictionary with image and label information
            webcam: Webcam model object
            
        Returns:
            Formatted response dictionary
        """
        # Get first label if available
        label = image_data['labels'][0] if image_data.get('labels') else None
        
        # Convert GCS path to public URL
        gcs_path = image_data['cloud_storage_path']
        if gcs_path.startswith('gs://'):
            image_url = gcs_path.replace('gs://', 'https://storage.googleapis.com/')
        else:
            image_url = gcs_path
        
        response = {
            'camera_id': webcam.id,
            'camera_name': webcam.name,
            'latitude': webcam.latitude,
            'longitude': webcam.longitude,
            'description': webcam.description,
            'image_url': image_url,
            'timestamp': image_data['timestamp'].isoformat(),
            'age_minutes': (datetime.now() - image_data['timestamp'].replace(tzinfo=None)).total_seconds() / 60
        }
        
        if label:
            response.update({
                'fog_score': label.get('fog_score', 0),
                'fog_level': label.get('fog_level', 'Unknown'),
                'confidence': label.get('confidence', 0),
                'reasoning': label.get('reasoning', ''),
                'visibility_estimate': label.get('visibility_estimate', 'Unknown'),
                'weather_conditions': label.get('weather_conditions', [])
            })
        else:
            response.update({
                'fog_score': None,
                'fog_level': 'Unknown',
                'confidence': 0,
                'reasoning': 'No analysis available',
                'visibility_estimate': 'Unknown',
                'weather_conditions': []
            })
        
        return response