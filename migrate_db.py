#!/usr/bin/env python3
"""
Database Migration Job for Cloud Run
Migrates database schema from dual-method to simplified Gemini-only structure
"""

import os
import sys
import psycopg2
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the database migration"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    logger.info("🗄️  Starting database schema migration...")
    logger.info("   Migrating from dual-method to Gemini-only schema")
    
    migration_sql = """
-- Database Schema Migration: Simplify to Gemini-only approach
BEGIN;

-- 1. Create new simplified image_collections table
CREATE TABLE IF NOT EXISTS image_collections (
    id SERIAL PRIMARY KEY,
    collection_run_id INTEGER REFERENCES collection_runs(id),
    webcam_id VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE,
    image_filename VARCHAR(255),
    
    -- Gemini scoring results
    fog_score FLOAT,
    fog_level VARCHAR(50),
    confidence FLOAT,
    reasoning TEXT,
    visibility_estimate VARCHAR(50),
    weather_conditions JSONB DEFAULT '[]',
    
    -- Status and storage
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    cloud_storage_path VARCHAR(500),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fog_score_range CHECK (fog_score >= 0 AND fog_score <= 100),
    CONSTRAINT confidence_range CHECK (confidence >= 0 AND confidence <= 1.0),
    CONSTRAINT valid_fog_level CHECK (fog_level IN ('Clear', 'Light Fog', 'Moderate Fog', 'Heavy Fog', 'Very Heavy Fog', 'Error', 'Unknown')),
    CONSTRAINT valid_status CHECK (status IN ('success', 'error', 'pending'))
);

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_image_collections_run_id ON image_collections(collection_run_id);
CREATE INDEX IF NOT EXISTS idx_image_collections_webcam ON image_collections(webcam_id);
CREATE INDEX IF NOT EXISTS idx_image_collections_timestamp ON image_collections(timestamp);
CREATE INDEX IF NOT EXISTS idx_image_collections_confidence ON image_collections(confidence);
CREATE INDEX IF NOT EXISTS idx_image_collections_fog_score ON image_collections(fog_score);

-- 3. Migrate existing data from webcam_collections if it exists (Gemini data only)
INSERT INTO image_collections (
    collection_run_id,
    webcam_id,
    timestamp,
    image_filename,
    fog_score,
    fog_level,
    confidence,
    reasoning,
    visibility_estimate,
    weather_conditions,
    status,
    error_message,
    cloud_storage_path
)
SELECT 
    collection_run_id,
    webcam_id,
    timestamp,
    image_filename,
    COALESCE(gemini_score, 0) as fog_score,
    COALESCE(gemini_fog_level, 'Unknown') as fog_level,
    COALESCE(gemini_confidence, 0) as confidence,
    gemini_reasoning as reasoning,
    gemini_visibility_estimate as visibility_estimate,
    COALESCE(
        CASE 
            WHEN gemini_weather_conditions IS NULL OR TRIM(gemini_weather_conditions) = '' 
            THEN '[]'::jsonb
            WHEN gemini_weather_conditions = '""'
            THEN '[]'::jsonb
            ELSE 
                CASE 
                    WHEN gemini_weather_conditions::text ~ '^[\[{].*[\]}]$'
                    THEN gemini_weather_conditions::jsonb
                    ELSE ('["' || replace(gemini_weather_conditions, '"', '\\"') || '"]')::jsonb
                END
        END,
        '[]'::jsonb
    ) as weather_conditions,
    CASE 
        WHEN gemini_status = 'success' THEN 'success'
        WHEN gemini_status = 'error' THEN 'error'
        ELSE 'error'
    END as status,
    gemini_error as error_message,
    cloud_storage_path
FROM webcam_collections
WHERE webcam_collections.id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM image_collections WHERE image_collections.collection_run_id = webcam_collections.collection_run_id 
                AND image_collections.webcam_id = webcam_collections.webcam_id 
                AND image_collections.timestamp = webcam_collections.timestamp);

-- 4. Update collection_runs table to add new fields if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='collection_runs' AND column_name='avg_confidence') THEN
        ALTER TABLE collection_runs ADD COLUMN avg_confidence FLOAT;
    END IF;
END $$;

-- 5. Update collection_runs with calculated statistics
UPDATE collection_runs 
SET 
    successful_images = (
        SELECT COUNT(*) 
        FROM image_collections 
        WHERE image_collections.collection_run_id = collection_runs.id 
        AND image_collections.status = 'success'
    ),
    failed_images = (
        SELECT COUNT(*) 
        FROM image_collections 
        WHERE image_collections.collection_run_id = collection_runs.id 
        AND image_collections.status = 'error'
    ),
    avg_confidence = (
        SELECT AVG(confidence) 
        FROM image_collections 
        WHERE image_collections.collection_run_id = collection_runs.id 
        AND image_collections.status = 'success'
    );

COMMIT;
    """
    
    try:
        # Connect to database
        logger.info("📡 Connecting to database...")
        conn = psycopg2.connect(database_url)
        
        with conn.cursor() as cur:
            # Check current state
            logger.info("📊 Checking current database state...")
            
            # Check if old table exists
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'webcam_collections'
            """)
            old_table_exists = cur.fetchone()[0] > 0
            
            # Check if new table exists
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'image_collections'
            """)
            new_table_exists = cur.fetchone()[0] > 0
            
            if old_table_exists:
                cur.execute("SELECT COUNT(*) FROM webcam_collections")
                old_count = cur.fetchone()[0]
                logger.info(f"   Found {old_count} records in webcam_collections")
            else:
                logger.info("   No webcam_collections table found")
            
            if new_table_exists:
                cur.execute("SELECT COUNT(*) FROM image_collections")
                existing_count = cur.fetchone()[0]
                logger.info(f"   Found {existing_count} existing records in image_collections")
            
            # Run migration
            logger.info("🔄 Running migration...")
            cur.execute(migration_sql)
            
            # Verify migration
            logger.info("✅ Migration completed successfully!")
            
            # Get new record count
            cur.execute("SELECT COUNT(*) FROM image_collections")
            new_count = cur.fetchone()[0]
            logger.info(f"   Total records in image_collections: {new_count}")
            
            # Get statistics
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
                    AVG(CASE WHEN status = 'success' THEN confidence END) as avg_confidence
                FROM image_collections
            """)
            stats = cur.fetchone()
            success_count, error_count, avg_confidence = stats
            
            logger.info(f"   Success rate: {success_count}/{new_count} ({100*success_count/max(new_count,1):.1f}%)")
            if avg_confidence:
                logger.info(f"   Average confidence: {avg_confidence:.3f}")
            
            # Commit transaction
            conn.commit()
            
            logger.info("🎉 Migration completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = run_migration()
    logger.info("Migration job complete")
    sys.exit(0 if success else 1)