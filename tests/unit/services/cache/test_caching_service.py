import os
import time
import pytest
import tempfile
from pathlib import Path
import random
import string

from core.exceptions import CacheError

class TestCachingService:
    """Test suite for CachingService."""
    
    @pytest.fixture
    def memory_cache(self):
        """Create a CachingService with memory backend."""
        from services.cache import CachingService
        from core.config import ConfigManager
        
        config = ConfigManager()
        config.set("services.cache.type", "memory")
        config.set("services.cache.compression.enabled", True)
        config.set("services.cache.compression.threshold", 100)  # Low threshold for testing
        config.set("services.cache.memory.max_size", 10)  # Small size to test eviction
        
        return CachingService(config)
    
    @pytest.fixture
    def file_cache(self):
        """Create a CachingService with file backend."""
        from services.cache import CachingService
        from core.config import ConfigManager
        
        temp_dir = tempfile.mkdtemp()
        
        config = ConfigManager()
        config.set("services.cache.type", "file")
        config.set("services.cache.file.directory", temp_dir)
        config.set("services.cache.file.max_size_mb", 1)  # 1MB max size
        config.set("services.cache.compression.enabled", True)
        
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
        
        # Custom class
        class TestClass:
            def __init__(self, name):
                self.name = name
                
            def __eq__(self, other):
                return isinstance(other, TestClass) and self.name == other.name
                
        obj = TestClass("test_object")
        memory_cache.set("obj_key", obj)
        
        retrieved = memory_cache.get("obj_key")
        assert retrieved == obj
        assert retrieved.name == "test_object"
    
    def test_delete(self, memory_cache):
        """Test delete operation."""
        # Set values
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        
        # Verify values exist
        assert memory_cache.get("key1") == "value1"
        assert memory_cache.get("key2") == "value2"
        
        # Delete one key
        result = memory_cache.delete("key1")
        
        # Verify only that key is gone
        assert result is True
        assert memory_cache.get("key1") is None
        assert memory_cache.get("key2") == "value2"
        
        # Delete non-existent key
        result = memory_cache.delete("nonexistent")
        assert result is False
    
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
        
        # Set with TTL and check after expiration
        memory_cache.set("ttl_key", "ttl_value", ttl=1)
        assert memory_cache.has_key("ttl_key") is True
        
        time.sleep(1.1)
        
        assert memory_cache.has_key("ttl_key") is False
    
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
        call_count = 0
        
        # Define a function that returns a computed value and tracks calls
        def compute_value():
            nonlocal call_count
            call_count += 1
            return f"computed_value_{call_count}"
        
        # First call should compute the value
        value = memory_cache.get_or_set("compute_key", compute_value)
        assert value == "computed_value_1"
        assert call_count == 1
        
        # Second call should return the cached value
        value = memory_cache.get_or_set("compute_key", compute_value)
        assert value == "computed_value_1"  # Still the original value
        assert call_count == 1  # Function not called again
        
        # After expiration, should recompute
        memory_cache.set("compute_key", "old_value", ttl=1)
        time.sleep(1.1)
        
        value = memory_cache.get_or_set("compute_key", compute_value)
        assert value == "computed_value_2"  # New computed value
        assert call_count == 2  # Function called again
    
    def test_error_handling(self, memory_cache):
        """Test error handling in cache operations."""
        # Test error in compute function
        def failing_compute():
            raise ValueError("Compute function failed")
            
        with pytest.raises(CacheError) as exc_info:
            memory_cache.get_or_set("error_key", failing_compute)
            
        assert "Failed to compute cache value" in str(exc_info.value)
        assert exc_info.value.cache_key == "error_key"
    
    def test_memory_eviction(self, memory_cache):
        """Test LRU eviction in memory cache."""
        # Fill cache beyond its max size
        for i in range(15):  # Max size is 10
            memory_cache.set(f"key{i}", f"value{i}")
            
        # Some of the earliest keys should be evicted
        for i in range(5):
            assert memory_cache.get(f"key{i}") is None
            
        # Later keys should still be there
        for i in range(10, 15):
            assert memory_cache.get(f"key{i}") == f"value{i}"
            
        # Get stats
        stats = memory_cache._backend.get_stats()
        assert stats["evictions"] > 0
    
    def test_file_eviction(self, file_cache):
        """Test size-based eviction in file cache."""
        # Generate large data to trigger eviction
        def generate_data(size_kb):
            # Generate random string data of specified size
            return ''.join(random.choice(string.ascii_letters) for _ in range(size_kb * 1024))
            
        # Add files until we trigger eviction
        for i in range(5):
            # Each file is about 200KB
            file_cache.set(f"large_key{i}", generate_data(200))
            
        # Get stats
        stats = file_cache._backend.get_stats()
        
        # At least some evictions should have happened
        assert stats["evictions"] > 0
    
    def test_compression(self, memory_cache):
        """Test data compression for large values."""
        # Create compressible data (repeated patterns compress well)
        data = "abcdefghijklmnopqrstuvwxyz" * 100  # 2600 bytes, well over threshold
        
        # Set in cache
        memory_cache.set("compressed_key", data)
        
        # Get back and verify
        retrieved = memory_cache.get("compressed_key")
        assert retrieved == data
        
        # Verify storage was compressed
        stats = memory_cache._backend.get_stats()
        assert stats["compression"] is True
    
    def test_cache_stats(self, memory_cache, file_cache):
       """Test cache statistics."""
       # Exercise memory cache
       memory_cache.set("stats_key1", "value1")
       memory_cache.set("stats_key2", "value2")
       
       memory_cache.get("stats_key1")  # Hit
       memory_cache.get("nonexistent")  # Miss
       
       # Get memory stats
       mem_stats = memory_cache._backend.get_stats()
       
       assert mem_stats["type"] == "memory"
       assert mem_stats["hits"] == 1
       assert mem_stats["misses"] == 1
       assert mem_stats["items"] == 2
       
       # Exercise file cache
       file_cache.set("file_stats1", "value1")
       file_cache.get("file_stats1")  # Hit
       file_cache.get("nonexistent")  # Miss
       
       # Get file stats
       file_stats = file_cache._backend.get_stats()
       
       assert file_stats["type"] == "file"
       assert file_stats["hits"] == 1
       assert file_stats["misses"] == 1
       assert "directory" in file_stats
       assert "usage_percent" in file_stats