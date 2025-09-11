#!/usr/bin/env python3
"""
KarlCam Fog API
FastAPI server that reads historical camera data assessed by Gemini from Cloud SQL database
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .core.config import settings
from .core.dependencies import get_db_pool, cleanup_dependencies
from .core.openapi import setup_openapi
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


# OpenAPI tags for endpoint organization
tags_metadata = [
    {
        "name": "Health",
        "description": "Health check and system monitoring endpoints",
    },
    {
        "name": "Cameras",
        "description": """
        Camera operations including current fog detection data and historical information.
        
        Provides real-time fog assessments from webcams around San Francisco Bay Area,
        with AI-powered analysis and historical data tracking.
        """,
    },
    {
        "name": "Images", 
        "description": "Access to camera images and visual data",
    },
    {
        "name": "System",
        "description": """
        System statistics, status monitoring, and administrative operations.
        
        Includes fog detection statistics, system health metrics, and configuration management.
        """,
    },
    {
        "name": "Configuration",
        "description": "Public configuration settings and system parameters",
    }
]

# Create FastAPI app with comprehensive metadata
app = FastAPI(
    title="KarlCam Fog Detection API",
    description="""
    ## 🌫️ Real-time Fog Detection for San Francisco Bay Area
    
    The **KarlCam API** provides comprehensive fog detection data from webcams positioned 
    strategically around the San Francisco Bay Area. Our AI-powered system analyzes images 
    in real-time to deliver accurate fog assessments and historical trends.
    
    ## ✨ Key Features
    
    * 📷 **Multiple Camera Locations** - Strategic placement across SF Bay Area
    * 🤖 **AI-Powered Detection** - Advanced computer vision for fog analysis  
    * 📊 **Historical Data** - Track fog patterns over time
    * 🗺️ **Geographic Mapping** - Precise coordinates for visualization
    * ⚡ **Real-time Updates** - Fresh data approximately every 10 minutes
    * 📱 **Developer Friendly** - RESTful API with comprehensive documentation
    
    ## 🚀 Getting Started
    
    Most endpoints are **public** and require no authentication. Simply make HTTP requests 
    to start accessing fog data:
    
    ```bash
    curl https://api.karlcam.com/api/public/cameras
    ```
    
    ## 📈 Data Freshness
    
    * **Fog Assessments**: Updated every ~10 minutes
    * **Image Collection**: Continuous monitoring during daylight hours
    * **Historical Data**: Available for up to 30 days
    * **System Statistics**: Real-time aggregation
    
    ## 🔍 Fog Detection Levels
    
    Our AI system classifies fog into these categories:
    * **Clear** (0-20) - No fog detected
    * **Light Fog** (21-40) - Minimal visibility impact  
    * **Moderate Fog** (41-60) - Noticeable fog presence
    * **Heavy Fog** (61-80) - Significant visibility reduction
    * **Very Heavy Fog** (81-100) - Dense fog conditions
    
    ## 💡 Use Cases
    
    * Weather monitoring applications
    * Transportation planning systems
    * Photography and tourism apps
    * Academic research on fog patterns
    * Maritime and aviation weather services
    
    ## 🆘 Support
    
    Need help? Check our documentation or reach out:
    * 📧 Technical Support: Open an issue on GitHub
    * 🌐 System Status: Monitor via `/health` endpoints
    * 📖 API Updates: Follow our changelog
    """,
    version=settings.VERSION,
    openapi_tags=tags_metadata,
    servers=[
        {
            "url": "https://api.karlcam.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.karlcam.com", 
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8002",
            "description": "Local development server"
        }
    ],
    contact={
        "name": "KarlCam Development Team",
        "url": "https://github.com/your-repo/karlcam",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    swagger_ui_parameters={
        "docExpansion": "list",
        "defaultModelsExpandDepth": 2, 
        "defaultModelExpandDepth": 2,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
    },
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

# Setup custom OpenAPI schema
setup_openapi(app)

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
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="debug" if settings.DEBUG else "info"
    )