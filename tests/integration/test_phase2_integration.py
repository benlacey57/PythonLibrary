import os
import pytest
import tempfile
from pathlib import Path

class TestPhase2Integration:
    """Integration test for Phase 2 components."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_file_database_cache_integration(self, temp_dir):
        """Test integration between FileClient, DatabaseClient, and CachingService."""
        from core.config.config_manager import ConfigManager
        from services.storage.file_client import FileClient
        from services.database.database_client import DatabaseClient
        from services.cache.caching_service import CachingService
        from utils.console.console_service import ConsoleService
        
        # Set up configuration
        config = ConfigManager()
        config.set("services.database.type", "sqlite")
        config.set("services.database.connection", ":memory:")
        config.set("services.cache.type", "file")
        config.set("services.cache.file.directory", os.path.join(temp_dir, "cache"))
        
        # Initialize components
        file_client = FileClient(config)
        db_client = DatabaseClient(config)
        cache_service = CachingService(config)
        console_service = ConsoleService(config)
        
        # Create test data
        test_data = [
            {"id": 1, "name": "Item 1", "value": 100},
            {"id": 2, "name": "Item 2", "value": 200},
            {"id": 3, "name": "Item 3", "value": 300}
        ]
        
        # 1. Save data to a JSON file
        json_file = os.path.join(temp_dir, "test_data.json")
        file_client.write_json(json_file, test_data)
        
        # 2. Set up database and insert the data
        db_client.connect()
        db_client.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        
        for item in test_data:
            db_client.execute(
                "INSERT INTO items (id, name, value) VALUES (?, ?, ?)",
                [item["id"], item["name"], item["value"]]
            )
        
        # 3. Query the database through the cache
        def fetch_items():
            """Fetch items from database."""
            return db_client.query("SELECT * FROM items ORDER BY id")
        
        # First fetch will query the database
        items = cache_service.get_or_set("items", fetch_items, ttl=60)
        assert len(items) == 3
        assert items[0]["name"] == "Item 1"
        
        # Second fetch should use cached value (we can verify this by dropping the table)
        db_client.execute("DROP TABLE items")
        
        # This should still work because it uses the cache
        cached_items = cache_service.get("items")
        assert len(cached_items) == 3
        assert cached_items[2]["value"] == 300
        
        # 4. Export results to CSV
        csv_file = os.path.join(temp_dir, "items.csv")
        
        # Convert dict rows to list rows
        headers = ["id", "name", "value"]
        rows = [[str(item[h]) for h in headers] for item in cached_items]
        
        file_client.write_csv(csv_file, rows, headers=headers)
        
        # 5. Read CSV back
        csv_data = file_client.read_csv(csv_file)
        assert csv_data[0] == headers
        assert csv_data[1][1] == "Item 1"
        assert csv_data[3][2] == "300"
        
        # Clean up
        db_client.close()
        cache_service.clear()