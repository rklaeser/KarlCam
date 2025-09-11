"""
Dependency injection setup for KarlCam Fog API
"""
import sys
from pathlib import Path
from google.cloud import storage

# Add parent directory to path for db imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.manager import DatabaseManager
from .config import settings


def get_db_manager() -> DatabaseManager:
    """Dependency for database manager"""
    return DatabaseManager()


def get_storage_client() -> storage.Client:
    """Dependency for Google Cloud Storage client"""
    return storage.Client()


def get_bucket_name() -> str:
    """Dependency for bucket name"""
    return settings.BUCKET_NAME