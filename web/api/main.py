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
from .routers import health, cameras, images, system
from .utils.exceptions import KarlCamException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting up KarlCam Fog API...")
    
    # Initialize database pool
    db_pool = get_db_pool()
    logger.info("Database pool initialized")
    
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

logger.info(f"KarlCam Fog API {settings.VERSION} initialized")
logger.info(f"Database URL configured: {bool(settings.DATABASE_URL)}")
logger.info(f"Bucket name: {settings.BUCKET_NAME}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)