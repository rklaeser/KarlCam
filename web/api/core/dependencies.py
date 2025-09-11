"""
Dependency injection setup for KarlCam Fog API
"""
import sys
import logging
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from google.cloud import storage
import psycopg2
from psycopg2 import pool

# Add parent directory to path for db imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.manager import DatabaseManager
from .config import settings

logger = logging.getLogger(__name__)

# Global instances
_db_manager = None
_db_pool = None
_storage_client = None


class DatabasePool:
    """Database connection pool manager"""
    
    def __init__(self, database_url: str, min_conn: int = 2, max_conn: int = 10):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            min_conn,
            max_conn,
            database_url
        )
        logger.info(f"Database pool created with {min_conn}-{max_conn} connections")
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)
    
    def close_all(self):
        """Close all connections in the pool"""
        self.pool.closeall()
        logger.info("Database pool closed")


def get_db_pool() -> DatabasePool:
    """Get database connection pool (singleton)"""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool(
            database_url=settings.DATABASE_URL,
            min_conn=settings.DB_POOL_MIN_CONN,
            max_conn=settings.DB_POOL_MAX_CONN
        )
    return _db_pool


def get_db_manager() -> DatabaseManager:
    """Get database manager instance (singleton)"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@contextmanager
def get_db_session() -> Generator:
    """Get database connection session"""
    pool = get_db_pool()
    with pool.get_connection() as conn:
        yield conn


def get_db():
    """Dependency for direct database connection"""
    with get_db_session() as db:
        yield db


def get_storage_client() -> storage.Client:
    """Dependency for Google Cloud Storage client (singleton)"""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


def get_bucket_name() -> str:
    """Dependency for bucket name"""
    return settings.BUCKET_NAME


def cleanup_dependencies():
    """Cleanup all global dependencies"""
    global _db_pool, _storage_client
    if _db_pool:
        _db_pool.close_all()
        _db_pool = None
    _storage_client = None
    logger.info("Dependencies cleaned up")