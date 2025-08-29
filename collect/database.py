"""
Database utilities for Cloud SQL integration
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages Cloud SQL database connections and operations"""
    
    def __init__(self):
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable not set")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            yield conn
        finally:
            if conn:
                conn.close()
    
    def create_collection_run(self, total_images: int = 0) -> int:
        """Create a new collection run and return its ID"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collection_runs (timestamp, total_images)
                    VALUES (%s, %s)
                    RETURNING id
                """, (datetime.now(timezone.utc), total_images))
                
                collection_run_id = cur.fetchone()[0]
                conn.commit()
                
                logger.info(f"✅ Created collection run ID: {collection_run_id}")
                return collection_run_id
    
    def save_collection_result(self, collection_run_id: int, result: Dict) -> None:
        """Save individual webcam collection result to database (new simplified schema)"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Extract data from simplified scoring result
                webcam_info = result.get('webcam', {})
                
                # Convert any numpy types to native Python types
                def convert_value(val):
                    """Convert numpy types to native Python types"""
                    try:
                        import numpy as np
                        if hasattr(np, 'bool_') and isinstance(val, np.bool_):
                            return bool(val)
                        elif hasattr(np, 'bool8') and isinstance(val, np.bool8):
                            return bool(val)
                        elif isinstance(val, (np.integer, np.int_)):
                            return int(val)
                        elif isinstance(val, (np.floating, np.float_)):
                            return float(val)
                        elif isinstance(val, np.ndarray):
                            return val.tolist()
                    except (ImportError, AttributeError):
                        pass  # numpy not available or attribute doesn't exist
                    return val
                
                cur.execute("""
                    INSERT INTO image_collections (
                        collection_run_id, webcam_id, timestamp, image_filename,
                        fog_score, fog_level, confidence,
                        reasoning, visibility_estimate, weather_conditions,
                        status, error_message, cloud_storage_path
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s
                    )
                """, (
                    collection_run_id,
                    webcam_info.get('id'),
                    datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00')),
                    result.get('image_path'),
                    
                    # Gemini scoring results
                    convert_value(result.get('fog_score')),
                    result.get('fog_level'),
                    convert_value(result.get('confidence')),
                    result.get('reasoning'),
                    result.get('visibility_estimate'),
                    json.dumps(result.get('weather_conditions', [])),
                    
                    # Status and storage
                    result.get('status', 'success'),
                    result.get('error'),
                    f"gs://{os.getenv('OUTPUT_BUCKET', 'karlcam-fog-data')}/images/{result.get('image_path')}"
                ))
                
                conn.commit()
                logger.info(f"✅ Saved collection result for {webcam_info.get('name')}")
    
    def update_collection_run_summary(self, collection_run_id: int, summary: Dict) -> None:
        """Update collection run with final summary"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Only update columns that exist in the schema
                cur.execute("""
                    UPDATE collection_runs
                    SET successful_images = %s,
                        failed_images = %s,
                        summary_data = %s
                    WHERE id = %s
                """, (
                    summary.get('total_images', 0),
                    summary.get('failed_images', 0),
                    json.dumps(summary),
                    collection_run_id
                ))
                
                conn.commit()
                logger.info(f"✅ Updated collection run {collection_run_id} summary")
    
    def get_active_webcams(self) -> List[Dict]:
        """Get all active webcams from database"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, url, latitude, longitude, description, active
                    FROM webcams
                    WHERE active = true
                    ORDER BY name
                """)
                
                webcams = []
                for row in cur.fetchall():
                    webcams.append({
                        'id': row['id'],
                        'name': row['name'],
                        'url': row['url'],
                        'lat': row['latitude'],
                        'lon': row['longitude'],
                        'description': row['description'],
                        'active': row['active']
                    })
                
                logger.info(f"📡 Retrieved {len(webcams)} active webcams from database")
                return webcams
    
    def get_webcam_history(self, webcam_id: str, limit: int = 100) -> List[Dict]:
        """Get recent collection history for a webcam (new schema)"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ic.*, cr.timestamp as run_timestamp
                    FROM image_collections ic
                    JOIN collection_runs cr ON ic.collection_run_id = cr.id
                    WHERE ic.webcam_id = %s
                    ORDER BY ic.timestamp DESC
                    LIMIT %s
                """, (webcam_id, limit))
                
                return [dict(row) for row in cur.fetchall()]
    
    def get_collection_stats(self, days: int = 7) -> Dict:
        """Get collection statistics for the last N days"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_collections,
                        COUNT(DISTINCT webcam_id) as unique_webcams,
                        AVG(fog_score) as avg_fog_score,
                        AVG(confidence) as avg_confidence,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
                        COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count
                    FROM image_collections
                    WHERE timestamp >= NOW() - INTERVAL %s
                """, (f'{days} days',))
                
                return dict(cur.fetchone())