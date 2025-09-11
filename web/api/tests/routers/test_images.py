"""
Unit tests for Images Router endpoints
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

class TestImagesEndpoints:
    """Test suite for images router endpoints"""
    
    @pytest.mark.unit
    def test_serve_image_success(self, test_client):
        """Test successful image URL redirect"""
        # Setup
        filename = "golden-gate-north_2024-01-10T08-30-00Z.jpg"
        expected_url = f"https://storage.googleapis.com/karlcam-fog-data/raw_images/{filename}"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = expected_url
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
            
            # Assert
            assert response.status_code == 302  # Redirect
            assert response.headers['location'] == expected_url
            assert response.headers['cache-control'] == "public, max-age=3600"
            
            # Verify service was called with correct parameters
            mock_service.get_image_url.assert_called_once_with(filename)
    
    @pytest.mark.unit
    def test_serve_image_with_special_characters(self, test_client):
        """Test image serving with special characters in filename"""
        # Setup
        filename = "camera-1_2024-01-10T08:30:00Z.jpg"  # Colon in timestamp
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
    
    @pytest.mark.unit
    def test_serve_image_not_found(self, test_client):
        """Test image serving when image doesn't exist"""
        # Setup
        filename = "nonexistent-image.jpg"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.side_effect = HTTPException(
                status_code=404, 
                detail="Image file not found"
            )
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}")
            
            # Assert
            assert response.status_code == 404
            data = response.json()
            assert data["error_code"] == "IMAGE_NOT_FOUND"
    
    @pytest.mark.unit
    def test_serve_image_storage_error(self, test_client):
        """Test image serving when storage service fails"""
        # Setup
        filename = "test-image.jpg"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.side_effect = HTTPException(
                status_code=500,
                detail="Cloud Storage access failed"
            )
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}")
            
            # Assert
            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "STORAGE_ERROR"
    
    @pytest.mark.unit
    def test_serve_image_service_initialization(self, test_client):
        """Test that ImageService is properly initialized with dependencies"""
        # Setup
        filename = "test-image.jpg"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = "https://example.com/image.jpg"
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
            
            # Assert
            assert response.status_code == 302
            
            # Verify ImageService was instantiated with correct dependencies
            mock_service_class.assert_called_once()
            call_args = mock_service_class.call_args[0]
            assert len(call_args) == 2  # storage_client and bucket_name
    
    @pytest.mark.unit
    def test_serve_image_cache_headers(self, test_client):
        """Test that appropriate cache headers are set"""
        # Setup
        filename = "test-image.jpg"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = "https://example.com/image.jpg"
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
            
            # Assert
            assert response.status_code == 302
            
            # Verify cache headers
            cache_control = response.headers.get('cache-control')
            assert cache_control == "public, max-age=3600"
            
            # Verify it's a 1-hour cache (3600 seconds)
            assert "max-age=3600" in cache_control
            assert "public" in cache_control
    
    @pytest.mark.unit
    def test_serve_image_filename_validation(self, test_client):
        """Test filename parameter validation"""
        # Test valid filename patterns
        valid_filenames = [
            "camera-1_2024-01-10T08-30-00Z.jpg",
            "golden-gate-north_20240110_083000.jpg",
            "test_image.jpg",
            "cam123_image.jpeg"
        ]
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = "https://example.com/image.jpg"
            
            for filename in valid_filenames:
                response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
                assert response.status_code == 302, f"Failed for filename: {filename}"
    
    @pytest.mark.unit
    def test_serve_image_url_encoding(self, test_client):
        """Test that filenames with special characters are handled correctly"""
        # Setup - filename with URL-encoded characters
        filename = "camera%20test_2024-01-10T08%3A30%3A00Z.jpg"  # Encoded spaces and colons
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = "https://example.com/image.jpg"
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
            
            # Assert
            assert response.status_code == 302
            
            # Verify the service was called with the URL-encoded filename
            mock_service.get_image_url.assert_called_once_with(filename)
    
    @pytest.mark.unit
    def test_serve_image_multiple_redirects(self, test_client):
        """Test behavior when following redirects"""
        # Setup
        filename = "test-image.jpg"
        gcs_url = "https://storage.googleapis.com/karlcam-fog-data/raw_images/test-image.jpg"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = gcs_url
            
            # Execute without following redirects
            response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
            
            # Assert
            assert response.status_code == 302
            assert response.headers['location'] == gcs_url
            
            # The client should not attempt to follow the redirect to GCS
            # (which would fail in test environment)
    
    @pytest.mark.unit 
    def test_serve_image_different_file_extensions(self, test_client):
        """Test serving images with different file extensions"""
        # Setup
        filenames = [
            "test.jpg",
            "test.jpeg", 
            "test.png",
            "test.gif",
            "test.webp"
        ]
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = "https://example.com/image"
            
            for filename in filenames:
                # Execute
                response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
                
                # Assert
                assert response.status_code == 302, f"Failed for extension: {filename}"
                mock_service.get_image_url.assert_called_with(filename)
                
                # Reset mock for next iteration
                mock_service.get_image_url.reset_mock()
    
    @pytest.mark.unit
    def test_serve_image_response_type(self, test_client):
        """Test that response is a proper redirect response"""
        # Setup
        filename = "test-image.jpg"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = "https://example.com/image.jpg"
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
            
            # Assert
            assert response.status_code == 302
            assert 'location' in response.headers
            
            # Verify it's a proper HTTP redirect
            assert response.is_redirect
    
    @pytest.mark.unit
    def test_serve_image_performance_redirect(self, test_client):
        """Test that redirect approach is used for performance"""
        # This test verifies the architectural decision to redirect rather than proxy
        
        filename = "large-image.jpg"
        gcs_url = "https://storage.googleapis.com/karlcam-fog-data/raw_images/large-image.jpg"
        
        with patch('routers.images.ImageService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_image_url.return_value = gcs_url
            
            # Execute
            response = test_client.get(f"/api/public/images/{filename}", allow_redirects=False)
            
            # Assert - verify we get a redirect, not the actual image data
            assert response.status_code == 302
            assert response.headers['location'] == gcs_url
            
            # Important: The response should be small (just redirect headers)
            # not containing actual image data which would double bandwidth usage
            assert len(response.content) < 1000  # Redirect response should be tiny