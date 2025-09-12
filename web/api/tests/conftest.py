"""
Test configuration and fixtures for KarlCam API
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the main app and dependencies
import sys
from pathlib import Path

# Add the project root directory to Python path to enable imports  
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web.api.main import app
from web.api.core.dependencies import get_db_manager
from web.api.core.config import settings

# Test settings override
class TestSettings:
    """Test-specific settings that override production settings"""
    ENVIRONMENT = "test"
    DEBUG = True
    FOG_DETECTION_THRESHOLD = 20
    FOGGY_CONDITIONS_THRESHOLD = 50
    DEFAULT_LATITUDE = 37.7749
    DEFAULT_LONGITUDE = -122.4194
    RECENT_IMAGES_DAYS = 1
    CAMERA_HISTORY_DAYS = 30
    DEFAULT_HISTORY_HOURS = 24
    STATS_PERIOD_HOURS = 24

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db_manager():
    """Mock database manager for testing"""
    mock = Mock()
    
    # Mock common methods
    mock.get_recent_images = Mock(return_value=[])
    mock.get_active_webcams = Mock(return_value=[])
    mock.get_webcam = Mock(return_value=None)
    mock.get_recent_images_with_labels = Mock(return_value=[])
    
    return mock

@pytest.fixture
def test_client(mock_db_manager):
    """Test client with mocked dependencies"""
    # Override dependencies
    app.dependency_overrides[get_db_manager] = lambda: mock_db_manager
    
    with TestClient(app) as client:
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture
async def async_test_client(mock_db_manager):
    """Async test client for testing async endpoints"""
    # Override dependencies
    app.dependency_overrides[get_db_manager] = lambda: mock_db_manager
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture
def sample_webcam_data():
    """Sample webcam data for testing"""
    return {
        "id": "test-webcam-1",
        "name": "Test Camera",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "url": "http://example.com/camera.jpg",
        "video_url": "http://example.com/camera.mp4",
        "description": "Test camera description",
        "active": True
    }

@pytest.fixture
def sample_camera_conditions():
    """Sample camera conditions data for testing"""
    return {
        "id": "test-webcam-1",
        "name": "Test Camera",
        "lat": 37.7749,
        "lon": -122.4194,
        "description": "Test camera description",
        "fog_score": 75,
        "fog_level": "Heavy Fog",
        "confidence": 0.92,
        "weather_detected": True,
        "weather_confidence": 0.88,
        "timestamp": "2024-01-10T08:30:00Z",
        "active": True
    }

@pytest.fixture
def sample_image_collection():
    """Sample image collection data for testing"""
    return {
        "id": 1,
        "webcam_id": "test-webcam-1",
        "timestamp": "2024-01-10T08:30:00Z",
        "image_filename": "test-webcam-1_20240110_083000.jpg",
        "cloud_storage_path": "gs://karlcam-test/raw_images/test-webcam-1_20240110_083000.jpg",
        "labels": [
            {
                "id": 1,
                "image_id": 1,
                "labeler_name": "gemini-1.5",
                "labeler_version": "1.5.0",
                "fog_score": 75,
                "fog_level": "Heavy Fog",
                "confidence": 0.92,
                "reasoning": "Heavy fog visible across the image with limited visibility"
            }
        ]
    }

@pytest.fixture
def sample_system_status():
    """Sample system status data for testing"""
    return {
        "karlcam_mode": 0,
        "description": "Normal operation",
        "updated_at": "2024-01-10T08:30:00Z",
        "updated_by": "system"
    }

@pytest.fixture(autouse=True)
def override_settings():
    """Override settings for all tests"""
    # Store original values
    original_values = {}
    for attr in dir(TestSettings):
        if not attr.startswith('_'):
            original_values[attr] = getattr(settings, attr, None)
            setattr(settings, attr, getattr(TestSettings, attr))
    
    yield
    
    # Restore original values
    for attr, value in original_values.items():
        if value is not None:
            setattr(settings, attr, value)

# Helper functions for tests
def create_mock_webcam(webcam_id="test-webcam", **kwargs):
    """Create a mock webcam object"""
    defaults = {
        "id": webcam_id,
        "name": f"Test Camera {webcam_id}",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "url": f"http://example.com/{webcam_id}.jpg",
        "video_url": f"http://example.com/{webcam_id}.mp4",
        "description": f"Test camera {webcam_id}",
        "active": True
    }
    defaults.update(kwargs)
    
    mock = Mock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock

def create_mock_image_with_labels(webcam_id="test-webcam", fog_score=50, **kwargs):
    """Create a mock image with labels"""
    defaults = {
        "webcam_id": webcam_id,
        "timestamp": "2024-01-10T08:30:00Z",
        "labels": [
            {
                "fog_score": fog_score,
                "fog_level": "Moderate Fog" if fog_score > 40 else "Light Fog",
                "confidence": 0.85,
                "reasoning": f"Fog score {fog_score} detected"
            }
        ]
    }
    defaults.update(kwargs)
    return defaults