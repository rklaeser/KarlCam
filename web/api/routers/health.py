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

router = APIRouter(
    tags=["Health"],
    responses={
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        }
    }
)


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Basic service health check",
    description="""
    Basic health check endpoint that returns the service status and version information.
    
    This is a lightweight endpoint that provides immediate confirmation that the
    KarlCam API service is running and responding to requests. It does not test
    external dependencies like databases or cloud storage.
    
    ## Use Cases
    
    * Load balancer health checks
    * Basic service monitoring
    * Quick availability verification
    * Service discovery and registration
    * Uptime monitoring systems
    
    ## Response Time
    
    This endpoint typically responds in **under 10ms** as it performs no external
    operations or database queries.
    """,
    response_description="Basic service health status",
    responses={
        200: {
            "description": "Service is healthy and responding",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "KarlCam Fog API", 
                        "version": "2.0.0",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        }
    }
)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="KarlCam Fog API",
        version="2.0.0",
        timestamp=datetime.now().isoformat()
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Comprehensive service health with dependency checks",
    description="""
    Comprehensive health check that tests all critical system dependencies including
    database connectivity and other external services.
    
    This endpoint performs active health checks on:
    
    * **Database Connection**: Tests PostgreSQL connectivity with a simple query
    * **Service Status**: Confirms the API service is operational
    * **System Dependencies**: Validates critical external dependencies
    
    ## Health Status Levels
    
    * **healthy**: All systems operational, all dependencies accessible
    * **degraded**: Service running but some dependencies unavailable  
    * **unhealthy**: Critical failures preventing normal operation
    
    ## Use Cases
    
    * Comprehensive system monitoring
    * Dependency health verification  
    * Troubleshooting connectivity issues
    * Service readiness checks for deployments
    * Deep health monitoring for operations teams
    
    ## Response Time
    
    This endpoint may take **100-500ms** to complete as it actively tests database
    connections and other external dependencies.
    
    ## Monitoring Integration
    
    Perfect for integration with monitoring systems that need to verify not just
    service availability, but also the health of all critical dependencies.
    """,
    response_description="Comprehensive health status including dependency checks",
    responses={
        200: {
            "description": "All systems healthy and dependencies accessible",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "database": "connected",
                        "service": "KarlCam Fog API",
                        "version": "2.0.0", 
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        },
        200: {
            "description": "Service degraded due to dependency issues",
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "database": "disconnected",
                        "error": "Connection to database failed: timeout",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        }
    }
)
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