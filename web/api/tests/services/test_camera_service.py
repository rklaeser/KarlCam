"""
Unit tests for CameraService
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from services.camera_service import CameraService
from utils.exceptions import CameraNotFoundException, NoImagesFoundError, DataProcessingError
from tests.factories import (
    WebcamFactory, 
    ImageWithLabelsFactory, 
    CameraConditionsFactory,
    create_webcam_with_recent_images,
    create_multi_camera_scenario
)

class TestCameraService:
    """Test suite for CameraService"""
    
    @pytest.fixture
    def camera_service(self, mock_db_manager):
        """Create CameraService instance with mocked DB manager"""
        return CameraService(mock_db_manager)
    
    @pytest.mark.unit
    def test_get_latest_camera_data_empty_database(self, camera_service, mock_db_manager):
        """Test getting camera data when database is empty"""
        # Setup
        mock_db_manager.get_recent_images.return_value = []
        mock_db_manager.get_active_webcams.return_value = []
        
        # Execute
        result = camera_service.get_latest_camera_data()
        
        # Assert
        assert result == []
        mock_db_manager.get_recent_images.assert_called_once_with(days=1)
        mock_db_manager.get_active_webcams.assert_called_once()
    
    @pytest.mark.unit
    def test_get_latest_camera_data_no_labels(self, camera_service, mock_db_manager):
        """Test getting camera data when images have no labels"""
        # Setup
        webcam = WebcamFactory()
        mock_db_manager.get_active_webcams.return_value = [webcam]
        mock_db_manager.get_recent_images.return_value = [
            {
                'webcam_id': webcam.id,
                'timestamp': datetime.now(),
                'labels': []  # No labels
            }
        ]
        
        # Execute
        result = camera_service.get_latest_camera_data()
        
        # Assert
        assert result == []  # No cameras returned when no labels exist
    
    @pytest.mark.unit
    def test_get_latest_camera_data_with_fog_detected(self, camera_service, mock_db_manager):
        """Test getting camera data with fog detected"""
        # Setup
        webcam = WebcamFactory(id="test-cam-1", name="Test Camera")
        mock_db_manager.get_active_webcams.return_value = [webcam]
        
        fog_score = 75  # Above threshold (20)
        mock_db_manager.get_recent_images.return_value = [
            {
                'webcam_id': webcam.id,
                'timestamp': datetime.now(),
                'labels': [{
                    'fog_score': fog_score,
                    'fog_level': 'Heavy Fog',
                    'confidence': 0.92
                }]
            }
        ]
        
        # Execute
        result = camera_service.get_latest_camera_data()
        
        # Assert
        assert len(result) == 1
        camera_data = result[0]
        assert camera_data['id'] == webcam.id
        assert camera_data['name'] == webcam.name
        assert camera_data['fog_score'] == fog_score
        assert camera_data['fog_level'] == 'Heavy Fog'
        assert camera_data['weather_detected'] is True
        assert camera_data['confidence'] == 92.0  # Converted to percentage
    
    @pytest.mark.unit
    def test_get_latest_camera_data_no_fog_detected(self, camera_service, mock_db_manager):
        """Test getting camera data with no fog detected"""
        # Setup
        webcam = WebcamFactory()
        mock_db_manager.get_active_webcams.return_value = [webcam]
        
        fog_score = 10  # Below threshold (20)
        mock_db_manager.get_recent_images.return_value = [
            {
                'webcam_id': webcam.id,
                'timestamp': datetime.now(),
                'labels': [{
                    'fog_score': fog_score,
                    'fog_level': 'Clear',
                    'confidence': 0.95
                }]
            }
        ]
        
        # Execute
        result = camera_service.get_latest_camera_data()
        
        # Assert
        assert len(result) == 1
        camera_data = result[0]
        assert camera_data['weather_detected'] is False
        assert camera_data['fog_score'] == fog_score
    
    @pytest.mark.unit
    def test_get_latest_camera_data_multiple_cameras(self, camera_service, mock_db_manager):
        """Test getting data for multiple cameras"""
        # Setup
        cameras, images_by_camera = create_multi_camera_scenario(num_cameras=3)
        mock_db_manager.get_active_webcams.return_value = cameras
        
        # Flatten images for recent_images mock
        all_images = []
        for images in images_by_camera.values():
            all_images.extend(images)
        mock_db_manager.get_recent_images.return_value = all_images
        
        # Execute
        result = camera_service.get_latest_camera_data()
        
        # Assert
        assert len(result) == 3
        returned_ids = {camera['id'] for camera in result}
        expected_ids = {camera.id for camera in cameras}
        assert returned_ids == expected_ids
    
    @pytest.mark.unit
    def test_get_latest_camera_data_with_default_coordinates(self, camera_service, mock_db_manager):
        """Test default coordinates are used when webcam has none"""
        # Setup
        webcam = WebcamFactory(latitude=None, longitude=None)
        mock_db_manager.get_active_webcams.return_value = [webcam]
        mock_db_manager.get_recent_images.return_value = [
            ImageWithLabelsFactory(webcam_id=webcam.id)
        ]
        
        # Execute
        result = camera_service.get_latest_camera_data()
        
        # Assert
        assert len(result) == 1
        camera_data = result[0]
        assert camera_data['lat'] == 37.7749  # Default SF latitude
        assert camera_data['lon'] == -122.4194  # Default SF longitude
    
    @pytest.mark.unit
    def test_get_latest_camera_data_handles_missing_confidence(self, camera_service, mock_db_manager):
        """Test handling of missing confidence values"""
        # Setup
        webcam = WebcamFactory()
        mock_db_manager.get_active_webcams.return_value = [webcam]
        mock_db_manager.get_recent_images.return_value = [
            {
                'webcam_id': webcam.id,
                'timestamp': datetime.now(),
                'labels': [{
                    'fog_score': 50,
                    'fog_level': 'Moderate Fog',
                    'confidence': None  # Missing confidence
                }]
            }
        ]
        
        # Execute
        result = camera_service.get_latest_camera_data()
        
        # Assert
        assert len(result) == 1
        camera_data = result[0]
        assert camera_data['confidence'] == 0.0
        assert camera_data['weather_confidence'] == 0.0
    
    @pytest.mark.unit
    def test_get_latest_camera_data_database_error(self, camera_service, mock_db_manager):
        """Test error handling when database fails"""
        # Setup
        mock_db_manager.get_recent_images.side_effect = Exception("Database connection failed")
        
        # Execute & Assert
        with pytest.raises(DataProcessingError) as exc_info:
            camera_service.get_latest_camera_data()
        
        assert "Failed to fetch camera data" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_webcam_list_success(self, camera_service, mock_db_manager):
        """Test successful webcam list retrieval"""
        # Setup
        webcams = [WebcamFactory() for _ in range(3)]
        mock_db_manager.get_active_webcams.return_value = webcams
        
        # Execute
        result = camera_service.get_webcam_list()
        
        # Assert
        assert len(result) == 3
        for i, webcam_data in enumerate(result):
            assert webcam_data['id'] == webcams[i].id
            assert webcam_data['name'] == webcams[i].name
            assert webcam_data['lat'] == webcams[i].latitude
            assert webcam_data['lon'] == webcams[i].longitude
            assert webcam_data['url'] == webcams[i].url
            assert webcam_data['active'] == webcams[i].active
    
    @pytest.mark.unit
    def test_get_webcam_list_database_error(self, camera_service, mock_db_manager):
        """Test error handling in webcam list retrieval"""
        # Setup
        mock_db_manager.get_active_webcams.side_effect = Exception("Database error")
        
        # Execute & Assert
        with pytest.raises(DataProcessingError) as exc_info:
            camera_service.get_webcam_list()
        
        assert "Failed to fetch webcam list" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_camera_history_success(self, camera_service, mock_db_manager):
        """Test successful camera history retrieval"""
        # Setup
        camera_id = "test-camera-1"
        hours = 48
        
        # Create test images with timestamps
        images = []
        for i in range(5):
            timestamp = datetime.now() - timedelta(hours=i*2)
            images.append({
                'timestamp': timestamp,
                'labels': [{
                    'fog_score': 30 + i*10,
                    'fog_level': 'Moderate Fog',
                    'confidence': 0.8 + i*0.02
                }]
            })
        
        mock_db_manager.get_recent_images.return_value = images
        
        # Execute
        result = camera_service.get_camera_history(camera_id, hours)
        
        # Assert
        assert len(result) == 5
        mock_db_manager.get_recent_images.assert_called_once_with(
            webcam_id=camera_id, 
            days=2.0  # 48 hours = 2 days
        )
        
        # Check sorting (should be newest first)
        timestamps = [item['timestamp'] for item in result]
        assert timestamps == sorted(timestamps, reverse=True)
    
    @pytest.mark.unit
    def test_get_camera_history_default_hours(self, camera_service, mock_db_manager):
        """Test camera history with default hours parameter"""
        # Setup
        camera_id = "test-camera-1"
        mock_db_manager.get_recent_images.return_value = []
        
        # Execute
        result = camera_service.get_camera_history(camera_id)
        
        # Assert
        mock_db_manager.get_recent_images.assert_called_once_with(
            webcam_id=camera_id,
            days=1.0  # Default 24 hours = 1 day
        )
    
    @pytest.mark.unit
    def test_get_camera_history_minimum_days(self, camera_service, mock_db_manager):
        """Test camera history respects minimum 1 day limit"""
        # Setup
        camera_id = "test-camera-1"
        hours = 12  # Less than 24 hours
        mock_db_manager.get_recent_images.return_value = []
        
        # Execute
        result = camera_service.get_camera_history(camera_id, hours)
        
        # Assert
        mock_db_manager.get_recent_images.assert_called_once_with(
            webcam_id=camera_id,
            days=1  # Minimum 1 day enforced
        )
    
    @pytest.mark.unit
    def test_get_latest_image_info_success(self, camera_service, mock_db_manager):
        """Test successful latest image info retrieval"""
        # Setup
        camera_id = "test-camera-1"
        timestamp = datetime.now()
        mock_db_manager.get_recent_images.return_value = [
            {
                'timestamp': timestamp,
                'image_filename': 'test_image.jpg',
                'cloud_storage_path': 'gs://bucket/test_image.jpg'
            }
        ]
        
        # Execute
        result = camera_service.get_latest_image_info(camera_id)
        
        # Assert
        assert result['camera_id'] == camera_id
        assert result['image_url'] == 'https://storage.googleapis.com/bucket/test_image.jpg'
        assert result['filename'] == 'test_image.jpg'
        assert result['timestamp'] == timestamp.isoformat()
        assert 'age_hours' in result
    
    @pytest.mark.unit
    def test_get_latest_image_info_no_images(self, camera_service, mock_db_manager):
        """Test latest image info when no images exist"""
        # Setup
        camera_id = "test-camera-1"
        mock_db_manager.get_recent_images.return_value = []
        
        # Execute & Assert
        with pytest.raises(NoImagesFoundError):
            camera_service.get_latest_image_info(camera_id)
    
    @pytest.mark.unit
    def test_get_latest_image_info_non_gcs_path(self, camera_service, mock_db_manager):
        """Test image info with non-GCS storage path"""
        # Setup
        camera_id = "test-camera-1"
        direct_url = "https://example.com/image.jpg"
        mock_db_manager.get_recent_images.return_value = [
            {
                'timestamp': datetime.now(),
                'image_filename': 'test_image.jpg',
                'cloud_storage_path': direct_url
            }
        ]
        
        # Execute
        result = camera_service.get_latest_image_info(camera_id)
        
        # Assert
        assert result['image_url'] == direct_url  # Should use direct URL as-is