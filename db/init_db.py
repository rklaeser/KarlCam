#!/usr/bin/env python3
"""
Initialize Cloud SQL database with schema and load webcam data
"""

import os
import json
import logging
from pathlib import Path

from db.connection import get_db_connection
from db.manager import DatabaseManager
from db.models import Webcam

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with schema"""
    logger.info("Initializing database schema...")
    
    # Read schema file
    schema_path = Path(__file__).parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Execute schema
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(schema_sql)
                logger.info("✅ Database schema created successfully")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("✅ Database schema already exists, skipping creation")
                else:
                    raise e
        conn.commit()


def load_webcams_data():
    """Load webcam data from webcams.json into database"""
    logger.info("Loading webcam data...")
    
    # Load webcams from JSON file
    webcams_file = Path(__file__).parent.parent / 'data' / 'webcams.json'
    if not webcams_file.exists():
        logger.warning("webcams.json not found, skipping webcam data load")
        return
    
    with open(webcams_file, 'r') as f:
        webcams_data = json.load(f)
    
    webcams = webcams_data.get('webcams', [])
    
    # Use DatabaseManager for saving webcams
    db = DatabaseManager()
    
    for webcam_data in webcams:
        webcam = Webcam(
            id=webcam_data['id'],
            name=webcam_data['name'],
            url=webcam_data['url'],
            latitude=webcam_data['lat'],
            longitude=webcam_data['lon'],
            description=webcam_data.get('description'),
            active=webcam_data.get('active', True)
        )
        
        db.save_webcam(webcam)
        logger.info(f"✅ Loaded webcam: {webcam.name}")
    
    logger.info(f"✅ Loaded {len(webcams)} webcams into database")


def verify_setup():
    """Verify database setup is working"""
    logger.info("Verifying database setup...")
    
    db = DatabaseManager()
    
    # Get active webcams
    active_webcams = db.get_active_webcams()
    
    # Get table list
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
    
    logger.info(f"✅ Database verification complete:")
    logger.info(f"   - Tables: {', '.join(tables)}")
    logger.info(f"   - Active webcams: {len(active_webcams)}")
    
    # Show sample stats
    stats = db.get_collection_stats(days=1)
    logger.info(f"   - Images collected (last 24h): {stats.get('total_images', 0)}")
    logger.info(f"   - Total labels: {stats.get('total_labels', 0)}")


if __name__ == "__main__":
    try:
        init_database()
        load_webcams_data()
        verify_setup()
        logger.info("🎉 Database initialization complete!")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise