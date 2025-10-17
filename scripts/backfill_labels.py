#!/usr/bin/env python3
"""
Backfill script to label unlabeled images in production database
"""

import sys
import logging
import asyncio
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.manager import DatabaseManager
from db.connection import get_db_connection
from pipeline.labelers.registry import get_registry
from PIL import Image
import requests
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LabelBackfiller:
    """Backfill labels for unlabeled images"""
    
    def __init__(self, batch_size: int = 50, max_images: int = None):
        self.batch_size = batch_size
        self.max_images = max_images
        self.db_manager = DatabaseManager()
        self.registry = get_registry()
        self.bucket_name = os.getenv('BUCKET_NAME', 'karlcam-fog-data')
        
        if not self.registry:
            raise RuntimeError("Failed to initialize labeler registry")
            
        self.labelers = self.registry.get_ready_labelers()
        if not self.labelers:
            raise RuntimeError("No labelers available")
            
        logger.info(f"Initialized with {len(self.labelers)} labelers")
    
    def get_unlabeled_images(self, limit: int) -> List[Dict[str, Any]]:
        """Get batch of unlabeled images"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        ic.id,
                        ic.image_filename,
                        ic.cloud_storage_path,
                        ic.webcam_id,
                        ic.created_at,
                        w.name as webcam_name
                    FROM image_collections ic
                    LEFT JOIN image_labels il ON ic.id = il.image_id
                    LEFT JOIN webcams w ON ic.webcam_id = w.id
                    WHERE il.id IS NULL
                    AND ic.created_at >= '2025-09-26'  -- After labeling stopped
                    ORDER BY ic.created_at DESC
                    LIMIT %s
                """, (limit,))
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def get_image_from_storage(self, cloud_storage_path: str) -> Image.Image:
        """Download and load image from cloud storage"""
        # Use direct GCS URL
        image_url = f"https://storage.googleapis.com/{self.bucket_name}/raw_images/{cloud_storage_path.split('/')[-1]}"
        
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        return Image.open(BytesIO(response.content))
    
    async def label_image(self, image_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Label a single image with all available labelers"""
        try:
            # Download image
            image = self.get_image_from_storage(image_data['cloud_storage_path'])
            
            # Prepare metadata
            metadata = {
                "webcam": {
                    "id": image_data['webcam_id'],
                    "name": image_data['webcam_name']
                },
                "timestamp": image_data['created_at'].isoformat()
            }
            
            # Run all labelers
            results = []
            for labeler, config in self.labelers:
                try:
                    result = labeler.label_image(image, metadata)
                    if isinstance(result, dict) and result.get('status') == 'success':
                        result['labeler_name'] = config['name']
                        result['labeler_version'] = config['version']
                        result['image_id'] = image_data['id']
                        results.append(result)
                        logger.info(f"✅ {config['name']}: {result.get('fog_level', 'Unknown')} "
                                   f"(score: {result.get('fog_score', 'N/A')})")
                    else:
                        logger.error(f"❌ {config['name']} failed: {result}")
                except Exception as e:
                    logger.error(f"❌ {config['name']} exception: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to process image {image_data['id']}: {e}")
            return []
    
    def save_labels(self, label_results: List[Dict[str, Any]]):
        """Save label results to database"""
        if not label_results:
            return
            
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for result in label_results:
                    try:
                        cur.execute("""
                            INSERT INTO image_labels (
                                image_id, labeler_name, labeler_version,
                                fog_score, fog_level, confidence, reasoning,
                                visibility_estimate, weather_conditions, label_data,
                                execution_time_ms, api_cost_cents
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            result['image_id'],
                            result['labeler_name'],
                            result['labeler_version'],
                            result.get('fog_score'),
                            result.get('fog_level'),
                            result.get('confidence'),
                            result.get('reasoning'),
                            result.get('visibility_estimate'),
                            result.get('weather_conditions', []),
                            result,  # Full result as label_data
                            result.get('_performance', {}).get('execution_time_ms'),
                            result.get('_performance', {}).get('api_cost_cents')
                        ))
                    except Exception as e:
                        logger.error(f"Failed to save label: {e}")
                        
                conn.commit()
    
    async def run_backfill(self):
        """Run the backfill process"""
        total_processed = 0
        
        while True:
            # Get batch of unlabeled images
            remaining = None
            if self.max_images:
                remaining = self.max_images - total_processed
                if remaining <= 0:
                    break
                    
            batch_size = min(self.batch_size, remaining) if remaining else self.batch_size
            unlabeled_images = self.get_unlabeled_images(batch_size)
            
            if not unlabeled_images:
                logger.info("No more unlabeled images found")
                break
                
            logger.info(f"Processing batch of {len(unlabeled_images)} images...")
            
            # Process each image
            for i, image_data in enumerate(unlabeled_images):
                logger.info(f"Processing image {i+1}/{len(unlabeled_images)}: {image_data['image_filename']}")
                
                label_results = await self.label_image(image_data)
                if label_results:
                    self.save_labels(label_results)
                    logger.info(f"Saved {len(label_results)} labels for {image_data['image_filename']}")
                else:
                    logger.warning(f"No labels generated for {image_data['image_filename']}")
                
                total_processed += 1
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)
            
            logger.info(f"Completed batch. Total processed: {total_processed}")
            
            if len(unlabeled_images) < batch_size:
                logger.info("Reached end of unlabeled images")
                break
        
        logger.info(f"Backfill complete. Total images processed: {total_processed}")


async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill labels for unlabeled images')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of images to process per batch')
    parser.add_argument('--max-images', type=int, help='Maximum number of images to process (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually labeling')
    
    args = parser.parse_args()
    
    if args.dry_run:
        # Just show statistics
        backfiller = LabelBackfiller(args.batch_size, args.max_images)
        unlabeled = backfiller.get_unlabeled_images(args.max_images or 1000)
        logger.info(f"Would process {len(unlabeled)} unlabeled images")
        for img in unlabeled[:5]:
            logger.info(f"  - {img['image_filename']} ({img['created_at']})")
        return
    
    # Run actual backfill
    backfiller = LabelBackfiller(args.batch_size, args.max_images)
    await backfiller.run_backfill()


if __name__ == "__main__":
    asyncio.run(main())