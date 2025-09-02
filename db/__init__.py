"""
KarlCam Database Module
Centralized database access for all components
"""

from .models import (
    Webcam,
    CollectionRun,
    ImageCollection,
    ImageLabel,
    ImageSummary,
    LabelComparison
)

from .manager import DatabaseManager

from .connection import (
    get_db_connection,
    get_db_cursor,
    execute_query,
    execute_insert
)

__all__ = [
    'DatabaseManager',
    'Webcam',
    'CollectionRun', 
    'ImageCollection',
    'ImageLabel',
    'ImageSummary',
    'LabelComparison',
    'get_db_connection',
    'get_db_cursor',
    'execute_query',
    'execute_insert'
]