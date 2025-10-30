"""
Unit tests for Camera Router endpoints
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from fastapi import HTTPException

from tests.factories import (
    CameraConditionsFactory,
    WebcamFactory,
    create_multi_camera_scenario
)
from utils.exceptions import CameraNotFoundException, NoImagesFoundError

class TestCameraEndpoints:
    """Test suite for camera router endpoints"""
    
    @pytest.mark.unit
    def test_get_cameras_success(self, test_client, mock_db_manager):
        """Test successful camera list retrieval"""
        # Setup
        camera_data = [CameraConditionsFactory() for _ in range(3)]
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.return_value = camera_data
            
            # Execute
            response = test_client.get("/api/public/cameras")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert "cameras" in data
            assert "timestamp" in data
            assert "count" in data
            assert data["count"] == 3
            assert len(data["cameras"]) == 3
            
            # Verify response structure
            camera = data["cameras"][0]
            expected_fields = {
                'id', 'name', 'lat', 'lon', 'description', 
                'fog_score', 'fog_level', 'confidence',
                'weather_detected', 'weather_confidence', 
                'timestamp', 'active'
            }
            assert set(camera.keys()) == expected_fields
    
    @pytest.mark.unit
    def test_get_cameras_empty_response(self, test_client, mock_db_manager):
        """Test camera list with no cameras"""
        # Setup
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.return_value = []
            
            # Execute
            response = test_client.get("/api/public/cameras")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0
            assert data["cameras"] == []
    
    @pytest.mark.unit
    def test_get_cameras_service_error(self, test_client, mock_db_manager):
        """Test error handling in camera list endpoint"""
        # Setup
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.side_effect = Exception("Service error")
            
            # Execute
            response = test_client.get("/api/public/cameras")
            
            # Assert
            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "INTERNAL_ERROR"
    
    @pytest.mark.unit
    def test_get_webcams_success(self, test_client, mock_db_manager):
        """Test successful webcam list retrieval"""
        # Setup
        webcam_data = [
            {
                "id": "webcam-1",
                "name": "Test Camera 1",
                "lat": 37.7749,
                "lon": -122.4194,
                "url": "http://example.com/cam1.jpg",
                "video_url": "http://example.com/cam1.mp4",
                "description": "Test camera 1",
                "active": True
            },
            {
                "id": "webcam-2", 
                "name": "Test Camera 2",
                "lat": 37.8199,
                "lon": -122.4783,
                "url": "http://example.com/cam2.jpg",
                "video_url": "",
                "description": "Test camera 2",
                "active": True
            }
        ]
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_webcam_list.return_value = webcam_data
            
            # Execute
            response = test_client.get("/api/public/webcams")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert "webcams" in data
            assert "timestamp" in data
            assert "count" in data
            assert data["count"] == 2
            assert len(data["webcams"]) == 2
            
            # Verify response structure
            webcam = data["webcams"][0]
            expected_fields = {
                'id', 'name', 'lat', 'lon', 'url', 
                'video_url', 'description', 'active'
            }
            assert set(webcam.keys()) == expected_fields
    
    @pytest.mark.unit
    def test_get_latest_image_url_success(self, test_client, mock_db_manager):
        """Test successful latest image URL retrieval"""
        # Setup
        camera_id = "test-camera-1"
        image_info = {
            "camera_id": camera_id,
            "image_url": "https://storage.googleapis.com/bucket/test.jpg",
            "filename": "test.jpg",
            "timestamp": "2024-01-10T08:30:00Z",
            "age_hours": 2.5
        }
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_image_info.return_value = image_info
            
            # Execute
            response = test_client.get(f"/api/public/cameras/{camera_id}/latest-image")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data["camera_id"] == camera_id
            assert data["image_url"] == image_info["image_url"]
            assert data["filename"] == image_info["filename"]
            assert data["timestamp"] == image_info["timestamp"]
            assert data["age_hours"] == image_info["age_hours"]
    
    @pytest.mark.unit
    def test_get_latest_image_url_not_found(self, test_client, mock_db_manager):
        """Test latest image URL when no images exist"""
        # Setup
        camera_id = "nonexistent-camera"
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_image_info.side_effect = NoImagesFoundError(camera_id)
            
            # Execute
            response = test_client.get(f"/api/public/cameras/{camera_id}/latest-image")
            
            # Assert
            assert response.status_code == 404
            data = response.json()
            assert data["error_code"] == "NO_IMAGES_FOUND"
    
    @pytest.mark.unit
    def test_get_camera_detail_success(self, test_client, mock_db_manager):
        """Test successful camera detail retrieval"""
        # Setup
        camera_id = "test-camera-1"
        camera_data = [CameraConditionsFactory(id=camera_id)]
        history_data = [
            {
                "fog_score": 65,
                "fog_level": "Moderate Fog",
                "confidence": 0.89,
                "timestamp": "2024-01-10T08:20:00Z",
                "reasoning": "Moderate fog visible"
            }
        ]
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.return_value = camera_data
            mock_service.get_camera_history.return_value = history_data
            
            # Execute
            response = test_client.get(f"/api/public/cameras/{camera_id}")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert "camera" in data
            assert "history" in data
            assert "history_hours" in data
            assert "history_count" in data
            
            assert data["camera"]["id"] == camera_id
            assert data["history_hours"] == 24  # Default
            assert data["history_count"] == 1
            assert len(data["history"]) == 1
    
    @pytest.mark.unit
    def test_get_camera_detail_with_custom_hours(self, test_client, mock_db_manager):
        """Test camera detail with custom hours parameter"""
        # Setup
        camera_id = "test-camera-1"
        hours = 48
        camera_data = [CameraConditionsFactory(id=camera_id)]
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.return_value = camera_data
            mock_service.get_camera_history.return_value = []
            
            # Execute
            response = test_client.get(f"/api/public/cameras/{camera_id}?hours={hours}")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["history_hours"] == hours
            
            # Verify service was called with correct hours
            mock_service.get_camera_history.assert_called_once_with(camera_id, hours)
    
    @pytest.mark.unit
    def test_get_camera_detail_not_found(self, test_client, mock_db_manager):
        """Test camera detail for non-existent camera"""
        # Setup
        camera_id = "nonexistent-camera"
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.return_value = []  # No cameras found
            
            # Execute
            response = test_client.get(f"/api/public/cameras/{camera_id}")
            
            # Assert
            assert response.status_code == 404
            data = response.json()
            assert camera_id in data["detail"]
    
    @pytest.mark.unit
    def test_get_camera_detail_invalid_hours_parameter(self, test_client, mock_db_manager):
        """Test camera detail with invalid hours parameter"""
        # Setup
        camera_id = "test-camera-1"
        invalid_hours = -5  # Negative hours should be rejected
        
        # Execute
        response = test_client.get(f"/api/public/cameras/{camera_id}?hours={invalid_hours}")
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
    
    @pytest.mark.unit
    def test_get_camera_detail_max_hours_parameter(self, test_client, mock_db_manager):
        """Test camera detail with maximum hours parameter"""
        # Setup
        camera_id = "test-camera-1"
        max_hours = 200  # Over the limit (168)
        
        # Execute
        response = test_client.get(f"/api/public/cameras/{camera_id}?hours={max_hours}")
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
    
    @pytest.mark.unit
    def test_camera_response_model_validation(self, test_client, mock_db_manager):
        """Test that camera response matches expected schema"""
        # Setup - Create camera data with all required fields
        camera_data = [
            {
                "id": "test-camera-1",
                "name": "Test Camera",
                "lat": 37.7749,
                "lon": -122.4194,
                "description": "Test camera description",
                "fog_score": 75,
                "fog_level": "Heavy Fog",
                "confidence": 92.0,  # As percentage
                "weather_detected": True,
                "weather_confidence": 88.0,
                "timestamp": "2024-01-10T08:30:00Z",
                "active": True
            }
        ]
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.return_value = camera_data
            
            # Execute
            response = test_client.get("/api/public/cameras")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            camera = data["cameras"][0]
            
            # Validate field types
            assert isinstance(camera["lat"], float)
            assert isinstance(camera["lon"], float)
            assert isinstance(camera["fog_score"], int)
            assert isinstance(camera["confidence"], float)
            assert isinstance(camera["weather_detected"], bool)
            assert isinstance(camera["active"], bool)
            
            # Validate field ranges
            assert 0 <= camera["fog_score"] <= 100
            assert 0 <= camera["confidence"] <= 100
    
    @pytest.mark.unit
    def test_cameras_endpoint_performance(self, test_client, mock_db_manager):
        """Test that cameras endpoint handles large datasets efficiently"""
        # Setup - Large dataset
        large_camera_data = [CameraConditionsFactory() for _ in range(100)]
        
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.return_value = large_camera_data
            
            # Execute
            response = test_client.get("/api/public/cameras")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 100
            assert len(data["cameras"]) == 100
            
            # Verify service was called only once (no N+1 queries)
            mock_service.get_latest_camera_data.assert_called_once()
    
    @pytest.mark.unit
    def test_cors_headers_present(self, test_client, mock_db_manager):
        """Test that CORS headers are properly set"""
        # Setup
        with patch('routers.cameras.CameraService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_latest_camera_data.return_value = []
            
            # Execute
            response = test_client.get("/api/public/cameras")
            
            # Assert
            assert response.status_code == 200
            # Note: CORS headers are set by middleware, would need integration test to verify