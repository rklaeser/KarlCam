"""
Unit tests for Config Router endpoints
"""
import pytest
from unittest.mock import patch

class TestConfigEndpoints:
    """Test suite for config router endpoints"""
    
    @pytest.mark.unit
    def test_get_public_config_success(self, test_client):
        """Test successful public config retrieval"""
        # Execute
        response = test_client.get("/api/public/config/public")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        required_fields = {
            'app_name', 'version', 'environment', 'fog_detection_threshold',
            'foggy_conditions_threshold', 'default_location', 'default_history_hours',
            'stats_period_hours', 'api_prefix'
        }
        assert set(data.keys()) == required_fields
        
        # Validate default location structure
        location = data['default_location']
        assert 'name' in location
        assert 'latitude' in location
        assert 'longitude' in location
        
        # Validate field types
        assert isinstance(data['app_name'], str)
        assert isinstance(data['version'], str)
        assert isinstance(data['environment'], str)
        assert isinstance(data['fog_detection_threshold'], int)
        assert isinstance(data['foggy_conditions_threshold'], int)
        assert isinstance(data['default_history_hours'], int)
        assert isinstance(data['stats_period_hours'], int)
        assert isinstance(data['api_prefix'], str)
        
        assert isinstance(location['name'], str)
        assert isinstance(location['latitude'], (int, float))
        assert isinstance(location['longitude'], (int, float))
    
    @pytest.mark.unit
    def test_get_public_config_values(self, test_client):
        """Test that public config returns expected values"""
        # Execute
        response = test_client.get("/api/public/config/public")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Validate specific values from test settings
        assert data['app_name'] == 'KarlCam Fog API'
        assert data['environment'] == 'test'  # From test settings override
        assert data['fog_detection_threshold'] == 20
        assert data['foggy_conditions_threshold'] == 50
        assert data['default_history_hours'] == 24
        assert data['stats_period_hours'] == 24
        assert data['api_prefix'] == '/api'
        
        # Validate San Francisco default location
        location = data['default_location']
        assert location['name'] == 'San Francisco'
        assert location['latitude'] == 37.7749
        assert location['longitude'] == -122.4194
    
    @pytest.mark.unit
    def test_get_public_config_no_sensitive_data(self, test_client):
        """Test that public config doesn't expose sensitive data"""
        # Execute
        response = test_client.get("/api/public/config/public")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Ensure no sensitive fields are present
        sensitive_fields = {
            'database_url', 'db_password', 'secret_key', 'gcp_credentials',
            'bucket_name', 'project_id', 'service_account_key'
        }
        
        for field in sensitive_fields:
            assert field not in data, f"Sensitive field '{field}' found in public config"
    
    @pytest.mark.unit 
    def test_get_full_config_in_production(self, test_client):
        """Test that full config is blocked in production environment"""
        # Setup - Mock production environment
        with patch('routers.config.settings') as mock_settings:
            mock_settings.is_production = True
            
            # Execute
            response = test_client.get("/api/public/config/full")
            
            # Assert
            assert response.status_code == 403
            data = response.json()
            assert "not available in production" in data['detail']
    
    @pytest.mark.unit
    def test_get_full_config_in_development(self, test_client):
        """Test full config access in development environment"""
        # Setup - Mock development environment
        with patch('routers.config.settings') as mock_settings:
            # Set up mock settings with all required attributes
            mock_settings.is_production = False
            mock_settings.APP_NAME = 'KarlCam Fog API'
            mock_settings.VERSION = '2.0.0'
            mock_settings.ENVIRONMENT = 'test'
            mock_settings.DEBUG = True
            mock_settings.API_PREFIX = '/api'
            mock_settings.FOG_DETECTION_THRESHOLD = 20
            mock_settings.FOGGY_CONDITIONS_THRESHOLD = 50
            mock_settings.DEFAULT_LATITUDE = 37.7749
            mock_settings.DEFAULT_LONGITUDE = -122.4194
            mock_settings.DEFAULT_LOCATION_NAME = 'San Francisco'
            mock_settings.RECENT_IMAGES_DAYS = 1
            mock_settings.CAMERA_HISTORY_DAYS = 30
            mock_settings.DEFAULT_HISTORY_HOURS = 24
            mock_settings.STATS_PERIOD_HOURS = 24
            mock_settings.DB_POOL_MIN_CONN = 1
            mock_settings.DB_POOL_MAX_CONN = 10
            mock_settings.DB_POOL_TIMEOUT = 30
            mock_settings.BUCKET_NAME = 'test-bucket'
            mock_settings.GCS_TIMEOUT = 60
            mock_settings.CORS_ORIGINS = ['*']
            mock_settings.CORS_ALLOW_CREDENTIALS = True
            mock_settings.CORS_ALLOWED_METHODS = ['*']
            mock_settings.CORS_ALLOWED_HEADERS = ['*']
            
            # Execute
            response = test_client.get("/api/public/config/full")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Validate comprehensive config fields
            assert 'app_name' in data
            assert 'version' in data
            assert 'environment' in data
            assert 'debug' in data
            assert 'fog_detection_threshold' in data
            assert 'db_pool_min_conn' in data
            assert 'bucket_name' in data
            assert 'cors_origins' in data
    
    @pytest.mark.unit
    def test_get_full_config_includes_database_settings(self, test_client):
        """Test that full config includes database configuration"""
        # Setup
        with patch('routers.config.settings') as mock_settings:
            mock_settings.is_production = False
            mock_settings.DB_POOL_MIN_CONN = 2
            mock_settings.DB_POOL_MAX_CONN = 20
            mock_settings.DB_POOL_TIMEOUT = 45
            # Set other required attributes
            for attr in ['APP_NAME', 'VERSION', 'ENVIRONMENT', 'DEBUG', 'API_PREFIX',
                        'FOG_DETECTION_THRESHOLD', 'FOGGY_CONDITIONS_THRESHOLD',
                        'DEFAULT_LATITUDE', 'DEFAULT_LONGITUDE', 'DEFAULT_LOCATION_NAME',
                        'RECENT_IMAGES_DAYS', 'CAMERA_HISTORY_DAYS', 'DEFAULT_HISTORY_HOURS',
                        'STATS_PERIOD_HOURS', 'BUCKET_NAME', 'GCS_TIMEOUT',
                        'CORS_ORIGINS', 'CORS_ALLOW_CREDENTIALS', 'CORS_ALLOWED_METHODS',
                        'CORS_ALLOWED_HEADERS']:
                setattr(mock_settings, attr, 'test_value')
            
            # Execute
            response = test_client.get("/api/public/config/full")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['db_pool_min_conn'] == 2
            assert data['db_pool_max_conn'] == 20
            assert data['db_pool_timeout'] == 45
    
    @pytest.mark.unit
    def test_get_full_config_includes_gcs_settings(self, test_client):
        """Test that full config includes GCS configuration"""
        # Setup
        with patch('routers.config.settings') as mock_settings:
            mock_settings.is_production = False
            mock_settings.BUCKET_NAME = 'karlcam-test-bucket'
            mock_settings.GCS_TIMEOUT = 120
            # Set other required attributes
            for attr in ['APP_NAME', 'VERSION', 'ENVIRONMENT', 'DEBUG', 'API_PREFIX',
                        'FOG_DETECTION_THRESHOLD', 'FOGGY_CONDITIONS_THRESHOLD',
                        'DEFAULT_LATITUDE', 'DEFAULT_LONGITUDE', 'DEFAULT_LOCATION_NAME',
                        'RECENT_IMAGES_DAYS', 'CAMERA_HISTORY_DAYS', 'DEFAULT_HISTORY_HOURS',
                        'STATS_PERIOD_HOURS', 'DB_POOL_MIN_CONN', 'DB_POOL_MAX_CONN',
                        'DB_POOL_TIMEOUT', 'CORS_ORIGINS', 'CORS_ALLOW_CREDENTIALS',
                        'CORS_ALLOWED_METHODS', 'CORS_ALLOWED_HEADERS']:
                setattr(mock_settings, attr, 'test_value')
            
            # Execute
            response = test_client.get("/api/public/config/full")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['bucket_name'] == 'karlcam-test-bucket'
            assert data['gcs_timeout'] == 120
    
    @pytest.mark.unit
    def test_get_full_config_includes_cors_settings(self, test_client):
        """Test that full config includes CORS configuration"""
        # Setup
        with patch('routers.config.settings') as mock_settings:
            mock_settings.is_production = False
            mock_settings.CORS_ORIGINS = ['http://localhost:3000', 'https://karlcam.org']
            mock_settings.CORS_ALLOW_CREDENTIALS = False
            mock_settings.CORS_ALLOWED_METHODS = ['GET', 'POST']
            mock_settings.CORS_ALLOWED_HEADERS = ['Content-Type', 'Authorization']
            # Set other required attributes
            for attr in ['APP_NAME', 'VERSION', 'ENVIRONMENT', 'DEBUG', 'API_PREFIX',
                        'FOG_DETECTION_THRESHOLD', 'FOGGY_CONDITIONS_THRESHOLD',
                        'DEFAULT_LATITUDE', 'DEFAULT_LONGITUDE', 'DEFAULT_LOCATION_NAME',
                        'RECENT_IMAGES_DAYS', 'CAMERA_HISTORY_DAYS', 'DEFAULT_HISTORY_HOURS',
                        'STATS_PERIOD_HOURS', 'DB_POOL_MIN_CONN', 'DB_POOL_MAX_CONN',
                        'DB_POOL_TIMEOUT', 'BUCKET_NAME', 'GCS_TIMEOUT']:
                setattr(mock_settings, attr, 'test_value')
            
            # Execute
            response = test_client.get("/api/public/config/full")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['cors_origins'] == ['http://localhost:3000', 'https://karlcam.org']
            assert data['cors_allow_credentials'] is False
            assert data['cors_allowed_methods'] == ['GET', 'POST']
            assert data['cors_allowed_headers'] == ['Content-Type', 'Authorization']
    
    @pytest.mark.unit
    def test_config_endpoints_consistency(self, test_client):
        """Test that public and full config share consistent values"""
        # Get public config
        public_response = test_client.get("/api/public/config/public")
        assert public_response.status_code == 200
        public_data = public_response.json()
        
        # Get full config (in test environment)
        with patch('routers.config.settings') as mock_settings:
            mock_settings.is_production = False
            # Copy values from public config to ensure consistency
            mock_settings.APP_NAME = public_data['app_name']
            mock_settings.VERSION = public_data['version']
            mock_settings.ENVIRONMENT = public_data['environment']
            mock_settings.FOG_DETECTION_THRESHOLD = public_data['fog_detection_threshold']
            mock_settings.API_PREFIX = public_data['api_prefix']
            # Set other required attributes
            for attr in ['DEBUG', 'FOGGY_CONDITIONS_THRESHOLD', 'DEFAULT_LATITUDE',
                        'DEFAULT_LONGITUDE', 'DEFAULT_LOCATION_NAME', 'RECENT_IMAGES_DAYS',
                        'CAMERA_HISTORY_DAYS', 'DEFAULT_HISTORY_HOURS', 'STATS_PERIOD_HOURS',
                        'DB_POOL_MIN_CONN', 'DB_POOL_MAX_CONN', 'DB_POOL_TIMEOUT',
                        'BUCKET_NAME', 'GCS_TIMEOUT', 'CORS_ORIGINS', 'CORS_ALLOW_CREDENTIALS',
                        'CORS_ALLOWED_METHODS', 'CORS_ALLOWED_HEADERS']:
                setattr(mock_settings, attr, 'test_value')
            
            full_response = test_client.get("/api/public/config/full")
            assert full_response.status_code == 200
            full_data = full_response.json()
            
            # Check that shared fields have consistent values
            shared_fields = ['app_name', 'version', 'environment', 'fog_detection_threshold', 'api_prefix']
            for field in shared_fields:
                assert public_data[field] == full_data[field], f"Inconsistent value for {field}"
    
    @pytest.mark.unit
    def test_public_config_response_format(self, test_client):
        """Test that public config response format is stable"""
        # Execute
        response = test_client.get("/api/public/config/public")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Validate that all expected fields are present and have correct types
        assert isinstance(data.get('app_name'), str)
        assert isinstance(data.get('version'), str)  
        assert isinstance(data.get('environment'), str)
        assert isinstance(data.get('fog_detection_threshold'), int)
        assert isinstance(data.get('foggy_conditions_threshold'), int)
        assert isinstance(data.get('default_history_hours'), int)
        assert isinstance(data.get('stats_period_hours'), int)
        assert isinstance(data.get('api_prefix'), str)
        
        # Validate default_location structure
        location = data.get('default_location', {})
        assert isinstance(location.get('name'), str)
        assert isinstance(location.get('latitude'), (int, float))
        assert isinstance(location.get('longitude'), (int, float))