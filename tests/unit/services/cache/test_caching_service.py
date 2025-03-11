import os
import time
import pytest
import tempfile
from pathlib import Path

class TestCachingService:
    """Test suite for CachingService."""
    
    @pytest.fixture
    def memory_cache(self):
        """Create a CachingService with memory backend."""
        from services.cache.caching_service import CachingService
        from core.config.config_manager import ConfigManager
        
        config = ConfigManager()
        config.set("services.cache.type", "memory")
        
        return CachingService(config)
    
    @pytest.fixture
    def file_cache(self):
        """Create a CachingService with file backend."""
        from services.cache.caching_service import CachingService
        from core.config.config_manager import ConfigManager
        
        temp_dir = tempfile.mkdtemp()
        
        config = ConfigManager()
        config.set("services.cache.type", "file")
        config.set("services.cache.file.directory", temp_dir)
        
        cache = CachingService(config)
        
        yield cache
        
        # Cleanup
        cache.clear()
        os.rmdir(temp_dir)
    
    def test_set_get_basic(self, memory_cache):
        """Test basic set and get operations."""
        # Set a value
        memory_cache.set("test_key", "test_value")
        
        # Get the value
        value = memory_cache.get("test_key")
        assert value == "test_value"
        
        # Get a non-existent key
        value = memory_cache.get("non_existent_key")
        assert value is None
        
        # Get with default value
        value = memory_cache.get("non_existent_key", "default_value")
        assert value == "default_value"
    
    def test_set_get_with_ttl(self, memory_cache):
        """Test TTL (time-to-live) functionality."""
        # Set with short TTL
        memory_cache.set("ttl_key", "ttl_value", ttl=1)
        
        # Get immediately
        value = memory_cache.get("ttl_key")
        assert value == "ttl_value"
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Get after TTL expiration
        value = memory_cache.get("ttl_key")
        assert value is None
    
    def test_set_get_complex_data(self, memory_cache):
        """Test caching complex data structures."""
        # Dictionary
        dict_data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        memory_cache.set("dict_key", dict_data)
        assert memory_cache.get("dict_key") == dict_data
        
        # List
        list_data = [1, "string", {"key": "value"}, [4, 5, 6]]
        memory_cache.set("list_key", list_data)
        assert memory_cache.get("list_key") == list_data
    
    def test_delete(self, memory_cache):
        """Test delete operation."""
        # Set values
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        
        # Verify values exist
        assert memory_cache.get("key1") == "value1"
        assert memory_cache.get("key2") == "value2"
        
        # Delete one key
        memory_cache.delete("key1")
        
        # Verify only that key is gone
        assert memory_cache.get("key1") is None
        assert memory_cache.get("key2") == "value2"
    
    def test_clear(self, memory_cache):
        """Test clear operation."""
        # Set values
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        
        # Verify values exist
        assert memory_cache.get("key1") == "value1"
        assert memory_cache.get("key2") == "value2"
        
        # Clear cache
        memory_cache.clear()
        
        # Verify all keys are gone
        assert memory_cache.get("key1") is None
        assert memory_cache.get("key2") is None
    
    def test_has_key(self, memory_cache):
        """Test has_key operation."""
        # Set a value
        memory_cache.set("test_key", "test_value")
        
        # Check existing key
        assert memory_cache.has_key("test_key") is True
        
        # Check non-existent key
        assert memory_cache.has_key("non_existent_key") is False
    
    def test_file_backend(self, file_cache):
        """Test file-based cache backend."""
        # Set values
        file_cache.set("file_key1", "file_value1")
        file_cache.set("file_key2", {"nested": "data"})
        
        # Get values
        assert file_cache.get("file_key1") == "file_value1"
        assert file_cache.get("file_key2") == {"nested": "data"}
        
        # Delete value
        file_cache.delete("file_key1")
        assert file_cache.get("file_key1") is None
        assert file_cache.get("file_key2") == {"nested": "data"}
        
        # Clear cache
        file_cache.clear()
        assert file_cache.get("file_key2") is None
    
    def test_get_or_set(self, memory_cache):
        """Test get_or_set operation."""
        # Define a function that returns a computed value
        def compute_value():
            return "computed_value"
        
        # First call should compute the value
        value = memory_cache.get_or_set("compute_key", compute_value)
        assert value == "computed_value"
        
        # Second call should return the cached value
        value = memory_cache.get_or_set("compute_key", lambda: "new_value")
        assert value == "computed_value"  # Still the original value