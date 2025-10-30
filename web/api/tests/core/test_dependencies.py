"""
Unit tests for dependency injection system
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
import psycopg2

from core.dependencies import (
    DatabasePool,
    get_db_pool,
    get_db_manager,
    get_db_session,
    get_db,
    get_storage_client,
    get_bucket_name,
    cleanup_dependencies
)

class TestDatabasePool:
    """Test suite for DatabasePool class"""
    
    @pytest.mark.unit
    @patch('core.dependencies.psycopg2.pool.ThreadedConnectionPool')
    def test_database_pool_creation(self, mock_pool_class):
        """Test DatabasePool initialization"""
        # Setup
        database_url = "postgresql://user:pass@localhost:5432/test"
        min_conn = 2
        max_conn = 10
        
        # Execute
        db_pool = DatabasePool(database_url, min_conn, max_conn)
        
        # Assert
        mock_pool_class.assert_called_once_with(min_conn, max_conn, database_url)
        assert db_pool.pool == mock_pool_class.return_value
    
    @pytest.mark.unit
    @patch('core.dependencies.psycopg2.pool.ThreadedConnectionPool')
    def test_database_pool_get_connection_success(self, mock_pool_class):
        """Test successful database connection retrieval"""
        # Setup
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        mock_connection = Mock()
        mock_pool.getconn.return_value = mock_connection
        
        db_pool = DatabasePool("test://url", 2, 10)
        
        # Execute
        with db_pool.get_connection() as conn:
            assert conn == mock_connection
        
        # Assert
        mock_pool.getconn.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_connection)
    
    @pytest.mark.unit
    @patch('core.dependencies.psycopg2.pool.ThreadedConnectionPool')
    def test_database_pool_get_connection_with_exception(self, mock_pool_class):
        """Test database connection handling with exception"""
        # Setup
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        mock_connection = Mock()
        mock_pool.getconn.return_value = mock_connection
        
        db_pool = DatabasePool("test://url", 2, 10)
        
        # Execute & Assert
        with pytest.raises(ValueError):
            with db_pool.get_connection() as conn:
                raise ValueError("Test exception")
        
        # Assert rollback was called
        mock_connection.rollback.assert_called_once()
        mock_connection.commit.assert_not_called()
        mock_pool.putconn.assert_called_once_with(mock_connection)
    
    @pytest.mark.unit
    @patch('core.dependencies.psycopg2.pool.ThreadedConnectionPool')
    def test_database_pool_close_all(self, mock_pool_class):
        """Test closing all database connections"""
        # Setup
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        
        db_pool = DatabasePool("test://url", 2, 10)
        
        # Execute
        db_pool.close_all()
        
        # Assert
        mock_pool.closeall.assert_called_once()

class TestDependencyFunctions:
    """Test suite for dependency injection functions"""
    
    @pytest.mark.unit
    @patch('core.dependencies.DatabasePool')
    @patch('core.dependencies.settings')
    def test_get_db_pool_singleton(self, mock_settings, mock_db_pool_class):
        """Test that get_db_pool returns singleton instance"""
        # Setup
        mock_settings.DATABASE_URL = "test://url"
        mock_settings.DB_POOL_MIN_CONN = 2
        mock_settings.DB_POOL_MAX_CONN = 10
        
        # Clear any existing global state
        import core.dependencies
        core.dependencies._db_pool = None
        
        # Execute - Call twice
        pool1 = get_db_pool()
        pool2 = get_db_pool()
        
        # Assert
        assert pool1 == pool2
        mock_db_pool_class.assert_called_once_with(
            database_url="test://url",
            min_conn=2,
            max_conn=10
        )
    
    @pytest.mark.unit
    @patch('core.dependencies.DatabaseManager')
    def test_get_db_manager_singleton(self, mock_db_manager_class):
        """Test that get_db_manager returns singleton instance"""
        # Clear any existing global state
        import core.dependencies
        core.dependencies._db_manager = None
        
        # Execute - Call twice
        manager1 = get_db_manager()
        manager2 = get_db_manager()
        
        # Assert
        assert manager1 == manager2
        mock_db_manager_class.assert_called_once()
    
    @pytest.mark.unit
    @patch('core.dependencies.get_db_pool')
    def test_get_db_session(self, mock_get_db_pool):
        """Test get_db_session context manager"""
        # Setup
        mock_pool = Mock()
        mock_get_db_pool.return_value = mock_pool
        mock_connection = Mock()
        
        @contextmanager
        def mock_get_connection():
            yield mock_connection
        
        mock_pool.get_connection = mock_get_connection
        
        # Execute
        with get_db_session() as session:
            assert session == mock_connection
        
        # Assert
        mock_get_db_pool.assert_called_once()
    
    @pytest.mark.unit
    @patch('core.dependencies.get_db_session')
    def test_get_db_dependency(self, mock_get_db_session):
        """Test get_db dependency function"""
        # Setup
        mock_connection = Mock()
        
        @contextmanager
        def mock_session():
            yield mock_connection
        
        mock_get_db_session.return_value = mock_session()
        
        # Execute
        db_generator = get_db()
        db_connection = next(db_generator)
        
        # Assert
        assert db_connection == mock_connection
    
    @pytest.mark.unit
    @patch('core.dependencies.storage.Client')
    def test_get_storage_client_singleton(self, mock_storage_client_class):
        """Test that get_storage_client returns singleton instance"""
        # Clear any existing global state
        import core.dependencies
        core.dependencies._storage_client = None
        
        # Execute - Call twice
        client1 = get_storage_client()
        client2 = get_storage_client()
        
        # Assert
        assert client1 == client2
        mock_storage_client_class.assert_called_once()
    
    @pytest.mark.unit
    @patch('core.dependencies.settings')
    def test_get_bucket_name(self, mock_settings):
        """Test get_bucket_name dependency"""
        # Setup
        mock_settings.BUCKET_NAME = "test-bucket-name"
        
        # Execute
        bucket_name = get_bucket_name()
        
        # Assert
        assert bucket_name == "test-bucket-name"
    
    @pytest.mark.unit
    @patch('core.dependencies.get_db_pool')
    def test_cleanup_dependencies(self, mock_get_db_pool):
        """Test cleanup_dependencies function"""
        # Setup
        import core.dependencies
        
        # Set up global state
        mock_pool = Mock()
        core.dependencies._db_pool = mock_pool
        core.dependencies._storage_client = Mock()
        
        # Execute
        cleanup_dependencies()
        
        # Assert
        mock_pool.close_all.assert_called_once()
        assert core.dependencies._db_pool is None
        assert core.dependencies._storage_client is None
    
    @pytest.mark.unit
    def test_cleanup_dependencies_no_existing_instances(self):
        """Test cleanup_dependencies when no instances exist"""
        # Setup
        import core.dependencies
        core.dependencies._db_pool = None
        core.dependencies._storage_client = None
        
        # Execute - Should not raise any exceptions
        cleanup_dependencies()
        
        # Assert - Should complete without errors
        assert core.dependencies._db_pool is None
        assert core.dependencies._storage_client is None

class TestDependencyIntegration:
    """Test suite for dependency integration scenarios"""
    
    @pytest.mark.unit
    @patch('core.dependencies.DatabasePool')
    @patch('core.dependencies.settings')
    def test_database_pool_configuration_from_settings(self, mock_settings, mock_db_pool_class):
        """Test that DatabasePool is configured with correct settings"""
        # Setup
        mock_settings.DATABASE_URL = "postgresql://user:pass@host:5432/db"
        mock_settings.DB_POOL_MIN_CONN = 5
        mock_settings.DB_POOL_MAX_CONN = 20
        
        # Clear global state
        import core.dependencies
        core.dependencies._db_pool = None
        
        # Execute
        get_db_pool()
        
        # Assert
        mock_db_pool_class.assert_called_once_with(
            database_url="postgresql://user:pass@host:5432/db",
            min_conn=5,
            max_conn=20
        )
    
    @pytest.mark.unit
    @patch('core.dependencies.storage.Client')
    def test_storage_client_creation(self, mock_storage_client_class):
        """Test Google Cloud Storage client creation"""
        # Clear global state
        import core.dependencies
        core.dependencies._storage_client = None
        
        # Execute
        client = get_storage_client()
        
        # Assert
        mock_storage_client_class.assert_called_once()
        assert client == mock_storage_client_class.return_value
    
    @pytest.mark.unit
    @patch('core.dependencies.DatabaseManager')
    @patch('core.dependencies.DatabasePool')
    def test_db_manager_and_pool_independence(self, mock_pool_class, mock_manager_class):
        """Test that database manager and pool are independent singletons"""
        # Clear global state
        import core.dependencies
        core.dependencies._db_pool = None
        core.dependencies._db_manager = None
        
        # Execute
        manager = get_db_manager()
        pool = get_db_pool()
        
        # Assert
        assert manager != pool
        mock_manager_class.assert_called_once()
        mock_pool_class.assert_called_once()
    
    @pytest.mark.unit
    def test_dependency_cleanup_and_recreation(self):
        """Test that dependencies can be recreated after cleanup"""
        # Clear and setup initial state
        import core.dependencies
        core.dependencies._db_pool = Mock()
        core.dependencies._storage_client = Mock()
        
        # Execute cleanup
        cleanup_dependencies()
        
        # Assert cleanup worked
        assert core.dependencies._db_pool is None
        assert core.dependencies._storage_client is None
        
        # Execute recreation
        with patch('core.dependencies.DatabasePool'), \
             patch('core.dependencies.storage.Client'), \
             patch('core.dependencies.settings'):
            
            new_pool = get_db_pool()
            new_client = get_storage_client()
            
            # Assert new instances were created
            assert new_pool is not None
            assert new_client is not None

class TestErrorHandling:
    """Test suite for error handling in dependencies"""
    
    @pytest.mark.unit
    @patch('core.dependencies.psycopg2.pool.ThreadedConnectionPool')
    def test_database_pool_creation_failure(self, mock_pool_class):
        """Test handling of database pool creation failure"""
        # Setup
        mock_pool_class.side_effect = psycopg2.OperationalError("Connection failed")
        
        # Execute & Assert
        with pytest.raises(psycopg2.OperationalError):
            DatabasePool("invalid://url", 2, 10)
    
    @pytest.mark.unit
    @patch('core.dependencies.storage.Client')
    def test_storage_client_creation_failure(self, mock_storage_client_class):
        """Test handling of storage client creation failure"""
        # Setup
        mock_storage_client_class.side_effect = Exception("GCS credentials error")
        
        # Clear global state
        import core.dependencies
        core.dependencies._storage_client = None
        
        # Execute & Assert
        with pytest.raises(Exception):
            get_storage_client()
    
    @pytest.mark.unit
    @patch('core.dependencies.psycopg2.pool.ThreadedConnectionPool')
    def test_database_pool_connection_failure(self, mock_pool_class):
        """Test handling of database connection retrieval failure"""
        # Setup
        mock_pool = Mock()
        mock_pool.getconn.side_effect = psycopg2.OperationalError("No connections available")
        mock_pool_class.return_value = mock_pool
        
        db_pool = DatabasePool("test://url", 2, 10)
        
        # Execute & Assert
        with pytest.raises(psycopg2.OperationalError):
            with db_pool.get_connection():
                pass