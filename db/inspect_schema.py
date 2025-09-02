#!/usr/bin/env python3
"""
Inspect current database schema to understand what needs to be migrated
"""

import os
import json
import logging
from pathlib import Path

from db.connection import get_db_connection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def inspect_current_schema():
    """Inspect current database schema and data"""
    logger.info("Inspecting current database schema...")
    
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
            
            logger.info(f"Found {len(tables)} tables:")
            for table_name, table_type in tables:
                logger.info(f"  - {table_name} ({table_type})")
            
            # For each table, get column information and row counts
            schema_info = {}
            
            for table_name, table_type in tables:
                if table_type == 'BASE TABLE':
                    # Get columns
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))
                    columns = cur.fetchall()
                    
                    # Get row count
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cur.fetchone()[0]
                    
                    schema_info[table_name] = {
                        'columns': columns,
                        'row_count': row_count
                    }
                    
                    logger.info(f"\n{table_name} ({row_count} rows):")
                    for col_name, data_type, nullable, default in columns:
                        logger.info(f"  - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
            
            # Get indexes
            cur.execute("""
                SELECT indexname, tablename, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            indexes = cur.fetchall()
            
            logger.info(f"\nFound {len(indexes)} indexes:")
            for idx_name, table_name, idx_def in indexes:
                logger.info(f"  - {table_name}.{idx_name}")
            
            # Get foreign keys
            cur.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='public'
            """)
            foreign_keys = cur.fetchall()
            
            logger.info(f"\nFound {len(foreign_keys)} foreign keys:")
            for table, column, ref_table, ref_column in foreign_keys:
                logger.info(f"  - {table}.{column} -> {ref_table}.{ref_column}")
            
            return {
                'tables': schema_info,
                'indexes': indexes,
                'foreign_keys': foreign_keys
            }


def analyze_data_patterns():
    """Analyze data patterns to understand migration needs"""
    logger.info("Analyzing data patterns...")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            
            # Check if we have the old or new schema
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN ('images', 'image_collections', 'collection_runs')
            """)
            existing_tables = [row[0] for row in cur.fetchall()]
            
            if 'images' in existing_tables:
                logger.info("Found old schema with 'images' table")
                
                # Analyze old images table
                cur.execute("SELECT COUNT(*) FROM images")
                image_count = cur.fetchone()[0]
                logger.info(f"  - Total images: {image_count}")
                
                # Check column structure
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = 'images'
                    ORDER BY ordinal_position
                """)
                image_columns = cur.fetchall()
                logger.info(f"  - Image table columns: {[col[0] for col in image_columns]}")
                
                # Sample some data
                cur.execute("SELECT * FROM images LIMIT 3")
                sample_rows = cur.fetchall()
                logger.info(f"  - Sample data structure: {len(sample_rows)} rows")
                
            elif 'image_collections' in existing_tables:
                logger.info("Found new schema with separated tables")
                
                cur.execute("SELECT COUNT(*) FROM image_collections")
                collection_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM image_labels") 
                label_count = cur.fetchone()[0]
                
                logger.info(f"  - Image collections: {collection_count}")
                logger.info(f"  - Labels: {label_count}")
            
            else:
                logger.info("No image-related tables found")


if __name__ == "__main__":
    try:
        schema_info = inspect_current_schema()
        analyze_data_patterns()
        logger.info("✅ Schema inspection complete!")
    except Exception as e:
        logger.error(f"❌ Schema inspection failed: {e}")
        raise