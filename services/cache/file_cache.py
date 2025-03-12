import hashlib
import pickle
import time
from pathlib import Path
from typing import Any, Optional
from python_library.services.cache.caching_service import CachingService

class FileCacheBackend(CachingService):
    """
    File-based cache backend.
    """
    
    def __init__(self, directory: str):
        """
        Initialize the file cache.
        
        Args:
            directory: Directory to store cache files.
        """
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key.
            
        Returns:
            Path: Path to the cache file.
        """
        # Hash the key to create a safe filename
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return self._directory / f"{hashed_key}.cache"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.
        """
        cache_path = self._get_cache_path(key)
        
        expiry_time = None
        if ttl is not None:
            expiry_time = int(time.time() + ttl)
            
        # Create cache data structure
        cache_data = {
            "key": key,
            "value": value,
            "expiry_time": expiry_time
        }
        
        # Write to file
        with open(cache_path, "wb") as f:
            pickle.dump(cache_data, f)
    
    def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found or expired.
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, "rb") as f:
                cache_data = pickle.load(f)
                
            # Check if expired
            expiry_time = cache_data.get("expiry_time")
            if expiry_time is not None and time.time() > expiry_time:
                self.delete(key)
                return None
                
            return cache_data["value"]
        except (pickle.PickleError, IOError, EOFError):
            # If file is corrupted, remove it
            self.delete(key)
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            bool: True if key was found and deleted, False otherwise.
        """
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                cache_path.unlink()
                return True
            except IOError:
                return False
        return False
    
    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        for cache_file in self._directory.glob("*.cache"):
            try:
                cache_file.unlink()
            except IOError:
                pass
    
    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            bool: True if key exists and is not expired, False otherwise.
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return False
            
        try:
            with open(cache_path, "rb") as f:
                cache_data = pickle.load(f)
                
            # Check if expired
            expiry_time = cache_data.get("expiry_time")
            if expiry_time is not None and time.time() > expiry_time:
                self.delete(key)
                return False
                
            return True
        except (pickle.PickleError, IOError, EOFError):
            # If file is corrupted, remove it
            self.delete(key)
            return False