"""
Core configuration module for KarlCam Fog API
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings"""
    
    # App settings
    APP_NAME: str = "KarlCam Fog API"
    VERSION: str = "2.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Google Cloud Storage
    BUCKET_NAME: str = os.getenv("BUCKET_NAME", "karlcam-fog-data")
    
    # API Settings
    API_PREFIX: str = "/api"
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]  # Configure for your domain
    
    def __post_init__(self):
        """Validate required settings"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")


# Global settings instance
settings = Settings()