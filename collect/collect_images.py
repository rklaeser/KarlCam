#!/usr/bin/env python3
"""
Collect webcam images without labeling
Images are stored for later labeling with different techniques
"""

import os
import json
import requests
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from PIL import Image
from io import BytesIO
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to import db module
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.manager import DatabaseManager
from db.models import ImageCollection

USE_CLOUD_STORAGE = os.getenv("USE_CLOUD_STORAGE", "true").lower() == "true"
BUCKET_NAME = os.getenv("OUTPUT_BUCKET", "karlcam-fog-data")
DATABASE_URL = os.getenv("DATABASE_URL")

def save_image_to_cloud_storage(image: Image.Image, filename: str) -> bool:
    """Save image to Cloud Storage"""
    if not USE_CLOUD_STORAGE:
        return False
        
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"raw_images/{filename}")
        
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr.seek(0)
        
        blob.upload_from_file(img_byte_arr, content_type='image/jpeg')
        logger.info(f"✅ Saved image to gs://{BUCKET_NAME}/raw_images/{filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save image to Cloud Storage: {e}")
        return False

def save_metadata_to_cloud_storage(metadata: dict, filename: str) -> bool:
    """Save metadata to Cloud Storage"""
    if not USE_CLOUD_STORAGE:
        return False
        
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"raw_metadata/{filename}")
        
        blob.upload_from_string(
            json.dumps(metadata, indent=2),
            content_type='application/json'
        )
        
        logger.info(f"✅ Saved metadata to gs://{BUCKET_NAME}/raw_metadata/{filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save metadata to Cloud Storage: {e}")
        return False

def discover_ipcamlive_url(alias: str) -> Optional[str]:
    """
    Discover the current snapshot URL for an IPCamLive camera
    
    Args:
        alias: The camera alias (e.g., '5e863c6e0e66d' for Marina District)
    
    Returns:
        Current snapshot URL or None if discovery fails
    """
    try:
        player_url = f"https://g1.ipcamlive.com/player/player.php?alias={alias}"
        response = requests.get(player_url, timeout=10)
        response.raise_for_status()
        
        content = response.text
        
        # Extract address and streamid using regex
        address_match = re.search(r"var address = '([^']+)';", content)
        streamid_match = re.search(r"var streamid = '([^']+)';", content)
        
        if not address_match or not streamid_match:
            logger.error(f"Could not extract address/streamid from player page for alias {alias}")
            return None
            
        address = address_match.group(1)
        streamid = streamid_match.group(1)
        
        # Construct snapshot URL
        # Convert http to https for security
        if address.startswith('http://'):
            address = 'https://' + address[7:]
            
        snapshot_url = f"{address}streams/{streamid}/snapshot.jpg"
        
        logger.info(f"🔍 Discovered URL for alias {alias}: {snapshot_url}")
        return snapshot_url
        
    except Exception as e:
        logger.error(f"❌ Error discovering URL for alias {alias}: {e}")
        return None

def get_webcam_url(webcam: dict, db: Optional['DatabaseManager'] = None) -> str:
    """
    Get the current URL for a webcam, handling dynamic discovery for IPCamLive cameras
    
    Args:
        webcam: Webcam dict with camera_type and discovery_metadata
        db: Database manager for updating discovered URLs
        
    Returns:
        Current working URL for the webcam
    """
    if webcam.get('camera_type') != 'ipcamlive':
        return webcam['url']
    
    # Handle IPCamLive dynamic discovery
    discovery_metadata = webcam.get('discovery_metadata') or {}
    alias = discovery_metadata.get('alias')
    
    if not alias:
        logger.error(f"❌ IPCamLive camera {webcam['id']} missing alias in discovery_metadata")
        return webcam['url']  # Fallback to current URL
    
    # Check if cached URL is still valid and not expired
    last_discovery_time = discovery_metadata.get('last_discovery_time')
    cache_ttl = discovery_metadata.get('discovery_cache_ttl', 3600)  # 1 hour default
    last_discovered_url = discovery_metadata.get('last_discovered_url')
    
    now = datetime.now(timezone.utc)
    cache_valid = False
    
    if last_discovery_time and last_discovered_url:
        try:
            last_time = datetime.fromisoformat(last_discovery_time.replace('Z', '+00:00'))
            cache_age = (now - last_time).total_seconds()
            cache_valid = cache_age < cache_ttl
        except:
            cache_valid = False
    
    # If cache is valid, try the cached URL first
    if cache_valid and last_discovered_url:
        try:
            response = requests.head(last_discovered_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Using cached URL for {webcam['id']}: {last_discovered_url}")
                return last_discovered_url
        except:
            logger.info(f"🔄 Cached URL failed for {webcam['id']}, rediscovering...")
    
    # Discover new URL
    discovered_url = discover_ipcamlive_url(alias)
    
    if discovered_url:
        # Update discovery metadata
        new_metadata = {
            **discovery_metadata,
            'last_discovered_url': discovered_url,
            'last_discovery_time': now.isoformat().replace('+00:00', 'Z'),
            'discovery_cache_ttl': cache_ttl
        }
        
        # Update database if available
        if db:
            try:
                db.update_webcam_discovery(webcam['id'], discovered_url, new_metadata)
            except Exception as e:
                logger.error(f"❌ Failed to update discovery metadata for {webcam['id']}: {e}")
        
        return discovered_url
    
    # Fallback to current URL if discovery fails
    logger.warning(f"⚠️ Discovery failed for {webcam['id']}, using fallback URL: {webcam['url']}")
    return webcam['url']

def collect_images():
    """Main collection function - only collects images without labeling"""
    logger.info("Starting image collection (no labeling)...")
    
    local_testing = os.getenv("LOCAL_TESTING", "false").lower() == "true"
    
    if local_testing:
        logger.info(f"💾 Local testing mode - saving to: {os.getenv('OUTPUT_DIR', './output')}")
        logger.info("🗄️ Database disabled for testing")
        db = None
        webcams_file = Path("data/webcams.json")
        if webcams_file.exists():
            with open(webcams_file, 'r') as f:
                webcams_data = json.load(f)
                webcam_urls = [w for w in webcams_data.get("webcams", []) if w.get("active", True)]
            logger.info(f"📷 Loaded {len(webcam_urls)} webcams from {webcams_file}")
        else:
            logger.error(f"❌ Could not find {webcams_file} for local testing")
            raise RuntimeError("webcams.json not found")
    else:
        logger.info(f"💾 Using Cloud Storage: gs://{BUCKET_NAME}")
        logger.info(f"🗄️ Using Cloud SQL database")
        db = DatabaseManager()
        try:
            webcams = db.get_active_webcams()
            # Convert Webcam objects to dict format expected by rest of code
            webcam_urls = [
                {
                    'id': w.id,
                    'name': w.name,
                    'url': w.url,
                    'lat': w.latitude,
                    'lon': w.longitude,
                    'description': w.description,
                    'active': w.active,
                    'camera_type': w.camera_type,
                    'discovery_metadata': w.discovery_metadata
                }
                for w in webcams
            ]
        except Exception as e:
            logger.error(f"❌ Failed to load webcams from database: {e}")
            logger.info("💡 Trying to load from webcams.json as fallback...")
            
            webcams_file = Path("data/webcams.json")
            if webcams_file.exists():
                with open(webcams_file, 'r') as f:
                    webcams_data = json.load(f)
                    webcam_urls = [w for w in webcams_data.get("webcams", []) if w.get("active", True)]
                logger.info(f"🎥 Loaded {len(webcam_urls)} webcams from {webcams_file}")
            else:
                logger.error("❌ No webcams configured and database unavailable!")
                raise RuntimeError("Unable to load webcam data")
    
    if not webcam_urls:
        logger.error("❌ No active webcams found!")
        raise RuntimeError("No active webcams configured")
    
    logger.info(f"🎥 Active webcams: {', '.join([w['name'] for w in webcam_urls])}")
    
    collection_run_id = None
    if db:
        collection_run_id = db.create_collection_run(total_images=len(webcam_urls))
    
    collection_results = []
    
    for webcam in webcam_urls:
        try:
            # Get the current URL (handles dynamic discovery for IPCamLive cameras)
            current_url = get_webcam_url(webcam, db)
            
            response = requests.get(current_url, timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGB')
            
            timestamp = datetime.now(timezone.utc)
            image_filename = f"{webcam['id']}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            
            metadata = {
                "image_path": image_filename,
                "timestamp": timestamp.isoformat().replace('+00:00', 'Z'),
                "webcam": webcam,
                "collection_run_id": collection_run_id,
                "labels": {}  # Empty - will be filled by labeling processes
            }
            
            if local_testing:
                output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
                raw_dir = output_dir / "raw_images"
                raw_dir.mkdir(parents=True, exist_ok=True)
                image_path = raw_dir / image_filename
                image.save(image_path)
                
                metadata_dir = output_dir / "raw_metadata"
                metadata_dir.mkdir(parents=True, exist_ok=True)
                json_path = metadata_dir / f"{image_filename}.json"
                with open(json_path, 'w') as f:
                    json.dump(metadata, f, indent=2, default=str)
                
                logger.info(f"💾 Saved locally: {image_path}")
            else:
                save_image_to_cloud_storage(image, image_filename)
                save_metadata_to_cloud_storage(metadata, f"{image_filename}.json")
                
                if db:
                    # Save basic collection info to database
                    image_collection = ImageCollection(
                        collection_run_id=collection_run_id,
                        webcam_id=webcam['id'],
                        timestamp=timestamp,
                        image_filename=image_filename,
                        cloud_storage_path=f"gs://{BUCKET_NAME}/raw_images/{image_filename}"
                    )
                    db.save_image_collection(image_collection)
            
            collection_results.append(metadata)
            logger.info(f"✅ Collected image from {webcam['name']}")
            
        except Exception as e:
            logger.error(f"Failed to collect from {webcam['name']}: {e}")
    
    successful_results = len(collection_results)
    summary = {
        "collection_time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "total_images": successful_results,
        "webcams_processed": [w['name'] for w in webcam_urls],
        "collection_run_id": collection_run_id
    }
    
    if db:
        db.update_collection_run(collection_run_id, {
            'successful_images': successful_results,
            'failed_images': len(webcam_urls) - successful_results,
            **summary
        })
    
    logger.info(f"""
    ========================================
    Collection Complete:
    - Collection Run ID: {collection_run_id}
    - Images collected: {summary['total_images']}
    - Storage: {'Local' if local_testing else 'Cloud Storage'}
    - Ready for labeling
    ========================================
    """)
    
    return collection_run_id

if __name__ == "__main__":
    collect_images()