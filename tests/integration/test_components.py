test_refined_components.py

import os
import pytest
import tempfile
import threading
import time
from pathlib import Path

class TestRefinedComponents:
    """Integration test for refined components with enhanced features."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def config_dir(self, temp_dir):
        """Create a test configuration directory."""
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Create base config
        base_config = {
            "app": {
                "name": "Test App",
                "version": "1.0.0"
            },
            "services": {
                "database": {
                    "type": "sqlite",
                    "connection": str(Path(temp_dir) / "test.db"),
                    "pool": {
                        "min_connections": 2,
                        "max_connections": 5
                    }
                },
                "cache": {
                    "type": "file",
                    "file": {
                        "directory": str(Path(temp_dir) / "cache")
                    },
                    "compression": {
                        "enabled": True,
                        "threshold": 1024
                    }
                }
            },
            "credentials": {
                "api_key": "this_will_be_encrypted"
            }
        }
        
        # Write config file
        with open(config_dir / "base.json", "w") as f:
            import json
            json.dump(base_config, f)
        
        # Create test environment config
        with open(config_dir / "test.json", "w") as f:
            json.dump({
                "app": {
                    "name": "Test App - Test Environment"
                }
            }, f)
        
        # Create .env file
        with open(config_dir / ".env.test", "w") as f:
            f.write("DB_CACHE_ENABLED=true\n")
            f.write("MAX_THREADS=4\n")
        
        return config_dir
    
    def test_all_components(self, temp_dir, config_dir):
        """Test all enhanced components working together."""
        from core.config import ConfigManager
        from core.exceptions import LibraryError
        from services.storage import FileClient
        from services.database import DatabaseClient
        from services.cache import CachingService
        from utils.console import ConsoleService
        
        # Initialize components with enhanced features
        
        # 1. Configuration with encryption
        config = ConfigManager(
            config_dir=config_dir, 
            environment="test",
            encryption_key="test_encryption_key"
        )
        
        # Verify config loading
        assert config.get("app.name") == "Test App - Test Environment"
        assert config.get("db.cache.enabled") is True  # From .env.test
        assert config.get("max.threads") == 4  # From .env.test
        
        # Test encryption
        api_key = config.get("credentials.api_key")
        config.set_encrypted("credentials.encrypted_api_key", api_key)
        encrypted_key = config.get("credentials.encrypted_api_key")
        
        # Encrypted value should be different
        assert encrypted_key != api_key
        
        # But should decrypt to the same value
        decrypted = config.get_encrypted("credentials.encrypted_api_key")
        assert decrypted == api_key
        
        # 2. Database with connection pooling
        db_client = DatabaseClient(config)
        
        # Create schema
        db_client.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price REAL,
                category TEXT
            )
        """)
        
        # 3. File operations
        file_client = FileClient(config)
        
        # Create some test data
        products_csv = Path(temp_dir) / "products.csv"
        file_client.write_csv(
            products_csv,
            [
                ["Product 1", "19.99", "Electronics"],
                ["Product 2", "29.99", "Books"],
                ["Product 3", "39.99", "Electronics"],
                ["Product 4", "49.99", "Clothing"]
            ],
            headers=["name", "price", "category"]
        )
        
        # Read the CSV
        csv_data = file_client.read_csv(products_csv)
        assert len(csv_data) == 5  # 4 rows + header
        
        # 4. Multithreaded database operations with connection pooling
        def import_products():
            # Skip header row
            for row in csv_data[1:]:
                try:
                    with db_client.transaction():
                        db_client.execute(
                            "INSERT INTO products (name, price, category) VALUES (?, ?, ?)",
                            row
                        )
                except Exception as e:
                    print(f"Error importing: {e}")
        
        # Create threads to test connection pooling
        threads = []
        for _ in range(2):
            thread = threading.Thread(target=import_products)
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to finish
        for thread in threads:
            thread.join()
            
        # Verify data was imported
        products = db_client.query("SELECT * FROM products")
        assert len(products) == 8  # 4 products * 2 threads
        
        # 5. Caching with compression
        cache = CachingService(config)
        
        # Function that should be cached
        call_count = 0
        
        def expensive_query():
            nonlocal call_count
            call_count += 1
            return db_client.query("SELECT * FROM products WHERE category = 'Electronics'")
        
        # First call should hit the database
        electronics = cache.get_or_set("electronics_products", expensive_query, ttl=60)
        assert len(electronics) == 4  # 2 products * 2 threads
        assert call_count == 1
        
        # Second call should use cache
        electronics = cache.get_or_set("electronics_products", expensive_query, ttl=60)
        assert len(electronics) == 4
        assert call_count == 1  # Count shouldn't increase
        
        # Test cache stats
        stats = cache._backend.get_stats()
        assert stats["hits"] >= 1
        
        # 6. Exception handling
        try:
            # Try an operation that should fail
            db_client.execute("SELECT * FROM nonexistent_table")
            assert False, "Should have raised an exception"
        except LibraryError as e:
            # Should be the specific DatabaseError
            assert e.error_code.startswith("DB-")
            assert "nonexistent_table" in str(e)
        
        # 7. Test batched operations
        batch_data = []
        for i in range(100):
            batch_data.append([f"Batch Product {i}", 10.99, "Batch"])
            
        # Execute as batch
        db_client.executemany(
            "INSERT INTO products (name, price, category) VALUES (?, ?, ?)",
            batch_data
        )
        
        # Verify batch insert
        batch_count = db_client.query_one("SELECT COUNT(*) as count FROM products WHERE category = 'Batch'")
        assert batch_count["count"] == 100
        
        # Clean up
        db_client.close()
        cache.clear()