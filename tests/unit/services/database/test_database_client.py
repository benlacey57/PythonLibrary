import pytest
import sqlite3
from unittest.mock import MagicMock, patch

class TestDatabaseClient:
    """Test suite for DatabaseClient."""
    
    @pytest.fixture
    def config(self):
        """Create a mock configuration for testing."""
        from core.config.config_manager import ConfigManager
        
        config = ConfigManager()
        config.set("services.database.type", "sqlite")
        config.set("services.database.connection", ":memory:")
        return config
    
    @pytest.fixture
    def db_client(self, config):
        """Create a DatabaseClient instance for testing."""
        from services.database.database_client import DatabaseClient
        return DatabaseClient(config)
    
    def test_connection(self, db_client):
        """Test database connection."""
        # Connect to database
        connection = db_client.connect()
        
        # Check connection is valid
        assert connection is not None
        
        # Close connection
        db_client.close()
    
    def test_execute_query(self, db_client):
        """Test executing a query."""
        # Connect and create a table
        db_client.connect()
        db_client.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        
        # Insert data
        db_client.execute("INSERT INTO test (name) VALUES (?)", ["Test 1"])
        db_client.execute("INSERT INTO test (name) VALUES (?)", ["Test 2"])
        
        # Query data
        rows = db_client.query("SELECT * FROM test ORDER BY id")
        
        # Check results
        assert len(rows) == 2
        assert rows[0]["name"] == "Test 1"
        assert rows[1]["name"] == "Test 2"
        
        # Close connection
        db_client.close()
    
    def test_transaction(self, db_client):
        """Test transaction support."""
        # Connect and create a table
        db_client.connect()
        db_client.execute("CREATE TABLE test_transaction (id INTEGER PRIMARY KEY, name TEXT)")
        
        # Start transaction
        with db_client.transaction():
            db_client.execute("INSERT INTO test_transaction (name) VALUES (?)", ["Transaction 1"])
            db_client.execute("INSERT INTO test_transaction (name) VALUES (?)", ["Transaction 2"])
        
        # Check data was committed
        rows = db_client.query("SELECT * FROM test_transaction ORDER BY id")
        assert len(rows) == 2
        
        # Test rollback
        try:
            with db_client.transaction():
                db_client.execute("INSERT INTO test_transaction (name) VALUES (?)", ["Transaction 3"])
                # Force an error
                db_client.execute("INSERT INTO nonexistent_table (name) VALUES (?)", ["Error"])
        except:
            pass
        
        # Check the transaction was rolled back
        rows = db_client.query("SELECT * FROM test_transaction ORDER BY id")
        assert len(rows) == 2  # Still only 2 rows
        
        # Close connection
        db_client.close()
    
    def test_connection_parameters(self):
        """Test connecting with different database types."""
        from services.database.database_client import DatabaseClient
        from core.config.config_manager import ConfigManager
        
        # Test SQLite
        config = ConfigManager()
        config.set("services.database.type", "sqlite")
        config.set("services.database.connection", ":memory:")
        
        sqlite_client = DatabaseClient(config)
        connection = sqlite_client.connect()
        assert connection is not None
        sqlite_client.close()
        
        # Test PostgreSQL (mocked)
        with patch("psycopg2.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            
            config = ConfigManager()
            config.set("services.database.type", "postgresql")
            config.set("services.database.host", "localhost")
            config.set("services.database.port", 5432)
            config.set("services.database.name", "test_db")
            config.set("services.database.user", "test_user")
            config.set("services.database.password", "test_password")
            
            pg_client = DatabaseClient(config)
            pg_client.connect()
            
            # Check that psycopg2.connect was called with correct params
            mock_connect.assert_called_once()
            call_args = mock_connect.call_args[1]
            assert call_args["host"] == "localhost"
            assert call_args["port"] == 5432
            assert call_args["database"] == "test_db"
            assert call_args["user"] == "test_user"
            assert call_args["password"] == "test_password"