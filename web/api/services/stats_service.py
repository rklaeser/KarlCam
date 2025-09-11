"""
Stats service containing business logic for statistics operations
"""
import logging
from datetime import datetime
from typing import Dict
import sys
from pathlib import Path

# Add parent directory to path for db imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from ..core.config import settings

logger = logging.getLogger(__name__)


class StatsService:
    """Service class for statistics operations"""
    
    def get_overall_stats(self) -> Dict:
        """Get overall fog statistics"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_assessments,
                            COUNT(DISTINCT webcam_id) as active_cameras,
                            AVG(fog_score) as avg_fog_score,
                            AVG(confidence) as avg_confidence,
                            COUNT(CASE WHEN fog_score > %s THEN 1 END) as foggy_conditions,
                            MAX(timestamp) as last_update
                        FROM image_collections 
                        WHERE status = 'success'
                            AND timestamp >= NOW() - INTERVAL '%s hours'
                    """, (settings.FOGGY_CONDITIONS_THRESHOLD, settings.STATS_PERIOD_HOURS))
                    
                    stats = cur.fetchone()
                    
                    return {
                        "total_assessments": stats['total_assessments'],
                        "active_cameras": stats['active_cameras'], 
                        "avg_fog_score": round(stats['avg_fog_score'] or 0, 2),
                        "avg_confidence": round(stats['avg_confidence'] or 0, 2),
                        "foggy_conditions": stats['foggy_conditions'],
                        "last_update": stats['last_update'].isoformat() if stats['last_update'] else None,
                        "period": f"{settings.STATS_PERIOD_HOURS} hours"
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return {
                "error": "Failed to fetch statistics",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_status(self) -> Dict:
        """Get system status including karlcam mode"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT status_key, status_value, description, updated_at, updated_by
                        FROM system_status 
                        WHERE status_key = 'karlcam_mode'
                    """)
                    
                    status = cur.fetchone()
                    if not status:
                        return {"karlcam_mode": 0, "description": "Default mode"}
                    
                    return {
                        "karlcam_mode": status['status_value'],
                        "description": status['description'],
                        "updated_at": status['updated_at'].isoformat() if status['updated_at'] else None,
                        "updated_by": status['updated_by']
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching system status: {e}")
            return {"karlcam_mode": 0, "description": "Default mode (error)"}
    
    def set_system_status(self, request: dict) -> Dict:
        """Set system status - for internal use by labeler"""
        try:
            karlcam_mode = request.get('karlcam_mode', 0)
            updated_by = request.get('updated_by', 'api')
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO system_status (status_key, status_value, updated_by, updated_at)
                        VALUES ('karlcam_mode', %s, %s, NOW())
                        ON CONFLICT (status_key) 
                        DO UPDATE SET 
                            status_value = EXCLUDED.status_value,
                            updated_by = EXCLUDED.updated_by,
                            updated_at = NOW()
                    """, (karlcam_mode, updated_by))
                    
                    conn.commit()
                    
                    return {
                        "success": True,
                        "karlcam_mode": karlcam_mode,
                        "updated_by": updated_by,
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error setting system status: {e}")
            raise