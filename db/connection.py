"""
Database connection utilities for KarlCam
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Any, List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

logger = logging.getLogger(__name__)


def load_env_file():
    """Load environment variables from .env file if exists"""
    # Try multiple locations for .env file
    env_paths = [
        Path(__file__).parent / '.env',
        Path(__file__).parent.parent / '.env',
        Path(__file__).parent.parent / 'cloudrun' / 'deploy' / '.env'
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            logger.info(f"Loading environment from {env_path}")
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key not in os.environ:
                                os.environ[key] = value.strip('"\'')
            break


# Load environment on module import
load_env_file()


def get_connection_string() -> str:
    """Get database connection string from environment"""
    connection_string = os.getenv('DATABASE_URL')
    if not connection_string:
        raise ValueError("DATABASE_URL environment variable not set")
    return connection_string


@contextmanager
def get_db_connection(cursor_factory=None):
    """
    Get database connection context manager
    
    Args:
        cursor_factory: Optional cursor factory (e.g., RealDictCursor)
    
    Yields:
        Database connection
    """
    conn = None
    try:
        conn = psycopg2.connect(
            get_connection_string(),
            cursor_factory=cursor_factory
        )
        yield conn
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_cursor(cursor_factory=None):
    """
    Get database cursor context manager
    
    Args:
        cursor_factory: Optional cursor factory (e.g., RealDictCursor)
    
    Yields:
        Database cursor
    """
    with get_db_connection(cursor_factory=cursor_factory) as conn:
        with conn.cursor() as cursor:
            yield cursor
        conn.commit()


def execute_query(
    query: str, 
    params: Optional[tuple] = None, 
    fetch_one: bool = False,
    cursor_factory=None
) -> Any:
    """
    Execute a database query
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch_one: If True, return single row, else return all rows
        cursor_factory: Optional cursor factory
    
    Returns:
        Query results
    """
    with get_db_cursor(cursor_factory=cursor_factory) as cursor:
        cursor.execute(query, params)
        
        # Check if this is a SELECT query
        if cursor.description:
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
        
        # For non-SELECT queries, return rowcount
        return cursor.rowcount


def execute_insert(
    query: str, 
    params: Optional[tuple] = None, 
    returning: bool = False
) -> Optional[Any]:
    """
    Execute an INSERT query
    
    Args:
        query: SQL INSERT query string
        params: Query parameters
        returning: If True, return the inserted row
    
    Returns:
        Inserted row ID if returning=True, else None
    """
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        if returning and cursor.description:
            return cursor.fetchone()
        return cursor.rowcount


def execute_many(
    query: str,
    params_list: List[tuple]
) -> int:
    """
    Execute multiple INSERT/UPDATE queries
    
    Args:
        query: SQL query string
        params_list: List of parameter tuples
    
    Returns:
        Number of affected rows
    """
    with get_db_cursor() as cursor:
        cursor.executemany(query, params_list)
        return cursor.rowcount