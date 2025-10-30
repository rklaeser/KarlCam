"""
Unit tests for OpenAPI schema configuration
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from core.openapi import custom_openapi, setup_openapi

class TestCustomOpenAPI:
    """Test suite for custom OpenAPI schema generation"""
    
    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI application"""
        app = Mock(spec=FastAPI)
        app.title = "KarlCam Fog API"
        app.version = "2.0.0"
        app.description = "Test API Description"
        app.routes = []
        app.openapi_tags = []
        app.servers = []
        app.openapi_schema = None
        return app
    
    @pytest.mark.unit
    def test_custom_openapi_basic_schema_generation(self, mock_app):
        """Test basic OpenAPI schema generation"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {
                "openapi": "3.0.2",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {}
            }
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert schema is not None
            assert "info" in schema
            assert "components" in schema
            assert "externalDocs" in schema
            
            # Verify get_openapi was called with correct parameters
            mock_get_openapi.assert_called_once_with(
                title=mock_app.title,
                version=mock_app.version,
                description=mock_app.description,
                routes=mock_app.routes,
                tags=mock_app.openapi_tags,
                servers=mock_app.servers,
            )
    
    @pytest.mark.unit
    def test_custom_openapi_caches_schema(self, mock_app):
        """Test that OpenAPI schema is cached after first generation"""
        # Setup
        mock_app.openapi_schema = {"cached": "schema"}
        
        # Execute
        schema = custom_openapi(mock_app)
        
        # Assert
        assert schema == {"cached": "schema"}
    
    @pytest.mark.unit
    def test_custom_openapi_adds_logo_info(self, mock_app):
        """Test that custom logo information is added"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {
                "info": {"title": "Test API"},
                "paths": {}
            }
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "x-logo" in schema["info"]
            logo_info = schema["info"]["x-logo"]
            assert "url" in logo_info
            assert "altText" in logo_info
            assert "karlcam-logo.png" in logo_info["url"]
    
    @pytest.mark.unit
    def test_custom_openapi_adds_external_docs(self, mock_app):
        """Test that external documentation links are added"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "externalDocs" in schema
            external_docs = schema["externalDocs"]
            assert "description" in external_docs
            assert "url" in external_docs
            assert "docs.karlcam.com" in external_docs["url"]
    
    @pytest.mark.unit
    def test_custom_openapi_adds_security_schemes(self, mock_app):
        """Test that security schemes are properly added"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "components" in schema
            assert "securitySchemes" in schema["components"]
            
            security_schemes = schema["components"]["securitySchemes"]
            assert "ApiKeyAuth" in security_schemes
            assert "BearerAuth" in security_schemes
            
            # Validate ApiKeyAuth configuration
            api_key_auth = security_schemes["ApiKeyAuth"]
            assert api_key_auth["type"] == "apiKey"
            assert api_key_auth["in"] == "header"
            assert api_key_auth["name"] == "X-API-Key"
            
            # Validate BearerAuth configuration
            bearer_auth = security_schemes["BearerAuth"]
            assert bearer_auth["type"] == "http"
            assert bearer_auth["scheme"] == "bearer"
            assert bearer_auth["bearerFormat"] == "JWT"
    
    @pytest.mark.unit
    def test_custom_openapi_adds_common_responses(self, mock_app):
        """Test that common response schemas are added"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "responses" in schema["components"]
            
            responses = schema["components"]["responses"]
            expected_responses = ["NotFound", "ValidationError", "InternalError", "ServiceUnavailable"]
            
            for response_name in expected_responses:
                assert response_name in responses
                assert "description" in responses[response_name]
                assert "content" in responses[response_name]
                assert "application/json" in responses[response_name]["content"]
    
    @pytest.mark.unit
    def test_custom_openapi_adds_common_parameters(self, mock_app):
        """Test that common parameters are added"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "parameters" in schema["components"]
            
            parameters = schema["components"]["parameters"]
            assert "CameraId" in parameters
            assert "HistoryHours" in parameters
            
            # Validate CameraId parameter
            camera_id_param = parameters["CameraId"]
            assert camera_id_param["name"] == "camera_id"
            assert camera_id_param["in"] == "path"
            assert camera_id_param["required"] is True
            
            # Validate HistoryHours parameter
            history_hours_param = parameters["HistoryHours"]
            assert history_hours_param["name"] == "hours"
            assert history_hours_param["in"] == "query"
            assert history_hours_param["required"] is False
            assert history_hours_param["schema"]["minimum"] == 1
            assert history_hours_param["schema"]["maximum"] == 168
    
    @pytest.mark.unit
    def test_custom_openapi_adds_custom_headers(self, mock_app):
        """Test that custom headers are added"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "headers" in schema["components"]
            
            headers = schema["components"]["headers"]
            expected_headers = ["X-Cache-Status", "X-RateLimit-Remaining", "X-Response-Time"]
            
            for header_name in expected_headers:
                assert header_name in headers
                assert "description" in headers[header_name]
                assert "schema" in headers[header_name]
    
    @pytest.mark.unit
    def test_custom_openapi_adds_api_versioning_info(self, mock_app):
        """Test that API versioning information is added"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "x-api-version" in schema["info"]
            
            version_info = schema["info"]["x-api-version"]
            assert "current" in version_info
            assert "supported" in version_info
            assert "deprecated" in version_info
            assert "sunset" in version_info
            
            assert version_info["current"] == "2.0.0"
            assert isinstance(version_info["supported"], list)
            assert isinstance(version_info["deprecated"], list)
    
    @pytest.mark.unit
    def test_custom_openapi_adds_rate_limiting_info(self, mock_app):
        """Test that rate limiting information is added"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "x-rate-limit" in schema["info"]
            
            rate_limit_info = schema["info"]["x-rate-limit"]
            assert "public_endpoints" in rate_limit_info
            assert "authenticated_endpoints" in rate_limit_info
            
            # Validate public endpoints rate limit
            public_limit = rate_limit_info["public_endpoints"]
            assert public_limit["limit"] == 1000
            assert public_limit["window"] == "1 hour"
            
            # Validate authenticated endpoints rate limit
            auth_limit = rate_limit_info["authenticated_endpoints"]
            assert auth_limit["limit"] == 5000
            assert auth_limit["window"] == "1 hour"
    
    @pytest.mark.unit
    def test_custom_openapi_initializes_components_if_missing(self, mock_app):
        """Test that components section is initialized if not present in base schema"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            # Return schema without components section
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "components" in schema
            assert isinstance(schema["components"], dict)
    
    @pytest.mark.unit
    def test_custom_openapi_preserves_existing_components(self, mock_app):
        """Test that existing components are preserved"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {
                "info": {},
                "paths": {},
                "components": {
                    "schemas": {"ExistingSchema": {"type": "object"}}
                }
            }
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            assert "schemas" in schema["components"]
            assert "ExistingSchema" in schema["components"]["schemas"]
            # Also ensure our custom components are added
            assert "securitySchemes" in schema["components"]
            assert "responses" in schema["components"]

class TestSetupOpenAPI:
    """Test suite for OpenAPI setup function"""
    
    @pytest.mark.unit
    def test_setup_openapi_assigns_custom_function(self):
        """Test that setup_openapi assigns custom_openapi as the openapi function"""
        # Setup
        mock_app = Mock(spec=FastAPI)
        
        # Execute
        setup_openapi(mock_app)
        
        # Assert
        assert mock_app.openapi is not None
        # The function should be a lambda that calls custom_openapi
        # We can't easily test the lambda content, but we can verify it's assigned
        assert callable(mock_app.openapi)
    
    @pytest.mark.unit
    def test_setup_openapi_function_calls_custom_openapi(self):
        """Test that the assigned function calls custom_openapi with the app"""
        # Setup
        mock_app = Mock(spec=FastAPI)
        mock_app.openapi_schema = None
        
        with patch('core.openapi.custom_openapi') as mock_custom_openapi:
            mock_custom_openapi.return_value = {"test": "schema"}
            
            # Execute setup
            setup_openapi(mock_app)
            
            # Execute the assigned function
            result = mock_app.openapi()
            
            # Assert
            mock_custom_openapi.assert_called_once_with(mock_app)
            assert result == {"test": "schema"}

class TestOpenAPIIntegration:
    """Test suite for OpenAPI integration scenarios"""
    
    @pytest.mark.unit
    def test_openapi_schema_structure_completeness(self, mock_app):
        """Test that the generated schema has all required OpenAPI 3.0 components"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {
                "openapi": "3.0.2",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {}
            }
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert essential OpenAPI 3.0 structure
            assert "openapi" in schema or "info" in schema  # Basic structure
            assert "components" in schema
            
            # Assert our custom additions
            components = schema["components"]
            required_components = [
                "securitySchemes", "responses", "parameters", "headers"
            ]
            for component in required_components:
                assert component in components
    
    @pytest.mark.unit
    def test_openapi_schema_caching_behavior(self, mock_app):
        """Test that OpenAPI schema caching works correctly"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute first call
            schema1 = custom_openapi(mock_app)
            
            # Simulate that schema is now cached
            mock_app.openapi_schema = schema1
            
            # Execute second call
            schema2 = custom_openapi(mock_app)
            
            # Assert
            assert schema1 is schema2  # Should return same cached object
            mock_get_openapi.assert_called_once()  # Should only call base function once
    
    @pytest.mark.unit
    def test_openapi_response_examples_are_valid_json(self, mock_app):
        """Test that all response examples in the schema are valid JSON structures"""
        # Setup
        with patch('core.openapi.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = {"info": {}, "paths": {}}
            
            # Execute
            schema = custom_openapi(mock_app)
            
            # Assert
            responses = schema["components"]["responses"]
            
            for response_name, response_def in responses.items():
                content = response_def.get("content", {})
                json_content = content.get("application/json", {})
                example = json_content.get("example")
                
                if example:
                    # Verify it's a valid dictionary (JSON object)
                    assert isinstance(example, dict), f"Example in {response_name} should be a dict"
                    
                    # Verify required fields for error responses
                    if "error" in response_name.lower() or response_name in ["NotFound", "ValidationError", "InternalError"]:
                        assert "detail" in example or "error_code" in example, f"Error response {response_name} missing error info"