#!/usr/bin/env python3
"""
Migrate KarlCam database to new schema structure with data preservation
Handles migration from old single-table structure to separated collection/labeling architecture
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from db.connection import get_db_connection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def inspect_current_schema() -> Dict[str, Any]:
    """Inspect current database schema to determine migration needs"""
    logger.info("🔍 Inspecting current database schema...")
    
    schema_info = {
        'tables': [],
        'needs_migration': False,
        'has_data': False,
        'migration_type': 'unknown'
    }
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            
            # Get all tables
            cur.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            schema_info['tables'] = [t[0] for t in tables if t[1] == 'BASE TABLE']
            
            logger.info(f"Found tables: {schema_info['tables']}")
            
            # Determine migration type
            if 'images' in schema_info['tables'] and 'image_collections' not in schema_info['tables']:
                schema_info['migration_type'] = 'old_to_new'
                schema_info['needs_migration'] = True
                logger.info("📝 Migration needed: Old single-table structure -> New separated structure")
                
                # Check if there's data
                cur.execute("SELECT COUNT(*) FROM images")
                image_count = cur.fetchone()[0]
                schema_info['has_data'] = image_count > 0
                logger.info(f"Found {image_count} existing images to migrate")
                
            elif 'image_collections' in schema_info['tables']:
                # Check if video_url column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'webcams' AND column_name = 'video_url'
                """)
                has_video_url = cur.fetchone() is not None
                
                if not has_video_url:
                    schema_info['migration_type'] = 'add_video_url'
                    schema_info['needs_migration'] = True
                    logger.info("📝 Migration needed: Add video_url field to webcams")
                else:
                    schema_info['migration_type'] = 'up_to_date'
                    logger.info("✅ Schema is up to date")
                    
            else:
                schema_info['migration_type'] = 'fresh_install'
                logger.info("📝 Fresh installation - will create new schema")
    
    return schema_info


def backup_existing_data() -> Dict[str, List[Dict]]:
    """Create in-memory backup of existing data before migration"""
    logger.info("💾 Creating backup of existing data...")
    
    backup = {}
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            
            # Backup webcams
            if table_exists(cur, 'webcams'):
                cur.execute("SELECT * FROM webcams")
                columns = [desc[0] for desc in cur.description]
                backup['webcams'] = [dict(zip(columns, row)) for row in cur.fetchall()]
                logger.info(f"Backed up {len(backup['webcams'])} webcams")
            
            # Backup old images table if exists
            if table_exists(cur, 'images'):
                cur.execute("SELECT * FROM images ORDER BY timestamp")
                columns = [desc[0] for desc in cur.description]
                backup['images'] = [dict(zip(columns, row)) for row in cur.fetchall()]
                logger.info(f"Backed up {len(backup['images'])} images")
                
            # Backup existing new-format tables if they exist
            for table in ['collection_runs', 'image_collections', 'image_labels']:
                if table_exists(cur, table):
                    cur.execute(f"SELECT * FROM {table}")
                    columns = [desc[0] for desc in cur.description]
                    backup[table] = [dict(zip(columns, row)) for row in cur.fetchall()]
                    logger.info(f"Backed up {len(backup[table])} records from {table}")
    
    return backup


def table_exists(cursor, table_name: str) -> bool:
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        )
    """, (table_name,))
    return cursor.fetchone()[0]


def apply_new_schema():
    """Apply the new schema structure"""
    logger.info("🏗️  Applying new database schema...")
    
    # Read and apply schema
    schema_path = Path(__file__).parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(schema_sql)
                logger.info("✅ New schema applied successfully")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("✅ Schema tables already exist")
                else:
                    raise e
        conn.commit()


def migrate_webcams_add_video_url():
    """Add video_url column to existing webcams table"""
    logger.info("📹 Adding video_url field to webcams table...")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("ALTER TABLE webcams ADD COLUMN video_url TEXT")
                logger.info("✅ Added video_url column to webcams")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("✅ video_url column already exists")
                else:
                    logger.error(f"Failed to add video_url column: {e}")
                    raise e
        conn.commit()


def migrate_old_images_to_new_structure(backup: Dict[str, List[Dict]]):
    """Migrate old images table to new separated structure"""
    logger.info("🔄 Migrating old images to new structure...")
    
    if 'images' not in backup or not backup['images']:
        logger.info("No old images to migrate")
        return
    
    old_images = backup['images']
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            
            # Group images by collection runs (by day/batch)
            collections_by_run = {}
            
            for image in old_images:
                # Create collection run identifier based on date
                image_date = image['timestamp'].date() if isinstance(image['timestamp'], datetime) else image['timestamp']
                run_key = f"{image_date}_{image.get('webcam_id', 'unknown')}"
                
                if run_key not in collections_by_run:
                    collections_by_run[run_key] = []
                collections_by_run[run_key].append(image)
            
            logger.info(f"Grouped {len(old_images)} images into {len(collections_by_run)} collection runs")
            
            # Create collection runs and migrate data
            for run_key, images in collections_by_run.items():
                logger.info(f"Migrating collection run: {run_key} ({len(images)} images)")
                
                # Create collection run
                cur.execute("""
                    INSERT INTO collection_runs (timestamp, total_images, successful_images, failed_images, summary_data)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    images[0]['timestamp'],
                    len(images),
                    len([img for img in images if img.get('cloud_storage_path')]),
                    len([img for img in images if not img.get('cloud_storage_path')]),
                    json.dumps({'migrated_from': 'old_images_table'})
                ))
                collection_run_id = cur.fetchone()[0]
                
                # Migrate images to image_collections
                for image in images:
                    # Insert into image_collections
                    cur.execute("""
                        INSERT INTO image_collections (collection_run_id, webcam_id, timestamp, image_filename, cloud_storage_path)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        collection_run_id,
                        image.get('webcam_id'),
                        image['timestamp'],
                        image.get('filename', image.get('image_filename', 'unknown')),
                        image.get('cloud_storage_path', image.get('gcs_path', ''))
                    ))
                    image_collection_id = cur.fetchone()[0]
                    
                    # Migrate labels if they exist in the old format
                    if image.get('fog_score') is not None or image.get('fog_level'):
                        cur.execute("""
                            INSERT INTO image_labels (image_id, labeler_name, labeler_version, fog_score, fog_level, confidence, reasoning, label_data)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            image_collection_id,
                            'migrated_labeler',
                            '1.0',
                            image.get('fog_score'),
                            image.get('fog_level'),
                            image.get('confidence', image.get('avg_confidence')),
                            image.get('reasoning', image.get('analysis')),
                            json.dumps({
                                'migrated_from_old_schema': True,
                                'original_data': {k: v for k, v in image.items() if v is not None}
                            })
                        ))
            
            logger.info(f"✅ Successfully migrated {len(old_images)} images to new structure")
        conn.commit()


def restore_webcams_data(backup: Dict[str, List[Dict]]):
    """Restore webcam data, adding video_url field if needed"""
    logger.info("📡 Restoring webcam data...")
    
    if 'webcams' not in backup or not backup['webcams']:
        logger.info("No webcam data to restore")
        return
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for webcam in backup['webcams']:
                # Add video_url if it doesn't exist in the backup
                if 'video_url' not in webcam:
                    webcam['video_url'] = None
                
                cur.execute("""
                    INSERT INTO webcams (id, name, url, video_url, latitude, longitude, description, active, created_at, updated_at)
                    VALUES (%(id)s, %(name)s, %(url)s, %(video_url)s, %(latitude)s, %(longitude)s, %(description)s, %(active)s, %(created_at)s, %(updated_at)s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        url = EXCLUDED.url,
                        video_url = EXCLUDED.video_url,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        description = EXCLUDED.description,
                        active = EXCLUDED.active,
                        updated_at = NOW()
                """, webcam)
            
            logger.info(f"✅ Restored {len(backup['webcams'])} webcams")
        conn.commit()


def cleanup_old_tables():
    """Clean up old tables after successful migration"""
    logger.info("🧹 Cleaning up old tables...")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Rename old images table instead of dropping it
            if table_exists(cur, 'images'):
                cur.execute("ALTER TABLE images RENAME TO images_migrated_backup")
                logger.info("✅ Renamed old images table to images_migrated_backup")
        conn.commit()


def verify_migration():
    """Verify that migration was successful"""
    logger.info("✅ Verifying migration results...")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            
            # Check table structure
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            expected_tables = {'webcams', 'collection_runs', 'image_collections', 'image_labels'}
            missing_tables = expected_tables - set(tables)
            
            if missing_tables:
                raise Exception(f"Migration failed: Missing tables {missing_tables}")
            
            logger.info(f"✅ All expected tables present: {sorted(tables)}")
            
            # Check data counts
            stats = {}
            for table in ['webcams', 'collection_runs', 'image_collections', 'image_labels']:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cur.fetchone()[0]
                logger.info(f"  {table}: {stats[table]} records")
            
            # Check webcams have video_url column
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'webcams' AND column_name = 'video_url'
            """)
            has_video_url = cur.fetchone() is not None
            
            if not has_video_url:
                raise Exception("Migration failed: webcams table missing video_url column")
            
            logger.info("✅ Webcams table has video_url column")
            
            return stats


def main():
    """Main migration function"""
    try:
        logger.info("🚀 Starting KarlCam database migration...")
        
        # Step 1: Inspect current state
        schema_info = inspect_current_schema()
        
        if not schema_info['needs_migration']:
            logger.info("✅ No migration needed - database is up to date!")
            return
            
        # Step 2: Backup existing data
        backup = backup_existing_data()
        
        # Step 3: Apply migrations based on type
        if schema_info['migration_type'] == 'old_to_new':
            logger.info("🔄 Performing full migration from old to new schema...")
            apply_new_schema()
            migrate_old_images_to_new_structure(backup)
            restore_webcams_data(backup)
            cleanup_old_tables()
            
        elif schema_info['migration_type'] == 'add_video_url':
            logger.info("📹 Adding video_url field to existing schema...")
            migrate_webcams_add_video_url()
            
        elif schema_info['migration_type'] == 'fresh_install':
            logger.info("🏗️  Fresh installation - creating new schema...")
            apply_new_schema()
        
        # Step 4: Verify migration
        stats = verify_migration()
        
        logger.info("🎉 Database migration completed successfully!")
        logger.info("Migration Summary:")
        logger.info(f"  Migration Type: {schema_info['migration_type']}")
        for table, count in stats.items():
            logger.info(f"  {table}: {count} records")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()