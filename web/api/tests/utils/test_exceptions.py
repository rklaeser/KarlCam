"""
Unit tests for custom exceptions
"""
import pytest
from fastapi import HTTPException

from utils.exceptions import (
    KarlCamException,
    CameraNotFoundException,
    DatabaseConnectionError,
    ImageNotFoundException,
    NoImagesFoundError,
    InvalidRequestError,
    DataProcessingError,
    CloudStorageError
)

class TestKarlCamException:
    """Test suite for base KarlCamException class"""
    
    @pytest.mark.unit
    def test_karlcam_exception_creation(self):
        """Test basic KarlCamException creation"""
        # Setup
        status_code = 400
        detail = "Test error message"
        error_code = "TEST_ERROR"
        
        # Execute
        exception = KarlCamException(
            status_code=status_code,
            detail=detail,
            error_code=error_code
        )
        
        # Assert
        assert exception.status_code == status_code
        assert exception.detail == detail
        assert exception.error_code == error_code
        assert exception.headers is None
    
    @pytest.mark.unit
    def test_karlcam_exception_with_headers(self):
        """Test KarlCamException with custom headers"""
        # Setup
        headers = {"X-Custom-Header": "test-value"}
        
        # Execute
        exception = KarlCamException(
            status_code=500,
            detail="Server error",
            error_code="SERVER_ERROR",
            headers=headers
        )
        
        # Assert
        assert exception.headers == headers
    
    @pytest.mark.unit
    def test_karlcam_exception_inherits_from_http_exception(self):
        """Test that KarlCamException inherits from FastAPI HTTPException"""
        # Execute
        exception = KarlCamException(400, "Test", "TEST_ERROR")
        
        # Assert
        assert isinstance(exception, HTTPException)
        assert hasattr(exception, 'error_code')

class TestCameraNotFoundException:
    """Test suite for CameraNotFoundException"""
    
    @pytest.mark.unit
    def test_camera_not_found_exception_creation(self):
        """Test CameraNotFoundException creation"""
        # Setup
        camera_id = "test-camera-123"
        
        # Execute
        exception = CameraNotFoundException(camera_id)
        
        # Assert
        assert exception.status_code == 404
        assert camera_id in exception.detail
        assert exception.error_code == "CAMERA_NOT_FOUND"
        assert "Camera with id test-camera-123 not found" == exception.detail
    
    @pytest.mark.unit
    def test_camera_not_found_different_ids(self):
        """Test CameraNotFoundException with different camera IDs"""
        # Setup
        camera_ids = ["cam-1", "golden-gate-north", "test_camera_with_underscores"]
        
        for camera_id in camera_ids:
            # Execute
            exception = CameraNotFoundException(camera_id)
            
            # Assert
            assert camera_id in exception.detail
            assert exception.status_code == 404
            assert exception.error_code == "CAMERA_NOT_FOUND"

class TestDatabaseConnectionError:
    """Test suite for DatabaseConnectionError"""
    
    @pytest.mark.unit
    def test_database_connection_error_default(self):
        """Test DatabaseConnectionError with default message"""
        # Execute
        exception = DatabaseConnectionError()
        
        # Assert
        assert exception.status_code == 503
        assert exception.detail == "Unable to connect to database"
        assert exception.error_code == "DATABASE_CONNECTION_ERROR"
    
    @pytest.mark.unit
    def test_database_connection_error_custom_detail(self):
        """Test DatabaseConnectionError with custom detail"""
        # Setup
        custom_detail = "Database timeout after 30 seconds"
        
        # Execute
        exception = DatabaseConnectionError(custom_detail)
        
        # Assert
        assert exception.status_code == 503
        assert exception.detail == custom_detail
        assert exception.error_code == "DATABASE_CONNECTION_ERROR"

class TestImageNotFoundException:
    """Test suite for ImageNotFoundException"""
    
    @pytest.mark.unit
    def test_image_not_found_exception_creation(self):
        """Test ImageNotFoundException creation"""
        # Setup
        image_id = "test-image-456"
        
        # Execute
        exception = ImageNotFoundException(image_id)
        
        # Assert
        assert exception.status_code == 404
        assert image_id in exception.detail
        assert exception.error_code == "IMAGE_NOT_FOUND"
        assert f"Image {image_id} not found" == exception.detail
    
    @pytest.mark.unit
    def test_image_not_found_different_formats(self):
        """Test ImageNotFoundException with different image ID formats"""
        # Setup
        image_ids = ["123", "image.jpg", "camera1_20240110_083000.jpg"]
        
        for image_id in image_ids:
            # Execute
            exception = ImageNotFoundException(image_id)
            
            # Assert
            assert image_id in exception.detail
            assert exception.status_code == 404

class TestNoImagesFoundError:
    """Test suite for NoImagesFoundError"""
    
    @pytest.mark.unit
    def test_no_images_found_error_creation(self):
        """Test NoImagesFoundError creation"""
        # Setup
        camera_id = "empty-camera-789"
        
        # Execute
        exception = NoImagesFoundError(camera_id)
        
        # Assert
        assert exception.status_code == 404
        assert camera_id in exception.detail
        assert exception.error_code == "NO_IMAGES_FOUND"
        assert f"No collected images found for camera {camera_id}" == exception.detail
    
    @pytest.mark.unit
    def test_no_images_found_vs_camera_not_found(self):
        """Test distinction between NoImagesFoundError and CameraNotFoundException"""
        # Setup
        camera_id = "test-camera"
        
        # Execute
        no_images_error = NoImagesFoundError(camera_id)
        camera_not_found_error = CameraNotFoundException(camera_id)
        
        # Assert
        assert no_images_error.error_code != camera_not_found_error.error_code
        assert "No collected images" in no_images_error.detail
        assert "Camera with id" in camera_not_found_error.detail

class TestInvalidRequestError:
    """Test suite for InvalidRequestError"""
    
    @pytest.mark.unit
    def test_invalid_request_error_creation(self):
        """Test InvalidRequestError creation"""
        # Setup
        detail = "Invalid parameter value: hours must be positive"
        
        # Execute
        exception = InvalidRequestError(detail)
        
        # Assert
        assert exception.status_code == 400
        assert exception.detail == detail
        assert exception.error_code == "INVALID_REQUEST"
    
    @pytest.mark.unit
    def test_invalid_request_different_messages(self):
        """Test InvalidRequestError with different validation messages"""
        # Setup
        error_messages = [
            "Missing required parameter: camera_id",
            "Invalid date format: expected YYYY-MM-DD",
            "Parameter out of range: hours must be between 1 and 168"
        ]
        
        for message in error_messages:
            # Execute
            exception = InvalidRequestError(message)
            
            # Assert
            assert exception.status_code == 400
            assert exception.detail == message
            assert exception.error_code == "INVALID_REQUEST"

class TestDataProcessingError:
    """Test suite for DataProcessingError"""
    
    @pytest.mark.unit
    def test_data_processing_error_default(self):
        """Test DataProcessingError with default message"""
        # Execute
        exception = DataProcessingError()
        
        # Assert
        assert exception.status_code == 500
        assert exception.detail == "Failed to process data"
        assert exception.error_code == "PROCESSING_ERROR"
    
    @pytest.mark.unit
    def test_data_processing_error_custom_detail(self):
        """Test DataProcessingError with custom detail"""
        # Setup
        custom_detail = "Failed to parse image labels from ML service"
        
        # Execute
        exception = DataProcessingError(custom_detail)
        
        # Assert
        assert exception.status_code == 500
        assert exception.detail == custom_detail
        assert exception.error_code == "PROCESSING_ERROR"

class TestCloudStorageError:
    """Test suite for CloudStorageError"""
    
    @pytest.mark.unit
    def test_cloud_storage_error_default(self):
        """Test CloudStorageError with default message"""
        # Execute
        exception = CloudStorageError()
        
        # Assert
        assert exception.status_code == 502
        assert exception.detail == "Cloud Storage operation failed"
        assert exception.error_code == "CLOUD_STORAGE_ERROR"
    
    @pytest.mark.unit
    def test_cloud_storage_error_custom_detail(self):
        """Test CloudStorageError with custom detail"""
        # Setup
        custom_detail = "Failed to upload image to gs://karlcam-bucket/images/"
        
        # Execute
        exception = CloudStorageError(custom_detail)
        
        # Assert
        assert exception.status_code == 502
        assert exception.detail == custom_detail
        assert exception.error_code == "CLOUD_STORAGE_ERROR"

class TestExceptionHierarchy:
    """Test suite for exception hierarchy and integration"""
    
    @pytest.mark.unit
    def test_all_exceptions_inherit_from_karlcam_exception(self):
        """Test that all custom exceptions inherit from KarlCamException"""
        # Setup
        exception_classes = [
            CameraNotFoundException,
            DatabaseConnectionError,
            ImageNotFoundException,
            NoImagesFoundError,
            InvalidRequestError,
            DataProcessingError,
            CloudStorageError
        ]
        
        for exception_class in exception_classes:
            # Execute - Create instance with minimal parameters
            if exception_class in [CameraNotFoundException, ImageNotFoundException, NoImagesFoundError]:
                exception = exception_class("test-id")
            else:
                exception = exception_class()
            
            # Assert
            assert isinstance(exception, KarlCamException)
            assert isinstance(exception, HTTPException)
            assert hasattr(exception, 'error_code')
    
    @pytest.mark.unit
    def test_exception_status_codes_are_appropriate(self):
        """Test that exception status codes follow HTTP standards"""
        # Setup & Execute
        exceptions_and_expected_codes = [
            (CameraNotFoundException("test"), 404),
            (DatabaseConnectionError(), 503),
            (ImageNotFoundException("test"), 404),
            (NoImagesFoundError("test"), 404),
            (InvalidRequestError("test"), 400),
            (DataProcessingError(), 500),
            (CloudStorageError(), 502)
        ]
        
        for exception, expected_code in exceptions_and_expected_codes:
            # Assert
            assert exception.status_code == expected_code, f"{exception.__class__.__name__} should have status code {expected_code}"
    
    @pytest.mark.unit
    def test_exception_error_codes_are_unique(self):
        """Test that each exception has a unique error code"""
        # Setup & Execute
        exceptions = [
            CameraNotFoundException("test"),
            DatabaseConnectionError(),
            ImageNotFoundException("test"),
            NoImagesFoundError("test"),
            InvalidRequestError("test"),
            DataProcessingError(),
            CloudStorageError()
        ]
        
        error_codes = [exc.error_code for exc in exceptions]
        
        # Assert
        assert len(error_codes) == len(set(error_codes)), "Error codes should be unique"
    
    @pytest.mark.unit
    def test_exceptions_can_be_caught_as_http_exception(self):
        """Test that custom exceptions can be caught as HTTPException"""
        # Setup
        custom_exception = CameraNotFoundException("test-camera")
        
        # Execute & Assert
        try:
            raise custom_exception
        except HTTPException as e:
            assert e.status_code == 404
            assert "test-camera" in e.detail
        except Exception:
            pytest.fail("Should be catchable as HTTPException")
    
    @pytest.mark.unit
    def test_exceptions_preserve_original_attributes(self):
        """Test that custom exceptions preserve all HTTPException attributes"""
        # Setup
        exception = DataProcessingError("Custom processing error")
        
        # Assert
        assert hasattr(exception, 'status_code')
        assert hasattr(exception, 'detail')
        assert hasattr(exception, 'headers')
        assert hasattr(exception, 'error_code')  # Custom attribute
        
        # Verify values
        assert exception.status_code == 500
        assert exception.detail == "Custom processing error"
        assert exception.error_code == "PROCESSING_ERROR"