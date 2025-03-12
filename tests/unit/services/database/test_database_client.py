import pytest
import sqlite3
import threading
import time
from unittest.mock import MagicMock, patch

from core.exceptions import DatabaseError, ConnectionError

class TestDatabaseClient:
    """Test suite for DatabaseClient."""
    
    @pytest.fixture
    def config(self):
        """Create a mock configuration for testing."""
        from core.config import ConfigManager
        
        config = ConfigManager()
        config.set("services.database.type", "sqlite")
        config.set("services.database.connection", ":memory:")
        config.set("services.database.pool.min_connections", 2)
        config.set("services.database.pool.max_connections", 5)
        return config
    
    @pytest.fixture
    def db_client(self, config):
        """Create a DatabaseClient instance for testing."""
        from services.database import DatabaseClient
        client = DatabaseClient(config)
        yield client
        client.close()
    
    def test_connection_pooling(self, db_client):
        """Test database connection pooling."""
        # Get multiple connections
        conn1 = db_client.connect()
        db_client.release(conn1)
        
        conn2 = db_client.connect()
        db_client.release(conn2)
        
        # The second connection should be the first one reused
        assert conn1 is conn2
        
        # Test multiple concurrent connections
        connections = []
        for _ in range(3):
            conn = db_client.connect()
            connections.append(conn)
            
        # All connections should be different
        assert len(set(connections)) == 3
        
        # Release all connections
        for conn in connections:
            db_client.release(conn)
    
    def test_execute_query(self, db_client):
        """Test executing a query."""
        # Connect and create a table
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
    
    def test_executemany(self, db_client):
        """Test executing multiple queries in batch."""
        # Create a table
        db_client.execute("CREATE TABLE batch_test (id INTEGER PRIMARY KEY, name TEXT)")
        
        # Prepare batch data
        batch_data = [
            ["Item 1"],
            ["Item 2"],
            ["Item 3"],
            ["Item 4"],
            ["Item 5"]
        ]
        
        # Execute batch insert
        affected = db_client.executemany(
            "INSERT INTO batch_test (name) VALUES (?)",
            batch_data
        )
        
        # Check affected rows
        assert affected == 5
        
        # Query data to verify
        rows = db_client.query("SELECT * FROM batch_test ORDER BY id")
        assert len(rows) == 5
        assert rows[2]["name"] == "Item 3"
    
    def test_query_one(self, db_client):
        """Test querying a single row."""
        # Create and populate table
        db_client.execute("CREATE TABLE single_test (id INTEGER PRIMARY KEY, name TEXT)")
        db_client.execute("INSERT INTO single_test (name) VALUES (?)", ["Single Item"])
        
        # Query single row
        row = db_client.query_one("SELECT * FROM single_test WHERE id = 1")
        
        # Check result
        assert row is not None
        assert row["name"] == "Single Item"
        
        # Query non-existent row
        row = db_client.query_one("SELECT * FROM single_test WHERE id = 999")
        assert row is None
    
    def test_transaction(self, db_client):
        """Test transaction support."""
        # Connect and create a table
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
        except DatabaseError:
            pass
        
        # Check the transaction was rolled back
        rows = db_client.query("SELECT * FROM test_transaction ORDER BY id")
        assert len(rows) == 2  # Still only 2 rows
    
    def test_nested_transactions(self, db_client):
        """Test support for nested transactions."""
        # Create a table
        db_client.execute("CREATE TABLE nested_tx (id INTEGER PRIMARY KEY, value TEXT)")
        
        # Start outer transaction
        with db_client.transaction():
            db_client.execute("INSERT INTO nested_tx (value) VALUES (?)", ["Outer"])
            
            # Start inner transaction
            with db_client.transaction():
                db_client.execute("INSERT INTO nested_tx (value) VALUES (?)", ["Inner"])
                
            # Check inner commit works
            inner_check = db_client.query("SELECT * FROM nested_tx")
            assert len(inner_check) == 2
            
        # Check outer commit works
        outer_check = db_client.query("SELECT * FROM nested_tx")
        assert len(outer_check) == 2
        
        # Test inner rollback doesn't affect outer
        try:
            with db_client.transaction():
                db_client.execute("INSERT INTO nested_tx (value) VALUES (?)", ["Outer 2"])
                
                try:
                    with db_client.transaction():
                        db_client.execute("INSERT INTO nested_tx (value) VALUES (?)", ["Inner 2"])
                        raise ValueError("Force inner rollback")
                except ValueError:
                    pass
                    
                # Add another in outer
                db_client.execute("INSERT INTO nested_tx (value) VALUES (?)", ["Outer 3"])
        except:
            pass
            
        # Check final state
        final_check = db_client.query("SELECT * FROM nested_tx ORDER BY id")
        assert len(final_check) == 4
        assert final_check[2]["value"] == "Outer 2"
        assert final_check[3]["value"] == "Outer 3"
    
    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        from services.database import DatabaseClient
        from core.config import ConfigManager
        
        # Configure with invalid connection
        config = ConfigManager()
        config.set("services.database.type", "sqlite")
        config.set("services.database.connection", "/nonexistent/path/db.sqlite")
        
        # Creation shouldn't fail, only connecting
        db = DatabaseClient(config)
        
        # Connection should raise a helpful error
        with pytest.raises(ConnectionError) as exc_info:
            conn = db.connect()
            
        assert "DatabaseClient" in str(exc_info.value)
        
        # Clean up
        db.close()
    
    def test_query_error_handling(self, db_client):
        """Test handling of query errors."""
        # Execute invalid query
        with pytest.raises(DatabaseError) as exc_info:
            db_client.execute("SELECT * FROM nonexistent_table")
            
        assert "Query execution failed" in str(exc_info.value)
        assert exc_info.value.error_code == "DB-004"
    
    def test_connection_reuse_in_context(self, db_client):
        """Test connection reuse when using context manager."""
        with db_client as client:
            # First query should get a connection
            client.execute("CREATE TABLE context_test (id INTEGER PRIMARY KEY, value TEXT)")
            client.execute("INSERT INTO context_test (value) VALUES (?)", ["Test"])
            
            # Second query should reuse the same connection
            rows = client.query("SELECT * FROM context_test")
            assert len(rows) == 1
            assert rows[0]["value"] == "Test"
    
    def test_concurrent_access(self, db_client):
        """Test concurrent database access."""
        # Skip for SQLite memory database which doesn't support true concurrency
        if ":memory:" in db_client.config.get("services.database.connection", ""):
            pytest.skip("In-memory SQLite doesn't support concurrent access")
            
        # Set up a test table
        db_client.execute("CREATE TABLE concurrent_test (id INTEGER PRIMARY KEY, counter INTEGER)")
        db_client.execute("INSERT INTO concurrent_test (id, counter) VALUES (1, 0)")
        
        # Define a function to increment the counter
        def increment_counter():
            for _ in range(5):
                with db_client.transaction():
                    # Read current value
                    row = db_client.query_one("SELECT counter FROM concurrent_test WHERE id = 1")
                    current = row["counter"]
                    
                    # Increment
                    db_client.execute(
                        "UPDATE concurrent_test SET counter = ? WHERE id = 1",
                        [current + 1]
                    )
                    
                    # Small delay to increase chance of concurrency issues
                    time.sleep(0.01)
        
        # Create and start threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=increment_counter)
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to finish
        for thread in threads:
            thread.join()
            
        # Check final counter value
        final = db_client.query_one("SELECT counter FROM concurrent_test WHERE id = 1")
        assert final["counter"] == 15  # 3 threads * 5 increments each