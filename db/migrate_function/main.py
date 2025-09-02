"""
Cloud Function for migrating images and labels from old KarlCam database to v2
"""

import os
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import functions_framework

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection_params(database_url):
    """Parse database URL to get connection parameters"""
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@/([^?]+)\?host=(.+)', database_url)
    if match:
        return {
            'user': match.group(1),
            'password': match.group(2),
            'dbname': match.group(3),
            'host': match.group(4).replace('%3A', ':')
        }
    return None

def get_old_connection():
    """Get connection to old database"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        params = get_connection_params(database_url)
        if params:
            return psycopg2.connect(**params)
    
    return psycopg2.connect(
        dbname='karlcam',
        user='karlcam',
        password='Tabudas38',
        host='/cloudsql/karlcam:us-central1:karlcam-db'
    )

def get_new_connection():
    """Get connection to new v2 database"""
    database_url_v2 = os.environ.get('DATABASE_URL_V2')
    if database_url_v2:
        params = get_connection_params(database_url_v2)
        if params:
            return psycopg2.connect(**params)
    
    return psycopg2.connect(
        dbname='karlcam_v2',
        user='karlcam_v2',
        password='NmAa6nOlOqa0Eec6fIeBVVxyrNA=',
        host='/cloudsql/karlcam:us-central1:karlcam-db'
    )

def migrate_images_to_collections():
    """Migrate old image_collections table to new image_collections structure"""
    logger.info("=" * 60)
    logger.info("MIGRATING IMAGES TO IMAGE_COLLECTIONS")
    logger.info("=" * 60)
    
    old_conn = get_old_connection()
    new_conn = get_new_connection()
    
    try:
        with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with new_conn.cursor() as new_cur:
                
                # Get all image collections from old database (collection data only)
                logger.info("Fetching image collections from old database...")
                old_cur.execute("""
                    SELECT id, collection_run_id, webcam_id, timestamp, 
                           image_filename, cloud_storage_path, created_at
                    FROM image_collections
                    ORDER BY id
                """)
                old_images = old_cur.fetchall()
                
                logger.info(f"Found {len(old_images)} images to migrate")
                
                if not old_images:
                    logger.info("No images to migrate")
                    return 0
                
                # Clear existing image_collections in v2 (be careful!)
                logger.info("Clearing existing image_collections in v2...")
                new_cur.execute("TRUNCATE TABLE image_collections RESTART IDENTITY CASCADE")
                
                # Insert images into image_collections
                migrated_count = 0
                for image in old_images:
                    try:
                        new_cur.execute("""
                            INSERT INTO image_collections 
                            (id, collection_run_id, webcam_id, timestamp, 
                             image_filename, cloud_storage_path, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                collection_run_id = EXCLUDED.collection_run_id,
                                webcam_id = EXCLUDED.webcam_id,
                                timestamp = EXCLUDED.timestamp,
                                image_filename = EXCLUDED.image_filename,
                                cloud_storage_path = EXCLUDED.cloud_storage_path,
                                created_at = EXCLUDED.created_at
                        """, (
                            image['id'],
                            image.get('collection_run_id'),
                            image['webcam_id'],
                            image['timestamp'],
                            image.get('image_filename', 'unknown'),
                            image.get('cloud_storage_path', ''),
                            image.get('created_at')
                        ))
                        migrated_count += 1
                        
                        if migrated_count % 100 == 0:
                            logger.info(f"  Migrated {migrated_count}/{len(old_images)} images...")
                            
                    except Exception as e:
                        logger.error(f"Failed to migrate image {image['id']}: {e}")
                        continue
                
                # Reset sequence
                new_cur.execute("""
                    SELECT setval('image_collections_id_seq', 
                                  COALESCE((SELECT MAX(id) FROM image_collections), 0) + 1, 
                                  false)
                """)
                
                new_conn.commit()
                logger.info(f"✅ Successfully migrated {migrated_count} images to image_collections")
                
                return migrated_count
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        new_conn.rollback()
        raise
    finally:
        old_conn.close()
        new_conn.close()

def migrate_labels():
    """Migrate labels from old image_collections table to new image_labels structure"""
    logger.info("=" * 60)
    logger.info("MIGRATING LABELS TO IMAGE_LABELS")
    logger.info("=" * 60)
    
    old_conn = get_old_connection()
    new_conn = get_new_connection()
    
    try:
        with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with new_conn.cursor() as new_cur:
                
                # Get all image collections with labels from old database
                logger.info("Fetching labeled images from old database...")
                old_cur.execute("""
                    SELECT id, fog_score, fog_level, confidence, 
                           reasoning, visibility_estimate, weather_conditions
                    FROM image_collections
                    WHERE fog_score IS NOT NULL 
                       OR fog_level IS NOT NULL
                    ORDER BY id
                """)
                labeled_images = old_cur.fetchall()
                
                logger.info(f"Found {len(labeled_images)} labeled images to migrate")
                
                if not labeled_images:
                    logger.info("No labels to migrate")
                    return 0
                
                # Clear existing labels in v2
                logger.info("Clearing existing image_labels in v2...")
                new_cur.execute("TRUNCATE TABLE image_labels RESTART IDENTITY")
                
                # Insert labels
                migrated_count = 0
                for image in labeled_images:
                    try:
                        new_cur.execute("""
                            INSERT INTO image_labels 
                            (image_id, labeler_name, labeler_version, 
                             fog_score, fog_level, confidence, reasoning,
                             visibility_estimate, weather_conditions, label_data, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (image_id, labeler_name, labeler_version) DO UPDATE SET
                                fog_score = EXCLUDED.fog_score,
                                fog_level = EXCLUDED.fog_level,
                                confidence = EXCLUDED.confidence,
                                reasoning = EXCLUDED.reasoning,
                                visibility_estimate = EXCLUDED.visibility_estimate,
                                weather_conditions = EXCLUDED.weather_conditions,
                                label_data = EXCLUDED.label_data
                        """, (
                            image['id'],  # image_id matches the id in image_collections
                            'gemini_migrated',  # labeler_name
                            '1.0',  # labeler_version
                            image.get('fog_score'),
                            image.get('fog_level'),
                            image.get('confidence'),
                            image.get('reasoning'),
                            image.get('visibility_estimate'),
                            json.dumps(image.get('weather_conditions')) if image.get('weather_conditions') else None,
                            None  # label_data - no extra data to merge
                        ))
                        migrated_count += 1
                        
                        if migrated_count % 100 == 0:
                            logger.info(f"  Migrated {migrated_count}/{len(labeled_images)} labels...")
                            
                    except Exception as e:
                        logger.error(f"Failed to migrate label for image {image['id']}: {e}")
                        continue
                
                new_conn.commit()
                logger.info(f"✅ Successfully migrated {migrated_count} labels")
                
                return migrated_count
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        new_conn.rollback()
        raise
    finally:
        old_conn.close()
        new_conn.close()

def verify_migration():
    """Verify images and labels were migrated correctly"""
    logger.info("\n" + "=" * 60)
    logger.info("VERIFYING IMAGES AND LABELS MIGRATION")
    logger.info("=" * 60)
    
    old_conn = get_old_connection()
    new_conn = get_new_connection()
    
    try:
        with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                
                # Check images/image_collections
                old_cur.execute("""
                    SELECT COUNT(*) as count FROM image_collections
                """)
                old_image_count = old_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) as count FROM image_collections")
                new_image_count = new_cur.fetchone()['count']
                
                logger.info(f"Images: {old_image_count} old -> {new_image_count} new")
                
                # Check labels
                old_cur.execute("""
                    SELECT COUNT(*) as count FROM image_collections 
                    WHERE fog_score IS NOT NULL OR fog_level IS NOT NULL
                """)
                old_label_count = old_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) as count FROM image_labels")
                new_label_count = new_cur.fetchone()['count']
                
                logger.info(f"Labels: {old_label_count} old -> {new_label_count} new")
                
                # Sample some recent data
                logger.info("\nSample recent images:")
                new_cur.execute("""
                    SELECT ic.id, ic.webcam_id, ic.timestamp, il.fog_score, il.fog_level
                    FROM image_collections ic
                    LEFT JOIN image_labels il ON ic.id = il.image_id
                    ORDER BY ic.timestamp DESC
                    LIMIT 5
                """)
                for row in new_cur.fetchall():
                    logger.info(f"  ID {row['id']}: {row['webcam_id']} at {row['timestamp']} - Score: {row['fog_score']}, Level: {row['fog_level']}")
                
                return {
                    'old_images': old_image_count,
                    'new_images': new_image_count,
                    'old_labels': old_label_count, 
                    'new_labels': new_label_count
                }
                
    finally:
        old_conn.close()
        new_conn.close()

@functions_framework.http
def migrate_karlcam_data(request):
    """HTTP Cloud Function for migrating KarlCam data"""
    try:
        logger.info("Starting KarlCam v2 Migration - Images and Labels")
        logger.info("=" * 60)
        
        # Migrate images to image_collections
        image_count = migrate_images_to_collections()
        
        # Migrate labels
        label_count = migrate_labels()
        
        # Verify everything
        verification = verify_migration()
        
        result = {
            'success': True,
            'images_migrated': image_count,
            'labels_migrated': label_count,
            'verification': verification,
            'message': f"🎉 Migration completed! Images: {image_count}, Labels: {label_count}"
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Images and labels migration finished!")
        logger.info(f"  • Images: {image_count}")
        logger.info(f"  • Labels: {label_count}")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': f"Migration failed: {e}"
        }, 500