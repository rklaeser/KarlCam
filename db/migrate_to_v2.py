#!/usr/bin/env python3
"""
Migrate data from old KarlCam database to v2 database
Table by table migration with data preservation
"""

import os
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection_params(database_url):
    """Parse database URL to get connection parameters"""
    # Format: postgresql://user:password@/dbname?host=/cloudsql/...
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@/([^?]+)\?host=(.+)', database_url)
    if match:
        return {
            'user': match.group(1),
            'password': match.group(2),
            'dbname': match.group(3),
            'host': match.group(4).replace('%3A', ':')  # URL decode colons
        }
    return None


def get_old_connection():
    """Get connection to old database"""
    # Try to get from DATABASE_URL environment variable (Cloud Run)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        params = get_connection_params(database_url)
        if params:
            return psycopg2.connect(**params)
    
    # Fallback to hardcoded for local testing
    return psycopg2.connect(
        dbname='karlcam',
        user='karlcam',
        password='Tabudas38',
        host='/cloudsql/karlcam:us-central1:karlcam-db'
    )


def get_new_connection():
    """Get connection to new v2 database"""
    # Try to get from DATABASE_URL_V2 environment variable (Cloud Run)
    database_url_v2 = os.environ.get('DATABASE_URL_V2')
    if database_url_v2:
        params = get_connection_params(database_url_v2)
        if params:
            return psycopg2.connect(**params)
    
    # Fallback to hardcoded for local testing
    return psycopg2.connect(
        dbname='karlcam_v2',
        user='karlcam_v2',
        password='NmAa6nOlOqa0Eec6fIeBVVxyrNA=',
        host='/cloudsql/karlcam:us-central1:karlcam-db'
    )


def migrate_collection_runs():
    """Migrate collection_runs table from old to new database"""
    logger.info("=" * 60)
    logger.info("MIGRATING COLLECTION_RUNS TABLE")
    logger.info("=" * 60)
    
    old_conn = get_old_connection()
    new_conn = get_new_connection()
    
    try:
        with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with new_conn.cursor() as new_cur:
                
                # Check if collection_runs exists in old database
                old_cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'collection_runs'
                    )
                """)
                if not old_cur.fetchone()['exists']:
                    logger.warning("collection_runs table doesn't exist in old database")
                    return 0
                
                # Get all collection_runs from old database
                logger.info("Fetching collection_runs from old database...")
                old_cur.execute("""
                    SELECT id, timestamp, total_images, successful_images, 
                           failed_images, summary_data, created_at
                    FROM collection_runs
                    ORDER BY id
                """)
                old_runs = old_cur.fetchall()
                
                logger.info(f"Found {len(old_runs)} collection runs to migrate")
                
                if not old_runs:
                    logger.info("No collection runs to migrate")
                    return 0
                
                # Clear existing data in new table (optional - comment out if appending)
                logger.info("Clearing existing collection_runs in v2 database...")
                new_cur.execute("TRUNCATE TABLE collection_runs RESTART IDENTITY CASCADE")
                
                # Insert collection runs into new database
                migrated_count = 0
                for run in old_runs:
                    try:
                        new_cur.execute("""
                            INSERT INTO collection_runs 
                            (id, timestamp, total_images, successful_images, 
                             failed_images, summary_data, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                timestamp = EXCLUDED.timestamp,
                                total_images = EXCLUDED.total_images,
                                successful_images = EXCLUDED.successful_images,
                                failed_images = EXCLUDED.failed_images,
                                summary_data = EXCLUDED.summary_data,
                                created_at = EXCLUDED.created_at
                        """, (
                            run['id'],
                            run['timestamp'],
                            run.get('total_images', 0),
                            run.get('successful_images', 0),
                            run.get('failed_images', 0),
                            json.dumps(run['summary_data']) if run.get('summary_data') else None,
                            run.get('created_at')
                        ))
                        migrated_count += 1
                        
                        if migrated_count % 100 == 0:
                            logger.info(f"  Migrated {migrated_count}/{len(old_runs)} runs...")
                            
                    except Exception as e:
                        logger.error(f"Failed to migrate run {run['id']}: {e}")
                        continue
                
                # Reset sequence to max ID + 1
                new_cur.execute("""
                    SELECT setval('collection_runs_id_seq', 
                                  COALESCE((SELECT MAX(id) FROM collection_runs), 0) + 1, 
                                  false)
                """)
                
                new_conn.commit()
                logger.info(f"✅ Successfully migrated {migrated_count} collection runs")
                
                # Verify migration
                new_cur.execute("SELECT COUNT(*) FROM collection_runs")
                new_count = new_cur.fetchone()[0]
                logger.info(f"Verification: {new_count} collection runs in v2 database")
                
                return migrated_count
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        new_conn.rollback()
        raise
    finally:
        old_conn.close()
        new_conn.close()


def verify_collection_runs():
    """Verify the migration of collection_runs"""
    logger.info("\n" + "=" * 60)
    logger.info("VERIFYING COLLECTION_RUNS MIGRATION")
    logger.info("=" * 60)
    
    old_conn = get_old_connection()
    new_conn = get_new_connection()
    
    try:
        with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
            with new_conn.cursor(cursor_factory=RealDictCursor) as new_cur:
                
                # Compare counts
                old_cur.execute("SELECT COUNT(*) as count FROM collection_runs")
                old_count = old_cur.fetchone()['count']
                
                new_cur.execute("SELECT COUNT(*) as count FROM collection_runs")
                new_count = new_cur.fetchone()['count']
                
                logger.info(f"Old database: {old_count} collection runs")
                logger.info(f"New database: {new_count} collection runs")
                
                if old_count != new_count:
                    logger.warning(f"⚠️  Count mismatch! Missing {old_count - new_count} runs")
                else:
                    logger.info("✅ Count matches!")
                
                # Compare some sample data
                old_cur.execute("""
                    SELECT id, timestamp, total_images, successful_images
                    FROM collection_runs
                    ORDER BY timestamp DESC
                    LIMIT 5
                """)
                old_sample = old_cur.fetchall()
                
                new_cur.execute("""
                    SELECT id, timestamp, total_images, successful_images
                    FROM collection_runs
                    ORDER BY timestamp DESC
                    LIMIT 5
                """)
                new_sample = new_cur.fetchall()
                
                logger.info("\nLatest 5 runs comparison:")
                logger.info("-" * 40)
                for i, (old, new) in enumerate(zip(old_sample, new_sample)):
                    match = old['id'] == new['id'] and old['total_images'] == new['total_images']
                    status = "✅" if match else "❌"
                    logger.info(f"{status} Run {old['id']}: {old['timestamp']} - {old['total_images']} images")
                
    finally:
        old_conn.close()
        new_conn.close()


if __name__ == "__main__":
    try:
        logger.info("Starting KarlCam v2 Migration - Collection Runs")
        logger.info("=" * 60)
        
        # Migrate collection_runs
        count = migrate_collection_runs()
        
        # Verify the migration
        verify_collection_runs()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Collection runs migration complete!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise