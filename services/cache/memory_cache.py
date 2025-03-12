import time
from typing import Any, Optional
from python_library.services.cache.caching_service import CachingService

class MemoryCacheBackend(CachingService):
    """
    Memory-based cache backend.
    """
    
    def __init__(self):
        """
        Initialize the memory cache.
        """
        self._cache = {}  # key -> (value, expiry_time)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.
        """
        expiry_time = None
        if ttl is not None:
            expiry_time = time.time() + ttl
            
        self._cache[key] = (value, expiry_time)
    
    def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found or expired.
        """
        if key not in self._cache:
            return None
            
        value, expiry_time = self._cache[key]
        
        # Check if expired
        if expiry_time is not None and time.time() > expiry_time:
            del self._cache[key]
            return None
            
        return value
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            bool: True if key was found and deleted, False otherwise.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        self._cache.clear()
    
    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            bool: True if key exists and is not expired, False otherwise.
        """
        if key not in self._cache:
            return False
            
        _, expiry_time = self._cache[key]
        
        # Check if expired
        if expiry_time is not None and time.time() > expiry_time:
            del self._cache[key]
            return False
            
        return True