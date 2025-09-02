#!/usr/bin/env python3
"""
Inspect the old KarlCam database to see what tables exist
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

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

def inspect_database():
    """Inspect the old database structure"""
    logger.info("=" * 60)
    logger.info("INSPECTING OLD KARLCAM DATABASE")
    logger.info("=" * 60)
    
    conn = get_old_connection()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            # List all tables
            logger.info("Getting all tables...")
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            
            logger.info(f"Found {len(tables)} tables:")
            for table in tables:
                logger.info(f"  • {table['table_name']}")
            
            # For each table, show structure and sample data
            for table in tables:
                table_name = table['table_name']
                logger.info("\n" + "-" * 40)
                logger.info(f"TABLE: {table_name}")
                logger.info("-" * 40)
                
                # Get column info
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cur.fetchall()
                
                logger.info("Columns:")
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    logger.info(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
                
                # Get row count
                cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cur.fetchone()['count']
                logger.info(f"Rows: {count}")
                
                # Show sample data if not empty
                if count > 0:
                    cur.execute(f"SELECT * FROM {table_name} ORDER BY 1 LIMIT 3")
                    samples = cur.fetchall()
                    logger.info("Sample rows:")
                    for i, row in enumerate(samples, 1):
                        logger.info(f"  Row {i}: {dict(row)}")
                
            logger.info("\n" + "=" * 60)
            logger.info("DATABASE INSPECTION COMPLETE")
            logger.info("=" * 60)
                
    except Exception as e:
        logger.error(f"Inspection failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_database()