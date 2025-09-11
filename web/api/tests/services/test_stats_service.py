"""
Unit tests for StatsService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services.stats_service import StatsService
from tests.factories import StatsResponseFactory, SystemStatusFactory

class TestStatsService:
    """Test suite for StatsService"""
    
    @pytest.fixture
    def stats_service(self):
        """Create StatsService instance"""
        return StatsService()
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_get_overall_stats_success(self, mock_get_db_connection, stats_service):
        """Test successful overall stats retrieval"""
        # Setup
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock database response
        mock_stats = {
            'total_assessments': 1440,
            'active_cameras': 12,
            'avg_fog_score': 32.5,
            'avg_confidence': 0.89,
            'foggy_conditions': 425,
            'last_update': datetime(2024, 1, 10, 8, 30, 0)
        }
        mock_cursor.fetchone.return_value = mock_stats
        
        # Execute
        result = stats_service.get_overall_stats()
        
        # Assert
        assert result['total_assessments'] == 1440
        assert result['active_cameras'] == 12
        assert result['avg_fog_score'] == 32.5
        assert result['avg_confidence'] == 0.89
        assert result['foggy_conditions'] == 425
        assert result['last_update'] == '2024-01-10T08:30:00'
        assert result['period'] == '24 hours'
        
        # Verify SQL query
        mock_cursor.execute.assert_called_once()
        executed_query = mock_cursor.execute.call_args[0][0]
        assert 'COUNT(*)' in executed_query
        assert 'AVG(fog_score)' in executed_query
        assert 'COUNT(CASE WHEN fog_score >' in executed_query
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_get_overall_stats_null_values(self, mock_get_db_connection, stats_service):
        """Test stats handling with null database values"""
        # Setup
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock database response with null values
        mock_stats = {
            'total_assessments': 0,
            'active_cameras': 0,
            'avg_fog_score': None,
            'avg_confidence': None,
            'foggy_conditions': 0,
            'last_update': None
        }
        mock_cursor.fetchone.return_value = mock_stats
        
        # Execute
        result = stats_service.get_overall_stats()
        
        # Assert
        assert result['avg_fog_score'] == 0.0  # Null converted to 0
        assert result['avg_confidence'] == 0.0  # Null converted to 0
        assert result['last_update'] is None
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_get_overall_stats_database_error(self, mock_get_db_connection, stats_service):
        """Test error handling when database fails"""
        # Setup
        mock_get_db_connection.side_effect = Exception("Database connection failed")
        
        # Execute
        result = stats_service.get_overall_stats()
        
        # Assert
        assert 'error' in result
        assert 'Failed to fetch statistics' in result['error']
        assert 'timestamp' in result
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_get_system_status_success(self, mock_get_db_connection, stats_service):
        """Test successful system status retrieval"""
        # Setup
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock database response
        mock_status = {
            'status_value': 0,
            'description': 'Normal operation',
            'updated_at': datetime(2024, 1, 10, 8, 30, 0),
            'updated_by': 'system'
        }
        mock_cursor.fetchone.return_value = mock_status
        
        # Execute
        result = stats_service.get_system_status()
        
        # Assert
        assert result['karlcam_mode'] == 0
        assert result['description'] == 'Normal operation'
        assert result['updated_at'] == '2024-01-10T08:30:00'
        assert result['updated_by'] == 'system'
        
        # Verify SQL query
        mock_cursor.execute.assert_called_once()
        executed_query = mock_cursor.execute.call_args[0][0]
        assert 'karlcam_mode' in executed_query
        assert 'system_status' in executed_query
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_get_system_status_not_found(self, mock_get_db_connection, stats_service):
        """Test system status when no record exists"""
        # Setup
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock empty response
        mock_cursor.fetchone.return_value = None
        
        # Execute
        result = stats_service.get_system_status()
        
        # Assert
        assert result['karlcam_mode'] == 0
        assert result['description'] == 'Default mode'
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_get_system_status_database_error(self, mock_get_db_connection, stats_service):
        """Test error handling in system status retrieval"""
        # Setup
        mock_get_db_connection.side_effect = Exception("Database error")
        
        # Execute
        result = stats_service.get_system_status()
        
        # Assert
        assert result['karlcam_mode'] == 0
        assert 'Default mode (error)' in result['description']
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_set_system_status_success(self, mock_get_db_connection, stats_service):
        """Test successful system status update"""
        # Setup
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        request_data = {
            'karlcam_mode': 1,
            'updated_by': 'admin'
        }
        
        # Execute
        result = stats_service.set_system_status(request_data)
        
        # Assert
        assert result['success'] is True
        assert result['karlcam_mode'] == 1
        assert result['updated_by'] == 'admin'
        assert 'timestamp' in result
        
        # Verify database operations
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        
        # Check SQL query
        executed_query = mock_cursor.execute.call_args[0][0]
        assert 'INSERT INTO system_status' in executed_query
        assert 'ON CONFLICT' in executed_query
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_set_system_status_default_updated_by(self, mock_get_db_connection, stats_service):
        """Test system status update with default updated_by"""
        # Setup
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        request_data = {
            'karlcam_mode': 0
            # No updated_by provided
        }
        
        # Execute
        result = stats_service.set_system_status(request_data)
        
        # Assert
        assert result['updated_by'] == 'api'  # Default value
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_set_system_status_database_error(self, mock_get_db_connection, stats_service):
        """Test error handling in system status update"""
        # Setup
        mock_get_db_connection.side_effect = Exception("Database error")
        
        request_data = {
            'karlcam_mode': 1,
            'updated_by': 'admin'
        }
        
        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            stats_service.set_system_status(request_data)
        
        assert "Database error" in str(exc_info.value)
    
    @pytest.mark.unit
    @patch('services.stats_service.get_db_connection')
    def test_get_overall_stats_uses_configured_thresholds(self, mock_get_db_connection, stats_service):
        """Test that stats query uses configured fog threshold"""
        # Setup
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock minimal response
        mock_cursor.fetchone.return_value = {
            'total_assessments': 0,
            'active_cameras': 0,
            'avg_fog_score': 0,
            'avg_confidence': 0,
            'foggy_conditions': 0,
            'last_update': None
        }
        
        # Execute
        stats_service.get_overall_stats()
        
        # Assert - Check that configured threshold is used in query
        call_args = mock_cursor.execute.call_args
        query_params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        
        # Should include the configured threshold (50) and period (24)
        assert 50 in query_params  # FOGGY_CONDITIONS_THRESHOLD
        assert 24 in query_params  # STATS_PERIOD_HOURS
    
    @pytest.mark.unit
    def test_stats_response_format_consistency(self, stats_service):
        """Test that stats response format is consistent"""
        # This test ensures the response format matches our API schema
        expected_keys = {
            'total_assessments',
            'active_cameras', 
            'avg_fog_score',
            'avg_confidence',
            'foggy_conditions',
            'last_update',
            'period'
        }
        
        with patch('services.stats_service.get_db_connection') as mock_conn:
            # Setup mock
            mock_cursor = MagicMock()
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = {
                'total_assessments': 100,
                'active_cameras': 5,
                'avg_fog_score': 25.0,
                'avg_confidence': 0.8,
                'foggy_conditions': 20,
                'last_update': datetime.now()
            }
            
            # Execute
            result = stats_service.get_overall_stats()
            
            # Assert
            assert set(result.keys()) == expected_keys
            assert isinstance(result['period'], str)
            assert 'hours' in result['period']