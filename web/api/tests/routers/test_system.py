"""
Unit tests for System Router endpoints
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from fastapi import HTTPException

from tests.factories import (
    StatsResponseFactory,
    SystemStatusFactory,
    NightModeStatusFactory,
    ActiveModeStatusFactory
)

class TestSystemEndpoints:
    """Test suite for system router endpoints"""
    
    @pytest.mark.unit
    def test_get_stats_success(self, test_client):
        """Test successful stats retrieval"""
        # Setup
        mock_stats = {
            'total_assessments': 1440,
            'active_cameras': 12,
            'avg_fog_score': 32.5,
            'avg_confidence': 0.89,
            'foggy_conditions': 425,
            'last_update': '2024-01-10T08:30:00Z',
            'period': '24 hours'
        }
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_overall_stats.return_value = mock_stats
            
            # Execute
            response = test_client.get("/api/public/stats")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['total_assessments'] == 1440
            assert data['active_cameras'] == 12
            assert data['avg_fog_score'] == 32.5
            assert data['avg_confidence'] == 0.89
            assert data['foggy_conditions'] == 425
            assert data['last_update'] == '2024-01-10T08:30:00Z'
            assert data['period'] == '24 hours'
    
    @pytest.mark.unit
    def test_get_stats_with_null_values(self, test_client):
        """Test stats retrieval with null database values"""
        # Setup
        mock_stats = {
            'total_assessments': 0,
            'active_cameras': 0,
            'avg_fog_score': 0.0,
            'avg_confidence': 0.0,
            'foggy_conditions': 0,
            'last_update': None,
            'period': '24 hours'
        }
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_overall_stats.return_value = mock_stats
            
            # Execute
            response = test_client.get("/api/public/stats")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['total_assessments'] == 0
            assert data['avg_fog_score'] == 0.0
            assert data['avg_confidence'] == 0.0
            assert data['last_update'] is None
    
    @pytest.mark.unit
    def test_get_stats_service_error(self, test_client):
        """Test error handling in stats endpoint"""
        # Setup
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_overall_stats.side_effect = Exception("Database error")
            
            # Execute
            response = test_client.get("/api/public/stats")
            
            # Assert
            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "INTERNAL_ERROR"
    
    @pytest.mark.unit
    def test_get_system_status_success(self, test_client):
        """Test successful system status retrieval"""
        # Setup
        mock_status = {
            'karlcam_mode': 0,
            'description': 'Normal operation',
            'updated_at': '2024-01-10T08:30:00Z',
            'updated_by': 'system'
        }
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_system_status.return_value = mock_status
            
            # Execute
            response = test_client.get("/api/public/system/status")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['karlcam_mode'] == 0
            assert data['description'] == 'Normal operation'
            assert data['updated_at'] == '2024-01-10T08:30:00Z'
            assert data['updated_by'] == 'system'
    
    @pytest.mark.unit
    def test_get_system_status_night_mode(self, test_client):
        """Test system status when in night mode"""
        # Setup
        mock_status = {
            'karlcam_mode': 1,
            'description': 'Night mode - collection paused',
            'updated_at': '2024-01-10T20:30:00Z',
            'updated_by': 'scheduler'
        }
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_system_status.return_value = mock_status
            
            # Execute
            response = test_client.get("/api/public/system/status")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data['karlcam_mode'] == 1
            assert 'Night mode' in data['description']
    
    @pytest.mark.unit
    def test_get_system_status_service_error(self, test_client):
        """Test error handling in system status endpoint"""
        # Setup
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_system_status.side_effect = Exception("Database error")
            
            # Execute
            response = test_client.get("/api/public/system/status")
            
            # Assert
            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "INTERNAL_ERROR"
    
    @pytest.mark.unit
    def test_set_system_status_success(self, test_client):
        """Test successful system status update"""
        # Setup
        request_data = {
            'karlcam_mode': 1,
            'updated_by': 'admin'
        }
        
        mock_result = {
            'success': True,
            'karlcam_mode': 1,
            'updated_by': 'admin',
            'timestamp': '2024-01-10T08:30:00Z'
        }
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.set_system_status.return_value = mock_result
            
            # Execute
            response = test_client.post("/api/public/system/status", json=request_data)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data['success'] is True
            assert data['karlcam_mode'] == 1
            assert data['updated_by'] == 'admin'
            assert 'timestamp' in data
    
    @pytest.mark.unit
    def test_set_system_status_to_normal_mode(self, test_client):
        """Test setting system to normal operation mode"""
        # Setup
        request_data = {
            'karlcam_mode': 0,
            'updated_by': 'admin-panel'
        }
        
        mock_result = {
            'success': True,
            'karlcam_mode': 0,
            'updated_by': 'admin-panel',
            'timestamp': '2024-01-10T08:30:00Z'
        }
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.set_system_status.return_value = mock_result
            
            # Execute
            response = test_client.post("/api/public/system/status", json=request_data)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data['karlcam_mode'] == 0
    
    @pytest.mark.unit
    def test_set_system_status_service_error(self, test_client):
        """Test error handling in system status update"""
        # Setup
        request_data = {
            'karlcam_mode': 1,
            'updated_by': 'admin'
        }
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.set_system_status.side_effect = Exception("Database error")
            
            # Execute
            response = test_client.post("/api/public/system/status", json=request_data)
            
            # Assert
            assert response.status_code == 500
            assert "Failed to update system status" in response.json()["detail"]
    
    @pytest.mark.unit
    def test_set_system_status_invalid_mode(self, test_client):
        """Test system status update with invalid mode"""
        # Setup
        request_data = {
            'karlcam_mode': 99,  # Invalid mode
            'updated_by': 'admin'
        }
        
        # Execute
        response = test_client.post("/api/public/system/status", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
    
    @pytest.mark.unit
    def test_set_system_status_missing_required_fields(self, test_client):
        """Test system status update with missing required fields"""
        # Setup
        request_data = {
            # Missing karlcam_mode
            'updated_by': 'admin'
        }
        
        # Execute
        response = test_client.post("/api/public/system/status", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
    
    @pytest.mark.unit
    def test_set_system_status_default_updated_by(self, test_client):
        """Test system status update without updated_by field"""
        # Setup
        request_data = {
            'karlcam_mode': 0
            # No updated_by provided - should default to 'api'
        }
        
        mock_result = {
            'success': True,
            'karlcam_mode': 0,
            'updated_by': 'api',  # Default value
            'timestamp': '2024-01-10T08:30:00Z'
        }
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.set_system_status.return_value = mock_result
            
            # Execute
            response = test_client.post("/api/public/system/status", json=request_data)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data['updated_by'] == 'api'
    
    @pytest.mark.unit
    def test_stats_response_format_validation(self, test_client):
        """Test that stats response matches expected schema"""
        # Setup
        mock_stats = StatsResponseFactory()
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_overall_stats.return_value = mock_stats
            
            # Execute
            response = test_client.get("/api/public/stats")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Validate required fields
            required_fields = {
                'total_assessments', 'active_cameras', 'avg_fog_score',
                'avg_confidence', 'foggy_conditions', 'last_update', 'period'
            }
            assert set(data.keys()) == required_fields
            
            # Validate field types
            assert isinstance(data['total_assessments'], int)
            assert isinstance(data['active_cameras'], int)
            assert isinstance(data['avg_fog_score'], (int, float))
            assert isinstance(data['avg_confidence'], (int, float))
            assert isinstance(data['foggy_conditions'], int)
            assert isinstance(data['period'], str)
    
    @pytest.mark.unit
    def test_system_status_response_format_validation(self, test_client):
        """Test that system status response matches expected schema"""
        # Setup
        mock_status = SystemStatusFactory()
        
        with patch('routers.system.StatsService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_system_status.return_value = mock_status
            
            # Execute
            response = test_client.get("/api/public/system/status")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Validate required fields
            required_fields = {'karlcam_mode', 'description', 'updated_at', 'updated_by'}
            assert set(data.keys()) == required_fields
            
            # Validate field types
            assert isinstance(data['karlcam_mode'], int)
            assert isinstance(data['description'], str)
            assert isinstance(data['updated_at'], str)
            assert isinstance(data['updated_by'], str)