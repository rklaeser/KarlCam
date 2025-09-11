#!/usr/bin/env python3
"""
KarlCam Fog API
FastAPI server that reads historical camera data assessed by Gemini from Cloud SQL database
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .routers import health, cameras, images, system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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