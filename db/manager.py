"""
Database manager for KarlCam
Provides high-level database operations for all components
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from psycopg2.extras import RealDictCursor

from .connection import get_db_cursor, execute_query, execute_insert
from .models import (
    Webcam, CollectionRun, ImageCollection, 
    ImageLabel, ImageSummary, FogLevel
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database manager for all KarlCam components"""
    
    # ============= Webcam Operations =============
    
    def get_active_webcams(self) -> List[Webcam]:
        """Get all active webcams"""
        query = """
            SELECT id, name, url, video_url, latitude, longitude, description, active,
                   created_at, updated_at
            FROM webcams
            WHERE active = true
            ORDER BY name
        """
        
        rows = execute_query(query, cursor_factory=RealDictCursor)
        return [
            Webcam(
                id=row['id'],
                name=row['name'],
                url=row['url'],
                video_url=row['video_url'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                description=row['description'],
                active=row['active'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]
    
    def get_webcam(self, webcam_id: str) -> Optional[Webcam]:
        """Get a specific webcam by ID"""
        query = """
            SELECT id, name, url, video_url, latitude, longitude, description, active,
                   created_at, updated_at
            FROM webcams
            WHERE id = %s
        """
        
        row = execute_query(query, (webcam_id,), fetch_one=True, cursor_factory=RealDictCursor)
        if row:
            return Webcam(**row)
        return None
    
    def save_webcam(self, webcam: Webcam) -> str:
        """Save or update a webcam"""
        query = """
            INSERT INTO webcams (id, name, url, video_url, latitude, longitude, description, active)
            VALUES (%(id)s, %(name)s, %(url)s, %(video_url)s, %(latitude)s, %(longitude)s, %(description)s, %(active)s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                url = EXCLUDED.url,
                video_url = EXCLUDED.video_url,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                description = EXCLUDED.description,
                active = EXCLUDED.active,
                updated_at = NOW()
            RETURNING id
        """
        
        result = execute_insert(query, webcam.to_dict(), returning=True)
        return result[0] if result else webcam.id
    
    # ============= Collection Operations =============
    
    def create_collection_run(self, total_images: int = 0) -> int:
        """Create a new collection run"""
        query = """
            INSERT INTO collection_runs (timestamp, total_images)
            VALUES (%s, %s)
            RETURNING id
        """
        
        result = execute_insert(
            query, 
            (datetime.utcnow(), total_images), 
            returning=True
        )
        
        collection_id = result[0] if result else None
        logger.info(f"Created collection run ID: {collection_id}")
        return collection_id
    
    def update_collection_run(self, run_id: int, summary: Dict[str, Any]):
        """Update collection run with summary data"""
        query = """
            UPDATE collection_runs
            SET successful_images = %s,
                failed_images = %s,
                summary_data = %s
            WHERE id = %s
        """
        
        execute_query(
            query,
            (
                summary.get('successful_images', 0),
                summary.get('failed_images', 0),
                json.dumps(summary),
                run_id
            )
        )
        logger.info(f"Updated collection run {run_id}")
    
    def save_image_collection(self, image: ImageCollection) -> int:
        """Save a collected image (without labels)"""
        query = """
            INSERT INTO image_collections (
                collection_run_id, webcam_id, timestamp, 
                image_filename, cloud_storage_path
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        result = execute_insert(
            query,
            (
                image.collection_run_id,
                image.webcam_id,
                image.timestamp,
                image.image_filename,
                image.cloud_storage_path
            ),
            returning=True
        )
        
        image_id = result[0] if result else None
        logger.info(f"Saved image collection: {image.image_filename} (ID: {image_id})")
        return image_id
    
    # ============= Label Operations =============
    
    def save_image_label(self, label: ImageLabel) -> int:
        """Save an image label from a labeler"""
        if not label.validate():
            raise ValueError(f"Invalid label data: {label}")
        
        query = """
            INSERT INTO image_labels (
                image_id, labeler_name, labeler_version,
                fog_score, fog_level, confidence,
                reasoning, visibility_estimate, weather_conditions,
                label_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (image_id, labeler_name, labeler_version) DO UPDATE SET
                fog_score = EXCLUDED.fog_score,
                fog_level = EXCLUDED.fog_level,
                confidence = EXCLUDED.confidence,
                reasoning = EXCLUDED.reasoning,
                visibility_estimate = EXCLUDED.visibility_estimate,
                weather_conditions = EXCLUDED.weather_conditions,
                label_data = EXCLUDED.label_data,
                created_at = NOW()
            RETURNING id
        """
        
        result = execute_insert(
            query,
            (
                label.image_id,
                label.labeler_name,
                label.labeler_version,
                label.fog_score,
                label.fog_level,
                label.confidence,
                label.reasoning,
                label.visibility_estimate,
                json.dumps(label.weather_conditions) if label.weather_conditions else '[]',
                json.dumps(label.label_data) if label.label_data else None
            ),
            returning=True
        )
        
        label_id = result[0] if result else None
        logger.info(f"Saved label for image {label.image_id} from {label.labeler_name}")
        return label_id
    
    def get_unlabeled_images(self, labeler_name: Optional[str] = None, limit: int = 100) -> List[ImageCollection]:
        """Get images that haven't been labeled (optionally by specific labeler)"""
        if labeler_name:
            query = """
                SELECT ic.* 
                FROM image_collections ic
                LEFT JOIN image_labels il ON ic.id = il.image_id 
                    AND il.labeler_name = %s
                WHERE il.id IS NULL
                ORDER BY ic.created_at DESC
                LIMIT %s
            """
            params = (labeler_name, limit)
        else:
            query = """
                SELECT ic.*
                FROM image_collections ic
                LEFT JOIN image_labels il ON ic.id = il.image_id
                WHERE il.id IS NULL
                ORDER BY ic.created_at DESC
                LIMIT %s
            """
            params = (limit,)
        
        rows = execute_query(query, params, cursor_factory=RealDictCursor)
        return [
            ImageCollection(
                id=row['id'],
                collection_run_id=row['collection_run_id'],
                webcam_id=row['webcam_id'],
                timestamp=row['timestamp'],
                image_filename=row['image_filename'],
                cloud_storage_path=row['cloud_storage_path'],
                created_at=row['created_at']
            )
            for row in rows
        ]
    
    def get_image_by_filename(self, filename: str) -> Optional[ImageCollection]:
        """Get image collection by filename"""
        query = """
            SELECT * FROM image_collections
            WHERE image_filename = %s
        """
        
        row = execute_query(query, (filename,), fetch_one=True, cursor_factory=RealDictCursor)
        if row:
            return ImageCollection(
                id=row['id'],
                collection_run_id=row['collection_run_id'],
                webcam_id=row['webcam_id'],
                timestamp=row['timestamp'],
                image_filename=row['image_filename'],
                cloud_storage_path=row['cloud_storage_path'],
                created_at=row['created_at']
            )
        return None
    
    def get_image_labels(self, image_id: int) -> List[ImageLabel]:
        """Get all labels for an image"""
        query = """
            SELECT * FROM image_labels
            WHERE image_id = %s
            ORDER BY created_at DESC
        """
        
        rows = execute_query(query, (image_id,), cursor_factory=RealDictCursor)
        labels = []
        for row in rows:
            # Parse JSON fields
            weather = row.get('weather_conditions')
            if isinstance(weather, str):
                weather = json.loads(weather) if weather else []
            
            label_data = row.get('label_data')
            if isinstance(label_data, str):
                label_data = json.loads(label_data) if label_data else None
            
            labels.append(ImageLabel(
                id=row['id'],
                image_id=row['image_id'],
                labeler_name=row['labeler_name'],
                labeler_version=row['labeler_version'],
                fog_score=row['fog_score'],
                fog_level=row['fog_level'],
                confidence=row['confidence'],
                reasoning=row['reasoning'],
                visibility_estimate=row['visibility_estimate'],
                weather_conditions=weather,
                label_data=label_data,
                created_at=row['created_at']
            ))
        
        return labels
    
    # ============= Query Operations =============
    
    def get_recent_images(self, webcam_id: Optional[str] = None, days: int = 7) -> List[Dict]:
        """Get recent images with their labels"""
        if webcam_id:
            query = """
                SELECT 
                    ic.*,
                    w.name as webcam_name,
                    COUNT(il.id) as label_count,
                    ARRAY_AGG(
                        json_build_object(
                            'labeler', il.labeler_name,
                            'version', il.labeler_version,
                            'fog_score', il.fog_score,
                            'fog_level', il.fog_level,
                            'confidence', il.confidence
                        )
                    ) FILTER (WHERE il.id IS NOT NULL) as labels
                FROM image_collections ic
                LEFT JOIN webcams w ON ic.webcam_id = w.id
                LEFT JOIN image_labels il ON ic.id = il.image_id
                WHERE ic.timestamp >= NOW() - INTERVAL '%s days'
                    AND (%s IS NULL OR ic.webcam_id = %s)
                GROUP BY ic.id, w.name
                ORDER BY ic.timestamp DESC
            """
            params = (days, webcam_id, webcam_id)
        else:
            query = """
                SELECT 
                    ic.*,
                    w.name as webcam_name,
                    COUNT(il.id) as label_count,
                    ARRAY_AGG(
                        json_build_object(
                            'labeler', il.labeler_name,
                            'version', il.labeler_version,
                            'fog_score', il.fog_score,
                            'fog_level', il.fog_level,
                            'confidence', il.confidence
                        )
                    ) FILTER (WHERE il.id IS NOT NULL) as labels
                FROM image_collections ic
                LEFT JOIN webcams w ON ic.webcam_id = w.id
                LEFT JOIN image_labels il ON ic.id = il.image_id
                WHERE ic.timestamp >= NOW() - INTERVAL '%s days'
                GROUP BY ic.id, w.name
                ORDER BY ic.timestamp DESC
            """
            params = (days,)
        
        return execute_query(query, params, cursor_factory=RealDictCursor)
    
    def get_label_comparison(self, image_id: int) -> List[Dict]:
        """Compare labels from different labelers for an image"""
        query = """
            SELECT 
                il.labeler_name,
                il.labeler_version,
                il.fog_score,
                il.fog_level,
                il.confidence,
                il.reasoning,
                il.created_at
            FROM image_labels il
            WHERE il.image_id = %s
            ORDER BY il.labeler_name, il.labeler_version
        """
        
        return execute_query(query, (image_id,), cursor_factory=RealDictCursor)
    
    def get_collection_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get collection and labeling statistics"""
        stats_query = """
            SELECT 
                COUNT(DISTINCT ic.id) as total_images,
                COUNT(DISTINCT ic.webcam_id) as unique_webcams,
                COUNT(DISTINCT il.id) as total_labels,
                COUNT(DISTINCT il.labeler_name) as unique_labelers,
                AVG(il.fog_score) as avg_fog_score,
                AVG(il.confidence) as avg_confidence
            FROM image_collections ic
            LEFT JOIN image_labels il ON ic.id = il.image_id
            WHERE ic.timestamp >= NOW() - INTERVAL '%s days'
        """
        
        fog_distribution_query = """
            SELECT 
                il.fog_level,
                COUNT(*) as count
            FROM image_labels il
            JOIN image_collections ic ON il.image_id = ic.id
            WHERE ic.timestamp >= NOW() - INTERVAL '%s days'
                AND il.fog_level IS NOT NULL
            GROUP BY il.fog_level
            ORDER BY COUNT(*) DESC
        """
        
        stats = execute_query(stats_query, (days,), fetch_one=True, cursor_factory=RealDictCursor)
        distribution = execute_query(fog_distribution_query, (days,), cursor_factory=RealDictCursor)
        
        return {
            **stats,
            'fog_distribution': distribution,
            'period_days': days
        }