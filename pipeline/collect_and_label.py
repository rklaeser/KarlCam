#!/usr/bin/env python3
"""
Unified pipeline that collects images and immediately labels them
Combines the functionality of collect_images.py and label_images.py for optimal performance
"""

import asyncio
import aiohttp
import os
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from PIL import Image
from io import BytesIO
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.manager import DatabaseManager
from db.models import ImageCollection, ImageLabel

logger = logging.getLogger(__name__)

class KarlCamPipeline:
    def __init__(self):
        self.db = DatabaseManager()
        self.use_cloud_storage = os.getenv("USE_CLOUD_STORAGE", "true").lower() == "true"
        self.bucket_name = os.getenv("OUTPUT_BUCKET", "karlcam-fog-data")
        self.local_testing = os.getenv("LOCAL_TESTING", "false").lower() == "true"
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent operations
        
        # Import labelers dynamically
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from labelers import create_labeler
            from labelers.registry import get_registry
            self.create_labeler = create_labeler
            self.registry = get_registry()
            if self.registry:
                logger.info(f"✅ Labeler registry initialized with {len(self.registry.configs)} configurations")
            else:
                logger.warning("⚠️ Labeler registry not available, falling back to direct labeler creation")
        except ImportError as e:
            logger.error(f"Failed to import labelers: {e}")
            self.create_labeler = None
            self.registry = None
        
    async def run(self):
        """Main pipeline execution"""
        logger.info("Starting KarlCam unified pipeline (collect + label)...")
        
        # Update KarlCam mode based on time
        self._update_karlcam_mode()
        
        # Get active webcams
        webcams = self._get_webcams()
        if not webcams:
            logger.error("No active webcams found!")
            return
            
        logger.info(f"🎥 Processing {len(webcams)} webcams: {', '.join([w['name'] for w in webcams])}")
        
        # Create collection run
        collection_run_id = None
        if not self.local_testing:
            collection_run_id = self.db.create_collection_run(total_images=len(webcams))
            logger.info(f"📝 Created collection run: {collection_run_id}")
        
        # Process all webcams concurrently
        start_time = time.time()
        tasks = [self.process_webcam(webcam, collection_run_id) for webcam in webcams]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        # Update collection run summary
        if collection_run_id and not self.local_testing:
            self.db.update_collection_run(collection_run_id, {
                'successful_images': successful,
                'failed_images': failed,
                'labeling_enabled': True,
                'labeler_used': 'gemini',
                'processing_time_seconds': round(total_time, 2)
            })
        
        # Log summary
        logger.info(f"""
        ========================================
        Pipeline Complete:
        - Collection Run ID: {collection_run_id}
        - Webcams processed: {successful}/{len(webcams)}
        - Failed: {failed}
        - Total time: {total_time:.2f}s
        - Avg time per webcam: {total_time/len(webcams):.2f}s
        ========================================
        """)
        
        # Log any exceptions for debugging
        for i, exc in enumerate(exceptions):
            logger.error(f"Exception {i+1}: {exc}")
        
        return collection_run_id
        
    async def process_webcam(self, webcam: Dict, collection_run_id: int) -> bool:
        """Process a single webcam: collect and label in parallel"""
        async with self.semaphore:  # Limit concurrent operations
            webcam_name = webcam['name']
            try:
                logger.info(f"🔄 Processing {webcam_name}...")
                
                # 1. Collect image
                image, image_bytes = await self.collect_image_async(webcam)
                
                timestamp = datetime.now(timezone.utc)
                image_filename = f"{webcam['id']}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                
                # 2. Start async tasks for storage and labeling
                storage_task = asyncio.create_task(
                    self.save_to_storage_async(image_bytes, image_filename)
                )
                
                label_task = asyncio.create_task(
                    self.label_image_multi_async(image, webcam)
                )
                
                # 3. Save image collection to database first
                image_id = None
                if not self.local_testing:
                    image_collection = ImageCollection(
                        collection_run_id=collection_run_id,
                        webcam_id=webcam['id'],
                        timestamp=timestamp,
                        image_filename=image_filename,
                        cloud_storage_path=f"gs://{self.bucket_name}/raw_images/{image_filename}"
                    )
                    image_id = self.db.save_image_collection(image_collection)
                    logger.info(f"💾 Saved image metadata for {webcam_name} (ID: {image_id})")
                
                # 4. Wait for storage and labeling to complete
                storage_result, label_result = await asyncio.gather(
                    storage_task, label_task, return_exceptions=True
                )
                
                # Handle storage result
                if isinstance(storage_result, Exception):
                    logger.error(f"❌ Storage failed for {webcam_name}: {storage_result}")
                else:
                    logger.info(f"☁️ Storage complete for {webcam_name}")
                
                # 5. Save labels to database
                if not isinstance(label_result, Exception) and image_id and not self.local_testing:
                    self.save_labels_to_db(image_id, label_result, webcam_name)
                elif isinstance(label_result, Exception):
                    logger.error(f"❌ Labeling failed for {webcam_name}: {label_result}")
                else:
                    logger.error(f"❌ Labeling failed for {webcam_name}: {label_result.get('error', 'Unknown error')}")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to process {webcam_name}: {e}")
                return False
    
    async def collect_image_async(self, webcam: Dict):
        """Asynchronously collect image from webcam"""
        url = self._get_webcam_url(webcam)
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                image_bytes = await response.read()
                image = Image.open(BytesIO(image_bytes)).convert('RGB')
                return image, image_bytes
    
    async def save_to_storage_async(self, image_bytes: bytes, filename: str):
        """Asynchronously save to cloud storage"""
        if self.local_testing:
            # Local save logic
            output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
            raw_dir = output_dir / "raw_images"
            raw_dir.mkdir(parents=True, exist_ok=True)
            image_path = raw_dir / filename
            
            # Run file I/O in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._save_local_sync, image_bytes, image_path)
            return
        
        if not self.use_cloud_storage:
            return
            
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._save_to_gcs_sync,
                image_bytes,
                filename
            )
        except Exception as e:
            logger.error(f"Failed to save to GCS: {e}")
            raise
    
    def _save_local_sync(self, image_bytes: bytes, image_path: Path):
        """Synchronous local save for executor"""
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
    
    def _save_to_gcs_sync(self, image_bytes: bytes, filename: str):
        """Synchronous GCS save for executor"""
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(self.bucket_name)
        blob = bucket.blob(f"raw_images/{filename}")
        blob.upload_from_string(image_bytes, content_type='image/jpeg')
    
    async def label_image_async(self, image: Image, webcam: Dict):
        """Asynchronously label image"""
        if not self.create_labeler:
            return {"status": "error", "error": "Labelers not available"}
        
        try:
            # Create labeler instance
            labeler = self.create_labeler("gemini")
            
            # Prepare metadata
            metadata = {
                "webcam": webcam,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Run CPU-bound labeling in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                labeler.label_image,
                image,
                metadata
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in label_image_async: {e}")
            return {"status": "error", "error": str(e)}
    
    def _update_karlcam_mode(self):
        """Update KarlCam mode based on current time"""
        if self.local_testing:
            return
            
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
            current_status = self.db.get_system_status("karlcam_mode")
            if current_status and current_status.get("status_value") == new_mode:
                logger.info(f"KarlCam already in {mode_name} (mode={new_mode})")
                return
            
            # Update mode
            success = self.db.update_system_status("karlcam_mode", new_mode, "pipeline_scheduler")
            if success:
                logger.info(f"✅ Updated KarlCam to {mode_name} (mode={new_mode})")
            else:
                logger.error(f"❌ Failed to update KarlCam mode to {new_mode}")
                
        except Exception as e:
            logger.error(f"Error updating KarlCam mode: {e}")
        
    def _get_webcams(self):
        """Get active webcams from database or file"""
        if self.local_testing:
            logger.info("💾 Local testing mode - loading from webcams.json")
            webcams_file = Path("data/webcams.json")
            if webcams_file.exists():
                with open(webcams_file, 'r') as f:
                    webcams_data = json.load(f)
                    webcam_urls = [w for w in webcams_data.get("webcams", []) if w.get("active", True)]
                logger.info(f"📷 Loaded {len(webcam_urls)} webcams from {webcams_file}")
                return webcam_urls
            else:
                logger.error(f"❌ Could not find {webcams_file} for local testing")
                raise RuntimeError("webcams.json not found")
        
        logger.info("🗄️ Loading webcams from database")
        try:
            webcams = self.db.get_active_webcams()
            # Convert Webcam objects to dict format
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
            logger.info(f"📷 Loaded {len(webcam_urls)} active webcams from database")
            return webcam_urls
        except Exception as e:
            logger.error(f"❌ Failed to load webcams from database: {e}")
            logger.info("💡 Trying to load from webcams.json as fallback...")
            
            webcams_file = Path("data/webcams.json")
            if webcams_file.exists():
                with open(webcams_file, 'r') as f:
                    webcams_data = json.load(f)
                    webcam_urls = [w for w in webcams_data.get("webcams", []) if w.get("active", True)]
                logger.info(f"🎥 Loaded {len(webcam_urls)} webcams from {webcams_file}")
                return webcam_urls
            else:
                logger.error("❌ No webcams configured and database unavailable!")
                raise RuntimeError("Unable to load webcam data")
        
    def _get_webcam_url(self, webcam: Dict) -> str:
        """Get webcam URL, handling dynamic discovery for IPCamLive cameras"""
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
            # For async context, we'll use the cached URL and let discovery happen elsewhere
            logger.info(f"✅ Using cached URL for {webcam['id']}: {last_discovered_url}")
            return last_discovered_url
        
        # For pipeline, we'll use the current URL and let periodic discovery update it
        # This avoids blocking the pipeline with discovery operations
        logger.info(f"🔄 Using fallback URL for {webcam['id']}: {webcam['url']}")
        return webcam['url']
    
    async def label_image_multi_async(self, image: Image, webcam: Dict):
        """Asynchronously label image using registry (with fallback to single labeler)"""
        # Try registry-based multi-labeling first
        if self.registry:
            try:
                return await self._run_registry_labelers(image, webcam)
            except Exception as e:
                logger.warning(f"Registry labeling failed, falling back to single labeler: {e}")
        
        # Fallback to original single labeler approach
        return await self.label_image_async(image, webcam)
    
    async def _run_registry_labelers(self, image: Image, webcam: Dict):
        """Run labelers from registry"""
        # Get all enabled labelers (mode is now determined by environment)
        all_labelers = self.registry.get_ready_labelers()
        
        if not all_labelers:
            logger.warning("No labelers available in registry")
            return {"status": "error", "error": "No labelers available"}
        
        # Prepare metadata
        metadata = {
            "webcam": webcam,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        labeling_tasks = []
        
        for labeler, config in all_labelers:
            task = asyncio.create_task(
                self._run_single_labeler_with_metrics(labeler, config, image, metadata)
            )
            labeling_tasks.append(task)
        
        # Wait for all labeling tasks to complete
        results = await asyncio.gather(*labeling_tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        for i, result in enumerate(results):
            labeler, config = all_labelers[i]
            if isinstance(result, Exception):
                logger.error(f"❌ {config['name']} labeler failed: {result}")
            elif result.get('status') == 'success':
                successful_results.append(result)
                logger.info(f"✅ {config['name']}: "
                           f"Fog {result.get('fog_level', 'Unknown')} "
                           f"(score: {result.get('fog_score', 'N/A')}, "
                           f"confidence: {result.get('confidence', 'N/A')})")
            else:
                logger.error(f"❌ {config['name']} labeler returned error: {result.get('error', 'Unknown')}")
        
        if not successful_results:
            return {"status": "error", "error": "All labelers failed"}
        
        # Return all successful results
        return {
            "status": "success",
            "results": successful_results,
            "primary_result": successful_results[0]  # First successful result as primary
        }
    
    async def _run_single_labeler_with_metrics(self, labeler, config: Dict, image: Image, metadata: Dict):
        """Run a single labeler and collect metrics"""
        loop = asyncio.get_event_loop()
        
        # Run labeling in executor (CPU-bound operation)
        result = await loop.run_in_executor(
            None,
            labeler.label_image,
            image,
            metadata
        )
        
        # Add labeler metadata to result
        if isinstance(result, dict) and result.get('status') == 'success':
            # The metrics wrapper already added performance data
            result['labeler_name'] = config['name']
            result['labeler_version'] = config['version']
        
        return result
    
    def save_labels_to_db(self, image_id: int, label_results: Dict, webcam_name: str):
        """Save label results to database (handles both single and multi-labeler results)"""
        try:
            # Handle both old single result format and new multi-result format
            if label_results.get('results'):
                # Multi-labeler results
                results_to_save = label_results['results']
            elif label_results.get('status') == 'success':
                # Single labeler result (backward compatibility)
                results_to_save = [label_results]
            else:
                logger.error(f"Invalid label results format for {webcam_name}")
                return
            
            # Save each successful result
            for result in results_to_save:
                if result.get('status') != 'success':
                    continue
                
                # Extract performance metrics if available
                performance = result.get('_performance', {})
                execution_time_ms = performance.get('execution_time_ms')
                labeler_mode = performance.get('labeler_mode', 'production')
                
                # Create ImageLabel with performance metrics
                label = ImageLabel(
                    image_id=image_id,
                    labeler_name=result.get('labeler_name', 'gemini'),
                    labeler_version=result.get('labeler_version', '1.0'),
                    fog_score=result.get('fog_score'),
                    fog_level=result.get('fog_level'),
                    confidence=result.get('confidence'),
                    reasoning=result.get('reasoning'),
                    visibility_estimate=result.get('visibility_estimate'),
                    weather_conditions=result.get('weather_conditions', []),
                    label_data=result
                )
                
                # Add new performance fields - need to modify the to_dict method or save directly
                label_dict = label.to_dict()
                label_dict['labeler_mode'] = labeler_mode
                label_dict['execution_time_ms'] = execution_time_ms
                label_dict['api_cost_cents'] = performance.get('api_cost_cents')
                
                # Save using raw dict to include new fields
                self._save_label_with_metrics(label_dict)
                
                logger.info(f"🏷️ Saved {result.get('labeler_name')} label for {webcam_name} "
                           f"({labeler_mode}, {execution_time_ms}ms)")
                
        except Exception as e:
            logger.error(f"Failed to save labels for {webcam_name}: {e}")
    
    def _save_label_with_metrics(self, label_dict: Dict):
        """Save label with performance metrics using raw SQL"""
        try:
            import json
            from db.connection import execute_query
            
            # Serialize JSON fields properly
            weather_conditions_json = json.dumps(label_dict.get('weather_conditions', []))
            label_data_json = json.dumps(label_dict.get('label_data', {}))
            
            # Use raw SQL to insert with new columns
            query = """
                INSERT INTO image_labels (
                    image_id, labeler_name, labeler_version, fog_score, fog_level,
                    confidence, reasoning, visibility_estimate, weather_conditions,
                    label_data, labeler_mode, execution_time_ms, api_cost_cents
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """
            
            params = (
                label_dict.get('image_id'),
                label_dict.get('labeler_name'),
                label_dict.get('labeler_version'),
                label_dict.get('fog_score'),
                label_dict.get('fog_level'),
                label_dict.get('confidence'),
                label_dict.get('reasoning'),
                label_dict.get('visibility_estimate'),
                weather_conditions_json,
                label_data_json,
                label_dict.get('labeler_mode'),
                label_dict.get('execution_time_ms'),
                label_dict.get('api_cost_cents')
            )
            
            execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Failed to save label with metrics: {e}")
            # Fallback to standard save without metrics
            try:
                from db.models import ImageLabel
                from db.manager import save_image_label
                
                label = ImageLabel(
                    image_id=label_dict.get('image_id'),
                    labeler_name=label_dict.get('labeler_name'),
                    labeler_version=label_dict.get('labeler_version'),
                    fog_score=label_dict.get('fog_score'),
                    fog_level=label_dict.get('fog_level'),
                    confidence=label_dict.get('confidence'),
                    reasoning=label_dict.get('reasoning'),
                    visibility_estimate=label_dict.get('visibility_estimate'),
                    weather_conditions=label_dict.get('weather_conditions', []),
                    label_data=label_dict.get('label_data', {})
                )
                save_image_label(label)
                logger.info("✅ Saved label using fallback method (without metrics)")
            except Exception as fallback_error:
                logger.error(f"Fallback save also failed: {fallback_error}")

async def main():
    """Main entry point"""
    pipeline = KarlCamPipeline()
    await pipeline.run()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())