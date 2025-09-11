"""
Health check endpoints for KarlCam Fog API
"""
from fastapi import APIRouter, Depends
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for db imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.connection import get_db_connection
from ..core.dependencies import get_db_manager
from ..schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="KarlCam Fog API",
        version="2.0.0",
        timestamp=datetime.now().isoformat()
    )


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check with database status"""
    try:
        # Test database connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        return HealthResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            database="disconnected",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )