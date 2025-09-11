"""
Core configuration module for KarlCam Fog API
Centralized configuration with minimal environment variables
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings with centralized, hard-coded configuration"""
    
    # App settings - hard-coded
    APP_NAME: str = "KarlCam Fog API"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    
    # Environment-specific (keep as env vars for deployment flexibility)
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    BUCKET_NAME: str = os.getenv("BUCKET_NAME")
    
    # Database connection pool - hard-coded defaults
    DB_POOL_MIN_CONN: int = 2
    DB_POOL_MAX_CONN: int = 10
    DB_POOL_TIMEOUT: int = 30
    
    # Google Cloud Storage - hard-coded
    GCS_TIMEOUT: int = 30
    
    # Fog Detection Settings - hard-coded business logic
    FOG_DETECTION_THRESHOLD: int = 20
    FOGGY_CONDITIONS_THRESHOLD: int = 50
    
    # Default Location Settings - hard-coded for San Francisco
    DEFAULT_LATITUDE: float = 37.7749
    DEFAULT_LONGITUDE: float = -122.4194
    DEFAULT_LOCATION_NAME: str = "San Francisco"
    
    # Time and Data Retention Settings - hard-coded
    RECENT_IMAGES_DAYS: int = 1
    CAMERA_HISTORY_DAYS: int = 30
    DEFAULT_HISTORY_HOURS: int = 24
    STATS_PERIOD_HOURS: int = 24
    
    # CORS settings - hard-coded for simplicity
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOWED_HEADERS: List[str] = ["*"]
    
    def __post_init__(self):
        """Validate required settings"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        if not self.BUCKET_NAME:
            raise ValueError("BUCKET_NAME environment variable is required")


# Global settings instance
settings = Settings()

# Validate settings on import
settings.__post_init__()