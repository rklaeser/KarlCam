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

USE_CLOUD_STORAGE = os.getenv("USE_CLOUD_STORAGE", "true").lower() == "true"
BUCKET_NAME = os.getenv("OUTPUT_BUCKET", "karlcam-fog-data")
DATABASE_URL = os.getenv("DATABASE_URL")

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

def save_labels_to_cloud_storage(labels: Dict, filename: str) -> bool:
    """Save labels to Cloud Storage"""
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"labels/{filename}")
        
        blob.upload_from_string(
            json.dumps(labels, indent=2),
            content_type='application/json'
        )
        
        logger.info(f"✅ Saved labels to gs://{BUCKET_NAME}/labels/{filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save labels to Cloud Storage: {e}")
        return False

def get_unlabeled_images(db: Optional[DatabaseManager] = None, labeler_name: str = None) -> List[Dict]:
    """Get list of images that need labeling"""
    if db:
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
    else:
        # Get from local filesystem or cloud storage
        if USE_CLOUD_STORAGE:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(BUCKET_NAME)
                
                # List all raw images
                raw_blobs = list(bucket.list_blobs(prefix="raw_images/"))
                # List all labeled images
                labeled_blobs = list(bucket.list_blobs(prefix="labels/"))
                
                raw_files = {b.name.replace("raw_images/", "") for b in raw_blobs}
                labeled_files = {b.name.replace("labels/", "").replace(".json", "") for b in labeled_blobs}
                
                # Find unlabeled images
                unlabeled = raw_files - labeled_files
                
                return [{"image_filename": f} for f in unlabeled if f.endswith('.jpg')]
            except Exception as e:
                logger.error(f"Failed to get unlabeled images from Cloud Storage: {e}")
                return []
        else:
            # Local filesystem
            output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
            raw_dir = output_dir / "raw_images"
            labels_dir = output_dir / "labels"
            
            if not raw_dir.exists():
                return []
            
            raw_files = {f.name for f in raw_dir.glob("*.jpg")}
            labeled_files = {f.stem for f in labels_dir.glob("*.json")} if labels_dir.exists() else set()
            
            unlabeled = raw_files - {f + ".jpg" for f in labeled_files}
            
            return [{"image_filename": f} for f in unlabeled]

def label_images(labeler_types: List[str] = None):
    """Main labeling function"""
    if labeler_types is None:
        labeler_types = ["gemini"]  # Default to Gemini labeler
    
    logger.info(f"Starting image labeling with techniques: {labeler_types}")
    
    local_testing = os.getenv("LOCAL_TESTING", "false").lower() == "true"
    
    # Initialize database if not in local testing
    db = None if local_testing else DatabaseManager()
    
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
            
            # Load image and metadata
            if local_testing:
                output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
                image_path = output_dir / "raw_images" / image_filename
                image = Image.open(image_path).convert('RGB')
                
                metadata_path = output_dir / "raw_metadata" / f"{image_filename}.json"
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
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
            
            # Save labels
            label_data = {
                "image_filename": image_filename,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "metadata": metadata,
                "labels": labels
            }
            
            if local_testing:
                labels_dir = output_dir / "labels"
                labels_dir.mkdir(parents=True, exist_ok=True)
                labels_path = labels_dir / f"{image_filename}.json"
                with open(labels_path, 'w') as f:
                    json.dump(label_data, f, indent=2, default=str)
                logger.info(f"💾 Saved labels locally: {labels_path}")
            else:
                save_labels_to_cloud_storage(label_data, f"{image_filename}.json")
                
                # Save to database
                if db:
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