#!/usr/bin/env python3
"""
Initialize Cloud SQL database with schema and load webcam data
"""

import os
import json
import psycopg2
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        logger.info(f"Loading environment from {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\'')

load_env_file()

def get_db_connection():
    """Get database connection using Cloud SQL connection string"""
    connection_string = os.getenv('DATABASE_URL')
    if not connection_string:
        raise ValueError("DATABASE_URL environment variable not set")
    
    return psycopg2.connect(connection_string)

def init_database():
    """Initialize database with schema"""
    logger.info("Initializing database schema...")
    
    # Read schema file
    schema_path = Path(__file__).parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Execute schema with error handling for existing objects
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(schema_sql)
                logger.info("✅ Database schema created successfully")
            except psycopg2.Error as e:
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
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for webcam in webcams:
                # Insert or update webcam
                cur.execute("""
                    INSERT INTO webcams (id, name, url, latitude, longitude, description, active)
                    VALUES (%(id)s, %(name)s, %(url)s, %(lat)s, %(lon)s, %(description)s, %(active)s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        url = EXCLUDED.url,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        description = EXCLUDED.description,
                        active = EXCLUDED.active,
                        updated_at = NOW()
                """, webcam)
                
                logger.info(f"✅ Loaded webcam: {webcam['name']}")
        
        conn.commit()
    
    logger.info(f"✅ Loaded {len(webcams)} webcams into database")

def verify_setup():
    """Verify database setup is working"""
    logger.info("Verifying database setup...")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check webcams table
            cur.execute("SELECT COUNT(*) FROM webcams WHERE active = true")
            active_webcams = cur.fetchone()[0]
            
            # Check tables exist
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
    
    logger.info(f"✅ Database verification complete:")
    logger.info(f"   - Tables: {', '.join(tables)}")
    logger.info(f"   - Active webcams: {active_webcams}")

if __name__ == "__main__":
    try:
        init_database()
        load_webcams_data()
        verify_setup()
        logger.info("🎉 Database initialization complete!")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise