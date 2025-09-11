"""
Integration tests for API workflows
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from tests.factories import (
    CameraConditionsFactory,
    WebcamFactory,
    create_webcam_with_recent_images,
    create_multi_camera_scenario
)

class TestCameraDataWorkflow:
    """Test complete camera data retrieval workflows"""
    
    @pytest.mark.integration
    def test_complete_camera_list_to_detail_workflow(self, test_client, mock_db_manager):
        """Test complete workflow from camera list to individual camera details"""
        # Setup - Create multiple cameras
        cameras, images_by_camera = create_multi_camera_scenario(num_cameras=3)
        mock_db_manager.get_active_webcams.return_value = cameras
        
        # Flatten images for recent_images mock
        all_images = []
        for images in images_by_camera.values():
            all_images.extend(images)
        mock_db_manager.get_recent_images.return_value = all_images
        
        # Step 1: Get camera list
        list_response = test_client.get("/api/public/cameras")
        assert list_response.status_code == 200
        list_data = list_response.json()
        
        assert list_data["count"] == 3
        assert len(list_data["cameras"]) == 3
        
        # Step 2: Get details for first camera
        first_camera = list_data["cameras"][0]
        camera_id = first_camera["id"]
        
        # Mock camera history for detail endpoint
        history_data = [
            {
                "fog_score": 65,
                "fog_level": "Moderate Fog",
                "confidence": 0.89,
                "timestamp": datetime.now().isoformat() + "Z",
                "reasoning": "Moderate fog visible"
            }
        ]
        mock_db_manager.get_recent_images.return_value = history_data
        
        detail_response = test_client.get(f"/api/public/cameras/{camera_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        
        # Verify consistency between list and detail
        assert detail_data["camera"]["id"] == camera_id
        assert detail_data["camera"]["name"] == first_camera["name"]
        assert "history" in detail_data
        assert "history_hours" in detail_data
    
    @pytest.mark.integration
    def test_camera_with_latest_image_workflow(self, test_client, mock_db_manager):
        """Test workflow for getting camera with latest image"""
        # Setup
        camera_id = "test-camera-1"
        webcam = WebcamFactory(id=camera_id)
        mock_db_manager.get_active_webcams.return_value = [webcam]
        
        # Mock recent images for camera list
        mock_images = [
            {
                'webcam_id': camera_id,
                'timestamp': datetime.now(),
                'labels': [{
                    'fog_score': 75,
                    'fog_level': 'Heavy Fog',
                    'confidence': 0.92
                }]
            }
        ]
        mock_db_manager.get_recent_images.return_value = mock_images
        
        # Step 1: Verify camera appears in list
        list_response = test_client.get("/api/public/cameras")
        assert list_response.status_code == 200
        list_data = list_response.json()
        
        camera_found = False
        for camera in list_data["cameras"]:
            if camera["id"] == camera_id:
                camera_found = True
                assert camera["fog_score"] == 75
                break
        assert camera_found
        
        # Step 2: Get latest image for the camera
        mock_db_manager.get_recent_images.return_value = [
            {
                'timestamp': datetime.now(),
                'image_filename': 'test_image.jpg',
                'cloud_storage_path': 'gs://bucket/test_image.jpg'
            }
        ]
        
        image_response = test_client.get(f"/api/public/cameras/{camera_id}/latest-image")
        assert image_response.status_code == 200
        image_data = image_response.json()
        
        assert image_data["camera_id"] == camera_id
        assert "image_url" in image_data
        assert "timestamp" in image_data
        assert "age_hours" in image_data
    
    @pytest.mark.integration
    def test_historical_data_workflow(self, test_client, mock_db_manager):
        """Test workflow for retrieving historical camera data"""
        # Setup
        camera_id = "historical-camera"
        webcam = WebcamFactory(id=camera_id)
        mock_db_manager.get_active_webcams.return_value = [webcam]
        
        # Mock for camera list (need recent data)
        recent_image = {
            'webcam_id': camera_id,
            'timestamp': datetime.now(),
            'labels': [{'fog_score': 30, 'fog_level': 'Light Fog', 'confidence': 0.85}]
        }
        mock_db_manager.get_recent_images.return_value = [recent_image]
        
        # Step 1: Verify camera exists
        list_response = test_client.get("/api/public/cameras")
        assert list_response.status_code == 200
        
        # Step 2: Get historical data with default period
        historical_data = []
        for i in range(5):
            timestamp = datetime.now() - timedelta(hours=i*4)
            historical_data.append({
                'timestamp': timestamp.isoformat() + 'Z',
                'labels': [{
                    'fog_score': 40 + i*10,
                    'fog_level': 'Moderate Fog',
                    'confidence': 0.8 + i*0.02
                }]
            })
        
        mock_db_manager.get_recent_images.return_value = historical_data
        
        history_response = test_client.get(f"/api/public/cameras/{camera_id}")
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        assert "history" in history_data
        assert history_data["history_hours"] == 24  # Default
        assert len(history_data["history"]) == 5
        
        # Step 3: Get extended historical data
        extended_response = test_client.get(f"/api/public/cameras/{camera_id}?hours=48")
        assert extended_response.status_code == 200
        extended_data = extended_response.json()
        
        assert extended_data["history_hours"] == 48

class TestWebcamWorkflow:
    """Test webcam-related workflows"""
    
    @pytest.mark.integration
    def test_webcam_list_workflow(self, test_client, mock_db_manager):
        """Test webcam list retrieval workflow"""
        # Setup
        webcams = [WebcamFactory() for _ in range(4)]
        mock_db_manager.get_active_webcams.return_value = webcams
        
        # Execute
        response = test_client.get("/api/public/webcams")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 4
        assert len(data["webcams"]) == 4
        
        # Verify webcam structure
        for webcam in data["webcams"]:
            required_fields = {'id', 'name', 'lat', 'lon', 'url', 'video_url', 'description', 'active'}
            assert set(webcam.keys()) == required_fields

class TestSystemStatusWorkflow:
    """Test system status and statistics workflows"""
    
    @pytest.mark.integration
    def test_system_monitoring_workflow(self, test_client):
        """Test complete system monitoring workflow"""
        # Step 1: Check basic health
        health_response = test_client.get("/api/public/")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        
        # Step 2: Check comprehensive health with DB
        with patch('routers.health.get_db_connection'):
            detailed_health_response = test_client.get("/api/public/health")
            assert detailed_health_response.status_code == 200
            detailed_health_data = detailed_health_response.json()
            assert detailed_health_data["status"] == "healthy"
        
        # Step 3: Get system statistics
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_overall_stats.return_value = {
                'total_assessments': 1440,
                'active_cameras': 12,
                'avg_fog_score': 32.5,
                'avg_confidence': 0.89,
                'foggy_conditions': 425,
                'last_update': '2024-01-10T08:30:00Z',
                'period': '24 hours'
            }
            
            stats_response = test_client.get("/api/public/stats")
            assert stats_response.status_code == 200
            stats_data = stats_response.json()
            assert stats_data["total_assessments"] == 1440
            assert stats_data["active_cameras"] == 12
        
        # Step 4: Check system status
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_system_status.return_value = {
                'karlcam_mode': 0,
                'description': 'Normal operation',
                'updated_at': '2024-01-10T08:30:00Z',
                'updated_by': 'system'
            }
            
            status_response = test_client.get("/api/public/system/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["karlcam_mode"] == 0
    
    @pytest.mark.integration
    def test_system_status_update_workflow(self, test_client):
        """Test system status update workflow"""
        # Step 1: Get current status
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_system_status.return_value = {
                'karlcam_mode': 0,
                'description': 'Normal operation',
                'updated_at': '2024-01-10T08:30:00Z',
                'updated_by': 'system'
            }
            
            get_response = test_client.get("/api/public/system/status")
            assert get_response.status_code == 200
            current_status = get_response.json()
            assert current_status["karlcam_mode"] == 0
        
        # Step 2: Update status
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.set_system_status.return_value = {
                'success': True,
                'karlcam_mode': 1,
                'updated_by': 'admin',
                'timestamp': '2024-01-10T09:00:00Z'
            }
            
            update_data = {
                'karlcam_mode': 1,
                'updated_by': 'admin'
            }
            
            update_response = test_client.post("/api/public/system/status", json=update_data)
            assert update_response.status_code == 200
            update_result = update_response.json()
            assert update_result["success"] is True
            assert update_result["karlcam_mode"] == 1
        
        # Step 3: Verify status was updated
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_system_status.return_value = {
                'karlcam_mode': 1,
                'description': 'Night mode - collection paused',
                'updated_at': '2024-01-10T09:00:00Z',
                'updated_by': 'admin'
            }
            
            verify_response = test_client.get("/api/public/system/status")
            assert verify_response.status_code == 200
            new_status = verify_response.json()
            assert new_status["karlcam_mode"] == 1
            assert new_status["updated_by"] == "admin"

class TestConfigurationWorkflow:
    """Test configuration access workflows"""
    
    @pytest.mark.integration
    def test_public_configuration_workflow(self, test_client):
        """Test public configuration retrieval workflow"""
        # Execute
        response = test_client.get("/api/public/config/public")
        
        # Assert
        assert response.status_code == 200
        config_data = response.json()
        
        # Verify configuration structure
        required_fields = {
            'app_name', 'version', 'environment', 'fog_detection_threshold',
            'foggy_conditions_threshold', 'default_location', 'default_history_hours',
            'stats_period_hours', 'api_prefix'
        }
        assert set(config_data.keys()) == required_fields
        
        # Verify default location structure
        location = config_data['default_location']
        assert 'name' in location
        assert 'latitude' in location
        assert 'longitude' in location
        
        # Verify no sensitive data
        sensitive_fields = {'database_url', 'bucket_name', 'project_id'}
        for field in sensitive_fields:
            assert field not in config_data

class TestErrorHandlingWorkflows:
    """Test error handling across workflows"""
    
    @pytest.mark.integration
    def test_camera_not_found_workflow(self, test_client, mock_db_manager):
        """Test camera not found error workflow"""
        # Setup - No cameras in database
        mock_db_manager.get_active_webcams.return_value = []
        mock_db_manager.get_recent_images.return_value = []
        
        # Step 1: Verify camera doesn't exist in list
        list_response = test_client.get("/api/public/cameras")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["count"] == 0
        
        # Step 2: Try to get details for non-existent camera
        detail_response = test_client.get("/api/public/cameras/nonexistent-camera")
        assert detail_response.status_code == 404
        detail_data = detail_response.json()
        assert "nonexistent-camera" in detail_data["detail"]
        
        # Step 3: Try to get latest image for non-existent camera
        image_response = test_client.get("/api/public/cameras/nonexistent-camera/latest-image")
        assert image_response.status_code == 404
        image_data = image_response.json()
        assert image_data["error_code"] == "NO_IMAGES_FOUND"
    
    @pytest.mark.integration
    def test_validation_error_workflow(self, test_client, mock_db_manager):
        """Test validation error workflow"""
        # Setup
        camera_id = "test-camera"
        webcam = WebcamFactory(id=camera_id)
        mock_db_manager.get_active_webcams.return_value = [webcam]
        mock_db_manager.get_recent_images.return_value = []
        
        # Test invalid hours parameter
        invalid_hours_response = test_client.get(f"/api/public/cameras/{camera_id}?hours=-5")
        assert invalid_hours_response.status_code == 422
        error_data = invalid_hours_response.json()
        assert error_data["error_code"] == "VALIDATION_ERROR"
        
        # Test hours over maximum
        over_max_response = test_client.get(f"/api/public/cameras/{camera_id}?hours=200")
        assert over_max_response.status_code == 422
        error_data = over_max_response.json()
        assert error_data["error_code"] == "VALIDATION_ERROR"
    
    @pytest.mark.integration
    def test_service_error_workflow(self, test_client, mock_db_manager):
        """Test service error handling workflow"""
        # Step 1: Test database error in camera list
        mock_db_manager.get_recent_images.side_effect = Exception("Database connection failed")
        
        list_response = test_client.get("/api/public/cameras")
        assert list_response.status_code == 500
        list_data = list_response.json()
        assert list_data["error_code"] == "INTERNAL_ERROR"
        
        # Step 2: Test stats service error
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_overall_stats.side_effect = Exception("Stats calculation failed")
            
            stats_response = test_client.get("/api/public/stats")
            assert stats_response.status_code == 500
            stats_data = stats_response.json()
            assert stats_data["error_code"] == "INTERNAL_ERROR"

class TestImageServingWorkflow:
    """Test image serving workflows"""
    
    @pytest.mark.integration
    def test_image_serving_workflow(self, test_client):
        """Test complete image serving workflow"""
        # Setup
        filename = "test-camera_2024-01-10T08-30-00Z.jpg"
        expected_url = f"https://storage.googleapis.com/karlcam-fog-data/raw_images/{filename}"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = expected_url
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
            
            # Assert
            assert response.status_code == 302
            assert response.headers['location'] == expected_url
            assert response.headers['cache-control'] == "public, max-age=3600"

class TestEndToEndScenarios:
    """Test complete end-to-end scenarios"""
    
    @pytest.mark.integration
    def test_typical_client_usage_scenario(self, test_client, mock_db_manager):
        """Test typical client application usage scenario"""
        # Scenario: A web client loading the KarlCam dashboard
        
        # Step 1: Client gets public configuration
        config_response = test_client.get("/api/public/config/public")
        assert config_response.status_code == 200
        config = config_response.json()
        fog_threshold = config["fog_detection_threshold"]
        
        # Step 2: Client gets list of all cameras
        cameras, images_by_camera = create_multi_camera_scenario(num_cameras=5)
        mock_db_manager.get_active_webcams.return_value = cameras
        
        all_images = []
        for images in images_by_camera.values():
            all_images.extend(images)
        mock_db_manager.get_recent_images.return_value = all_images
        
        cameras_response = test_client.get("/api/public/cameras")
        assert cameras_response.status_code == 200
        cameras_data = cameras_response.json()
        assert cameras_data["count"] == 5
        
        # Step 3: Client gets system statistics for dashboard
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_overall_stats.return_value = {
                'total_assessments': 2880,
                'active_cameras': 5,
                'avg_fog_score': 45.2,
                'avg_confidence': 0.87,
                'foggy_conditions': 850,
                'last_update': '2024-01-10T08:30:00Z',
                'period': '24 hours'
            }
            
            stats_response = test_client.get("/api/public/stats")
            assert stats_response.status_code == 200
            stats_data = stats_response.json()
            
            # Verify stats make sense given the configuration
            foggy_cameras = [c for c in cameras_data["cameras"] if c["fog_score"] > fog_threshold]
            assert stats_data["active_cameras"] == 5
        
        # Step 4: Client gets detailed view of a high-fog camera
        high_fog_camera = max(cameras_data["cameras"], key=lambda c: c["fog_score"])
        camera_id = high_fog_camera["id"]
        
        # Mock historical data for this camera
        mock_db_manager.get_recent_images.return_value = [
            {
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat() + 'Z',
                'labels': [{
                    'fog_score': 70 - i*5,
                    'fog_level': 'Heavy Fog' if (70 - i*5) > 60 else 'Moderate Fog',
                    'confidence': 0.9 - i*0.01
                }]
            } for i in range(6)
        ]
        
        detail_response = test_client.get(f"/api/public/cameras/{camera_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert len(detail_data["history"]) == 6
        
        # Step 5: Client gets latest image for display
        mock_db_manager.get_recent_images.return_value = [
            {
                'timestamp': datetime.now(),
                'image_filename': f'{camera_id}_latest.jpg',
                'cloud_storage_path': f'gs://bucket/{camera_id}_latest.jpg'
            }
        ]
        
        image_response = test_client.get(f"/api/public/cameras/{camera_id}/latest-image")
        assert image_response.status_code == 200
        image_data = image_response.json()
        assert "image_url" in image_data
        assert image_data["camera_id"] == camera_id