"""
Unit tests for Health Router endpoints
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

class TestHealthEndpoints:
    """Test suite for health router endpoints"""
    
    @pytest.mark.unit
    def test_root_health_check_success(self, test_client):
        """Test basic health check endpoint"""
        # Execute
        response = test_client.get("/api/public/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'healthy'
        assert data['service'] == 'KarlCam Fog API'
        assert data['version'] == '2.0.0'
        assert 'timestamp' in data
        
        # Validate timestamp format
        timestamp = data['timestamp']
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")
    
    @pytest.mark.unit
    def test_health_endpoint_with_database_success(self, test_client):
        """Test comprehensive health check with successful database connection"""
        # Setup
        with patch('routers.health.get_db_connection') as mock_get_db_connection:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_get_db_connection.return_value.__enter__.return_value = mock_connection
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Execute
            response = test_client.get("/api/public/health")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['status'] == 'healthy'
            assert data['database'] == 'connected'
            assert 'timestamp' in data
            
            # Verify database query was executed
            mock_cursor.execute.assert_called_once_with("SELECT 1")
    
    @pytest.mark.unit
    def test_health_endpoint_with_database_failure(self, test_client):
        """Test comprehensive health check with database connection failure"""
        # Setup
        with patch('routers.health.get_db_connection') as mock_get_db_connection:
            mock_get_db_connection.side_effect = Exception("Database connection failed")
            
            # Execute
            response = test_client.get("/api/public/health")
            
            # Assert
            assert response.status_code == 200  # Still returns 200, but degraded status
            data = response.json()
            
            assert data['status'] == 'degraded'
            assert data['database'] == 'disconnected'
            assert 'error' in data
            assert 'Database connection failed' in data['error']
            assert 'timestamp' in data
    
    @pytest.mark.unit
    def test_health_endpoint_with_database_timeout(self, test_client):
        """Test health check with database timeout"""
        # Setup
        with patch('routers.health.get_db_connection') as mock_get_db_connection:
            mock_get_db_connection.side_effect = TimeoutError("Connection timeout")
            
            # Execute
            response = test_client.get("/api/public/health")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['status'] == 'degraded'
            assert data['database'] == 'disconnected'
            assert 'timeout' in data['error'].lower()
    
    @pytest.mark.unit
    def test_health_endpoint_with_database_cursor_error(self, test_client):
        """Test health check with database cursor error"""
        # Setup
        with patch('routers.health.get_db_connection') as mock_get_db_connection:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_get_db_connection.return_value.__enter__.return_value = mock_connection
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Make cursor.execute fail
            mock_cursor.execute.side_effect = Exception("SQL execution failed")
            
            # Execute
            response = test_client.get("/api/public/health")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['status'] == 'degraded'
            assert data['database'] == 'disconnected'
            assert 'SQL execution failed' in data['error']
    
    @pytest.mark.unit
    def test_root_health_response_format(self, test_client):
        """Test that root health response matches expected schema"""
        # Execute
        response = test_client.get("/api/public/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        required_fields = {'status', 'service', 'version', 'timestamp'}
        assert set(data.keys()) == required_fields
        
        # Validate field types
        assert isinstance(data['status'], str)
        assert isinstance(data['service'], str)
        assert isinstance(data['version'], str)
        assert isinstance(data['timestamp'], str)
        
        # Validate specific values
        assert data['status'] == 'healthy'
        assert data['service'] == 'KarlCam Fog API'
        assert data['version'] == '2.0.0'
    
    @pytest.mark.unit
    def test_comprehensive_health_response_format_success(self, test_client):
        """Test comprehensive health response format when healthy"""
        # Setup
        with patch('routers.health.get_db_connection') as mock_get_db_connection:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_get_db_connection.return_value.__enter__.return_value = mock_connection
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Execute
            response = test_client.get("/api/public/health")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Validate required fields for healthy response
            required_fields = {'status', 'database', 'timestamp'}
            assert set(data.keys()) == required_fields
            
            # Validate field types
            assert isinstance(data['status'], str)
            assert isinstance(data['database'], str)
            assert isinstance(data['timestamp'], str)
    
    @pytest.mark.unit
    def test_comprehensive_health_response_format_degraded(self, test_client):
        """Test comprehensive health response format when degraded"""
        # Setup
        with patch('routers.health.get_db_connection') as mock_get_db_connection:
            mock_get_db_connection.side_effect = Exception("Database error")
            
            # Execute
            response = test_client.get("/api/public/health")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Validate required fields for degraded response
            required_fields = {'status', 'database', 'error', 'timestamp'}
            assert set(data.keys()) == required_fields
            
            # Validate field types
            assert isinstance(data['status'], str)
            assert isinstance(data['database'], str)
            assert isinstance(data['error'], str)
            assert isinstance(data['timestamp'], str)
            
            # Validate values
            assert data['status'] == 'degraded'
            assert data['database'] == 'disconnected'
    
    @pytest.mark.unit
    def test_health_endpoints_performance(self, test_client):
        """Test that health endpoints respond quickly"""
        # This is more of a smoke test - in a real environment you'd measure actual response times
        
        # Test basic health check
        response = test_client.get("/api/public/")
        assert response.status_code == 200
        
        # Test comprehensive health check
        with patch('routers.health.get_db_connection') as mock_get_db_connection:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_get_db_connection.return_value.__enter__.return_value = mock_connection
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            response = test_client.get("/api/public/health")
            assert response.status_code == 200
    
    @pytest.mark.unit
    def test_health_check_idempotent(self, test_client):
        """Test that health checks are idempotent and don't modify state"""
        # Execute multiple times
        responses = []
        for _ in range(3):
            response = test_client.get("/api/public/")
            responses.append(response)
        
        # Assert all successful
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert data['service'] == 'KarlCam Fog API'
            assert data['version'] == '2.0.0'
    
    @pytest.mark.unit
    def test_comprehensive_health_check_idempotent(self, test_client):
        """Test that comprehensive health checks are idempotent"""
        with patch('routers.health.get_db_connection') as mock_get_db_connection:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_get_db_connection.return_value.__enter__.return_value = mock_connection
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Execute multiple times
            responses = []
            for _ in range(3):
                response = test_client.get("/api/public/health")
                responses.append(response)
            
            # Assert all successful and consistent
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data['status'] == 'healthy'
                assert data['database'] == 'connected'
            
            # Verify database was queried the expected number of times
            assert mock_cursor.execute.call_count == 3