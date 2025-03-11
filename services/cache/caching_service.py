import os
import time
import json
import hashlib
import pickle
from pathlib import Path
from typing import Any, Optional, Callable, Dict, Union

from core.base.base_service import BaseService
from core.interfaces.configurable import Configurable
from core.interfaces.loggable import Loggable

class CachingService(BaseService, Configurable, Loggable):
    """
    Service for caching data with different backend options.
    
    Supports memory, file, and potentially other backend types.
    """
    
    def __init__(self, config=None):
        """
        Initialize the CachingService.
        
        Args:
            config: Configuration for the service.
        """
        self.configure(config)
        self.initialize_logger("caching_service")
        
        self._cache_type = self.config.get("services.cache.type", "memory").lower()
        self._initialize_backend()
    
    def _initialize_backend(self):
        """
        Initialize the appropriate cache backend based on configuration.
        """
        if self._cache_type == "memory":
            self._backend = MemoryCacheBackend()
        elif self._cache_type == "file":
            directory = self.config.get("services.cache.file.directory")
            if not directory:
                self.logger.warning("No cache directory specified, using temporary directory")
                import tempfile
                directory = tempfile.gettempdir()
            
            self._backend = FileCacheBackend(directory)
        else:
            self.logger.warning(f"Unknown cache type '{self._cache_type}', falling back to memory cache")
            self._backend = MemoryCacheBackend()
            
        self.logger.info(f"Initialized {self._cache_type} cache backend")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.
        """
        try:
            self._backend.set(key, value, ttl)
            self.logger.debug(f"Set cache key: {key}")
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {str(e)}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            default: Value to return if key is not found.
            
        Returns:
            Cached value or default.
        """
        try:
            value = self._backend.get(key)
            if value is None:
                return default
            return value
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {str(e)}")
            return default
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            bool: True if key was found and deleted, False otherwise.
        """
        try:
            result = self._backend.delete(key)
            if result:
                self.logger.debug(f"Deleted cache key: {key}")
            return result
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        try:
            self._backend.clear()
            self.logger.debug("Cleared cache")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
    
    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            bool: True if key exists, False otherwise.
        """
        try:
            return self._backend.has_key(key)
        except Exception as e:
            self.logger.error(f"Error checking cache key {key}: {str(e)}")
            return False
    
    def get_or_set(self, key: str, value_func: Callable[[], Any], 
                  ttl: Optional[int] = None) -> Any:
        """
        Get a value from the cache, or compute and set it if not found.
        
        Args:
            key: Cache key.
            value_func: Function to compute the value if not found.
            ttl: Time-to-live in seconds.
            
        Returns:
            Cached or computed value.
        """
        # Check if key exists in cache
        value = self.get(key)
        
        if value is None:
            # Compute value
            self.logger.debug(f"Computing value for cache key: {key}")
            value = value_func()
            
            # Store in cache
            self.set(key, value, ttl)
            
        return value