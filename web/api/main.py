#!/usr/bin/env python3
"""
KarlCam Fog API
FastAPI server that reads historical camera data assessed by Gemini from Cloud SQL database
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .core.config import settings
from .core.dependencies import get_db_pool, cleanup_dependencies
from .routers import health, cameras, images, system, config
from .utils.exceptions import KarlCamException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting up KarlCam Fog API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Validate configuration
    try:
        settings.__post_init__()
        logger.info("Configuration validation passed")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Initialize database pool
    db_pool = get_db_pool()
    logger.info("Database pool initialized")
    
    # Log key configuration values (non-sensitive)
    logger.info(f"Fog detection threshold: {settings.FOG_DETECTION_THRESHOLD}")
    logger.info(f"Default location: {settings.DEFAULT_LOCATION_NAME} ({settings.DEFAULT_LATITUDE}, {settings.DEFAULT_LONGITUDE})")
    logger.info(f"Recent images days: {settings.RECENT_IMAGES_DAYS}")
    logger.info(f"CORS origins: {len(settings.CORS_ORIGINS)} configured")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KarlCam Fog API...")
    
    # Cleanup dependencies
    cleanup_dependencies()


# Create FastAPI app with lifecycle management
app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
)


# Global exception handlers
@app.exception_handler(KarlCamException)
async def karlcam_exception_handler(request: Request, exc: KarlCamException):
    """Handle custom KarlCam exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "error_code": "VALIDATION_ERROR",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

# Include routers
app.include_router(health.router)
app.include_router(cameras.router, prefix=settings.API_PREFIX)
app.include_router(images.router, prefix=settings.API_PREFIX)
app.include_router(system.router, prefix=settings.API_PREFIX)
app.include_router(config.router, prefix=settings.API_PREFIX)

logger.info(f"KarlCam Fog API {settings.VERSION} initialized")
logger.info(f"Database URL configured: {bool(settings.DATABASE_URL)}")
logger.info(f"Bucket name: {settings.BUCKET_NAME}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        log_level="debug" if settings.DEBUG else "info"
    )