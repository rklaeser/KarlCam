#!/usr/bin/env python3
"""
Label collected images using configured labeling techniques
Runs after collect_images.py to apply labels to new images
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image
from io import BytesIO
from datetime import datetime, timezone
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to import db module
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.manager import DatabaseManager
from db.models import ImageLabel

from labelers import create_labeler

BUCKET_NAME = os.getenv("OUTPUT_BUCKET", "karlcam-fog-data")

def update_karlcam_mode(db: DatabaseManager):
    """Update KarlCam mode based on current time (Pacific Time)"""
    try:
        import pytz
        
        # Get current time in Pacific timezone
        pacific_tz = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(pacific_tz)
        current_hour = current_time.hour
        
        logger.info(f"Current Pacific time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Determine mode based on time
        # Night mode (sleeping): 7 PM (19:00) to 6 AM (06:00)
        # Business mode: 6 AM (06:00) to 7 PM (19:00)
        if 19 <= current_hour or current_hour < 6:
            new_mode = 1  # Night mode (sleeping)
            mode_name = "night mode"
        else:
            new_mode = 0  # Business as usual
            mode_name = "business mode"
        
        # Check current mode to avoid unnecessary updates
        current_status = db.get_system_status("karlcam_mode")
        if current_status and current_status.get("status_value") == new_mode:
            logger.info(f"KarlCam already in {mode_name} (mode={new_mode})")
            return
        
        # Update mode
        success = db.update_system_status("karlcam_mode", new_mode, "labeler_scheduler")
        if success:
            logger.info(f"✅ Updated KarlCam to {mode_name} (mode={new_mode})")
        else:
            logger.error(f"❌ Failed to update KarlCam mode to {new_mode}")
            
    except Exception as e:
        logger.error(f"Error updating KarlCam mode: {e}")

def load_image_from_cloud_storage(filename: str) -> Image.Image:
    """Load image from Cloud Storage"""
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"raw_images/{filename}")
        
        image_bytes = blob.download_as_bytes()
        return Image.open(BytesIO(image_bytes)).convert('RGB')
    except Exception as e:
        logger.error(f"Failed to load image from Cloud Storage: {e}")
        raise

def load_metadata_from_cloud_storage(filename: str) -> Dict:
    """Load metadata from Cloud Storage"""
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"raw_metadata/{filename}")
        
        metadata_str = blob.download_as_text()
        return json.loads(metadata_str)
    except Exception as e:
        logger.error(f"Failed to load metadata from Cloud Storage: {e}")
        raise

def get_unlabeled_images(db: DatabaseManager, labeler_name: str = None) -> List[Dict]:
    """Get list of images that need labeling from database"""
    # Get from database - returns ImageCollection objects
    images = db.get_unlabeled_images(labeler_name=labeler_name, limit=100)
    return [
        {
            "id": img.id,
            "image_filename": img.image_filename,
            "webcam_id": img.webcam_id,
            "timestamp": img.timestamp,
            "cloud_storage_path": img.cloud_storage_path
        }
        for img in images
    ]

def label_images(labeler_types: List[str] = None):
    """Main labeling function"""
    if labeler_types is None:
        labeler_types = ["gemini"]  # Default to Gemini labeler
    
    logger.info(f"Starting image labeling with techniques: {labeler_types}")
    
    # Initialize database
    db = DatabaseManager()
    
    # Update KarlCam mode based on current time
    update_karlcam_mode(db)
    
    # Get unlabeled images
    unlabeled_images = get_unlabeled_images(db)
    
    if not unlabeled_images:
        logger.info("No unlabeled images found")
        return
    
    logger.info(f"Found {len(unlabeled_images)} unlabeled images")
    
    # Initialize labelers
    labelers = []
    for labeler_type in labeler_types:
        try:
            labeler = create_labeler(labeler_type)
            labelers.append(labeler)
            logger.info(f"✅ Initialized {labeler_type} labeler")
        except Exception as e:
            logger.error(f"Failed to initialize {labeler_type} labeler: {e}")
    
    if not labelers:
        logger.error("No labelers available")
        return
    
    # Process each unlabeled image
    for image_info in unlabeled_images:
        image_filename = image_info["image_filename"]
        
        try:
            logger.info(f"Processing {image_filename}")
            
            # Load image and metadata from cloud storage
            image = load_image_from_cloud_storage(image_filename)
            metadata = load_metadata_from_cloud_storage(f"{image_filename}.json")
            
            # Apply each labeler
            labels = {}
            for labeler in labelers:
                label_result = labeler.label_image(image, metadata)
                labels[labeler.get_label_key()] = label_result
                
                if label_result.get("status") == "success":
                    logger.info(f"  ✅ {labeler.name}: Score={label_result.get('fog_score')}, Level={label_result.get('fog_level')}")
                else:
                    logger.error(f"  ❌ {labeler.name}: {label_result.get('error')}")
            
            # Save labels to database
            image_id = image_info.get("id")
            if not image_id:
                # Try to get image ID from database by filename
                img = db.get_image_by_filename(image_filename)
                if img:
                    image_id = img.id
            
            if image_id:
                for labeler_key, label_result in labels.items():
                    if label_result.get("status") == "success":
                        label = ImageLabel(
                            image_id=image_id,
                            labeler_name=labeler_key,
                            labeler_version="1.0",
                            fog_score=label_result.get('fog_score'),
                            fog_level=label_result.get('fog_level'),
                            confidence=label_result.get('confidence'),
                            reasoning=label_result.get('reasoning'),
                            visibility_estimate=label_result.get('visibility_estimate'),
                            weather_conditions=label_result.get('weather_conditions', []),
                            label_data=label_result
                        )
                        db.save_image_label(label)
            
        except Exception as e:
            logger.error(f"Failed to process {image_filename}: {e}")
    
    logger.info(f"""
    ========================================
    Labeling Complete:
    - Images processed: {len(unlabeled_images)}
    - Labeling techniques: {', '.join(labeler_types)}
    ========================================
    """)

if __name__ == "__main__":
    import sys
    
    # Allow specifying labeler types from command line
    if len(sys.argv) > 1:
        labeler_types = sys.argv[1].split(',')
    else:
        labeler_types = ["gemini"]
    
    label_images(labeler_types)