#!/usr/bin/env python3
"""
Simple migration script that can be run with local credentials
Use the secrets that we know work from the Cloud Run jobs
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connections():
    """Get both database connections"""
    # Use the same credentials that work in Cloud Run
    old_conn = psycopg2.connect(
        dbname='karlcam',
        user='karlcam', 
        password='Tabudas38',
        host='/cloudsql/karlcam:us-central1:karlcam-db'
    )
    
    new_conn = psycopg2.connect(
        dbname='karlcam_v2',
        user='karlcam_v2',
        password='NmAa6nOlOqa0Eec6fIeBVVxyrNA=',
        host='/cloudsql/karlcam:us-central1:karlcam-db'
    )
    
    return old_conn, new_conn

def migrate():
    """Run the migration"""
    logger.info("Starting KarlCam v2 Migration - Images and Labels")
    logger.info("=" * 60)
    
    old_conn, new_conn = get_connections()
    
    try:
        with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with new_conn.cursor() as new_cur:
                
                # STEP 1: Migrate image collections (collection data only)
                logger.info("STEP 1: Migrating image collections...")
                
                old_cur.execute("""
                    SELECT id, collection_run_id, webcam_id, timestamp, 
                           image_filename, cloud_storage_path, created_at
                    FROM image_collections
                    ORDER BY id
                """)
                old_images = old_cur.fetchall()
                logger.info(f"Found {len(old_images)} images to migrate")
                
                # Clear existing image_collections in v2
                new_cur.execute("TRUNCATE TABLE image_collections RESTART IDENTITY CASCADE")
                
                # Insert images into image_collections
                migrated_images = 0
                for image in old_images:
                    new_cur.execute("""
                        INSERT INTO image_collections 
                        (id, collection_run_id, webcam_id, timestamp, 
                         image_filename, cloud_storage_path, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        image['id'],
                        image.get('collection_run_id'),
                        image['webcam_id'],
                        image['timestamp'],
                        image.get('image_filename', 'unknown'),
                        image.get('cloud_storage_path', ''),
                        image.get('created_at')
                    ))
                    migrated_images += 1
                
                # Reset sequence
                new_cur.execute("""
                    SELECT setval('image_collections_id_seq', 
                                  COALESCE((SELECT MAX(id) FROM image_collections), 0) + 1, 
                                  false)
                """)
                
                logger.info(f"✅ Migrated {migrated_images} images to image_collections")
                
                # STEP 2: Migrate labels
                logger.info("STEP 2: Migrating labels...")
                
                old_cur.execute("""
                    SELECT id, fog_score, fog_level, confidence, 
                           reasoning, visibility_estimate, weather_conditions
                    FROM image_collections
                    WHERE fog_score IS NOT NULL OR fog_level IS NOT NULL
                    ORDER BY id
                """)
                labeled_images = old_cur.fetchall()
                logger.info(f"Found {len(labeled_images)} labeled images to migrate")
                
                # Clear existing labels in v2
                new_cur.execute("TRUNCATE TABLE image_labels RESTART IDENTITY")
                
                # Insert labels
                migrated_labels = 0
                for image in labeled_images:
                    new_cur.execute("""
                        INSERT INTO image_labels 
                        (image_id, labeler_name, labeler_version, 
                         fog_score, fog_level, confidence, reasoning,
                         visibility_estimate, weather_conditions, label_data, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        image['id'],
                        'gemini_migrated',
                        '1.0', 
                        image.get('fog_score'),
                        image.get('fog_level'),
                        image.get('confidence'),
                        image.get('reasoning'),
                        image.get('visibility_estimate'),
                        json.dumps(image.get('weather_conditions')) if image.get('weather_conditions') else None,
                        None
                    ))
                    migrated_labels += 1
                
                logger.info(f"✅ Migrated {migrated_labels} labels to image_labels")
                
                # STEP 3: Verify
                logger.info("STEP 3: Verifying migration...")
                
                old_cur.execute("SELECT COUNT(*) as count FROM image_collections")
                old_image_count = old_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) as count FROM image_collections")
                new_image_count = new_cur.fetchone()['count']
                
                old_cur.execute("""
                    SELECT COUNT(*) as count FROM image_collections 
                    WHERE fog_score IS NOT NULL OR fog_level IS NOT NULL
                """)
                old_label_count = old_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) as count FROM image_labels")
                new_label_count = new_cur.fetchone()['count']
                
                logger.info(f"Images: {old_image_count} old -> {new_image_count} new")
                logger.info(f"Labels: {old_label_count} old -> {new_label_count} new")
                
                # Commit everything
                new_conn.commit()
                
                logger.info("\n" + "=" * 60)
                logger.info("🎉 Migration completed successfully!")
                logger.info(f"  • Images migrated: {migrated_images}")
                logger.info(f"  • Labels migrated: {migrated_labels}")
                logger.info("=" * 60)
                
                return {
                    'images_migrated': migrated_images,
                    'labels_migrated': migrated_labels,
                    'verification': {
                        'old_images': old_image_count,
                        'new_images': new_image_count,
                        'old_labels': old_label_count,
                        'new_labels': new_label_count
                    }
                }
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        new_conn.rollback()
        raise
    finally:
        old_conn.close()
        new_conn.close()

if __name__ == "__main__":
    migrate()