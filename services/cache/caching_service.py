# /home/{user}/scripts/python/library/services/cache/caching_service.py

import os
import time
import json
import pickle
import hashlib
import zlib
from pathlib import Path
from typing import Any, Optional, Callable, Dict, Union

from core.base.base_service import BaseService
from core.interfaces.configurable import Configurable
from core.interfaces.loggable import Loggable
from core.exceptions import CacheError, FileError

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
        
        # Compression settings
        self._compression_enabled = self.config.get("services.cache.compression.enabled", True)
        self._compression_level = self.config.get("services.cache.compression.level", 6)
        self._compression_threshold = self.config.get("services.cache.compression.threshold", 1024)  # 1KB
        
        self._initialize_backend()
    
    def _initialize_backend(self):
        """
        Initialize the appropriate cache backend based on configuration.
        """
        try:
            if self._cache_type == "memory":
                self._backend = MemoryCacheBackend(
                    max_size=self.config.get("services.cache.memory.max_size", 1000),
                    compressor=self._create_compressor()
                )
            elif self._cache_type == "file":
                directory = self.config.get("services.cache.file.directory")
                if not directory:
                    self.logger.warning("No cache directory specified, using temporary directory")
                    import tempfile
                    directory = tempfile.gettempdir()
                
                max_size = self.config.get("services.cache.file.max_size_mb", 100) * 1024 * 1024  # Convert to bytes
                
                self._backend = FileCacheBackend(
                    directory,
                    max_size=max_size,
                    compressor=self._create_compressor()
                )
            else:
                self.logger.warning(f"Unknown cache type '{self._cache_type}', falling back to memory cache")
                self._backend = MemoryCacheBackend(compressor=self._create_compressor())
                
            self.logger.info(f"Initialized {self._cache_type} cache backend")
        except Exception as e:
            self.logger.error(f"Error initializing cache backend: {str(e)}")
            raise CacheError(f"Failed to initialize cache: {str(e)}")
    
    def _create_compressor(self):
        """
        Create a data compressor based on configuration.
        
        Returns:
            Compressor instance or None if compression is disabled.
        """
        if not self._compression_enabled:
            return None
            
        return ZlibCompressor(
            level=self._compression_level,
            threshold=self._compression_threshold
        )
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.
            
        Raises:
            CacheError: If setting the cache value fails.
        """
        try:
            self._backend.set(key, value, ttl)
            self.logger.debug(f"Set cache key: {key}")
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {str(e)}")
            raise CacheError(f"Failed to set cache value: {str(e)}", cache_key=key)
    
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
            
        Raises:
            CacheError: If deleting the cache value fails.
        """
        try:
            result = self._backend.delete(key)
            if result:
                self.logger.debug(f"Deleted cache key: {key}")
            return result
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {str(e)}")
            raise CacheError(f"Failed to delete cache value: {str(e)}", cache_key=key)
    
    def clear(self) -> None:
        """
        Clear all values from the cache.
        
        Raises:
            CacheError: If clearing the cache fails.
        """
        try:
            self._backend.clear()
            self.logger.debug("Cleared cache")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            raise CacheError(f"Failed to clear cache: {str(e)}")
    
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
            
        Raises:
            CacheError: If getting or setting the cache value fails.
        """
        # Check if key exists in cache
        value = self.get(key)
        
        if value is None:
            # Compute value
            self.logger.debug(f"Computing value for cache key: {key}")
            
            try:
                value = value_func()
            except Exception as e:
                self.logger.error(f"Error computing value for cache key {key}: {str(e)}")
                raise CacheError(f"Failed to compute cache value: {str(e)}", cache_key=key)
            
            # Store in cache
            self.set(key, value, ttl)
            
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            dict: Cache statistics.
        """
        try:
            return self._backend.get_stats()
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {str(e)}")
            return {}


class ZlibCompressor:
    """
    Compressor using zlib for efficient data storage.
    """
    
    def __init__(self, level=6, threshold=1024):
        """
        Initialize the compressor.
        
        Args:
            level: Compression level (1-9, 9 being highest).
            threshold: Size threshold in bytes for compression.
        """
        self.level = level
        self.threshold = threshold
    
    def compress(self, data):
        """
        Compress data if it exceeds the threshold size.
        
        Args:
            data: Data to compress.
            
        Returns:
            tuple: (compressed_data, is_compressed).
        """
        # Only compress if data is large enough
        if len(data) < self.threshold:
            return data, False
            
        compressed = zlib.compress(data, self.level)
        
        # Only use compressed data if it's smaller
        if len(compressed) < len(data):
            return compressed, True
        else:
            return data, False
    
    def decompress(self, data, is_compressed):
        """
        Decompress data if it was compressed.
        
        Args:
            data: Data to decompress.
            is_compressed: Whether the data is compressed.
            
        Returns:
            Decompressed data.
        """
        if is_compressed:
            return zlib.decompress(data)
        else:
            return data


class MemoryCacheBackend:
    """
    Memory-based cache backend with LRU eviction.
    """
    
    def __init__(self, max_size=1000, compressor=None):
        """
        Initialize the memory cache.
        
        Args:
            max_size: Maximum number of items to store.
            compressor: Optional data compressor.
        """
        self._cache = {}  # key -> (value, expiry_time, last_access_time, serialized_size)
        self._max_size = max_size
        self._compressor = compressor
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.
        """
        # Check if we need to evict items
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._evict_items()
            
        # Calculate expiry time
        expiry_time = None
        if ttl is not None:
            expiry_time = time.time() + ttl
            
        # Serialize and compress the value
        serialized = pickle.dumps(value)
        size = len(serialized)
        
        if self._compressor:
            serialized, is_compressed = self._compressor.compress(serialized)
        else:
            is_compressed = False
            
        # Store in cache
        self._cache[key] = (
            serialized,
            expiry_time,
            time.time(),  # Last access time
            is_compressed,
            size  # Original size for stats
        )
        
        # Update stats
        self._stats["size"] += size
    
    def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found or expired.
        """
        if key not in self._cache:
            self._stats["misses"] += 1
            return None
            
        serialized, expiry_time, last_access, is_compressed, _ = self._cache[key]
        
        # Check if expired
        if expiry_time is not None and time.time() > expiry_time:
            del self._cache[key]
            self._stats["misses"] += 1
            return None
            
        # Update last access time
        self._cache[key] = (serialized, expiry_time, time.time(), is_compressed, _)
        
        # Decompress and deserialize
        if self._compressor:
            serialized = self._compressor.decompress(serialized, is_compressed)
            
        # Update stats
        self._stats["hits"] += 1
        
        # Return deserialized value
        return pickle.loads(serialized)
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            bool: True if key was found and deleted, False otherwise.
        """
        if key in self._cache:
            _, _, _, _, size = self._cache[key]
            del self._cache[key]
            self._stats["size"] -= size
            return True
        return False
    
    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        self._cache.clear()
        self._stats["size"] = 0
    
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
            
        _, expiry_time, _, _, _ = self._cache[key]
        
        # Check if expired
        if expiry_time is not None and time.time() > expiry_time:
            del self._cache[key]
            return False
            
        return True
    
    def _evict_items(self) -> None:
        """
        Evict least recently used items from the cache.
        """
        # Sort items by last access time
        items = list(self._cache.items())
        items.sort(key=lambda x: x[1][2])  # Sort by last access time
        
        # Evict oldest 10% of items
        num_to_evict = max(1, len(items) // 10)
        
        for i in range(num_to_evict):
            if i < len(items):
                key, (_, _, _, _, size) = items[i]
                if key in self._cache:
                    del self._cache[key]
                    self._stats["size"] -= size
                    self._stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            dict: Cache statistics.
        """
        return {
            "type": "memory",
            "items": len(self._cache),
            "max_items": self._max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "size_bytes": self._stats["size"],
            "compression": self._compressor is not None
        }


class FileCacheBackend:
    """
    File-based cache backend.
    """
    
    def __init__(self, directory: str, max_size=100*1024*1024, compressor=None):
        """
        Initialize the file cache.
        
        Args:
            directory: Directory to store cache files.
            max_size: Maximum cache size in bytes.
            compressor: Optional data compressor.
        """
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._max_size = max_size
        self._compressor = compressor
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
        
        # Initialize stats
        self._update_size_stats()
    
    def _update_size_stats(self):
        """Update cache size statistics."""
        total_size = 0
        for cache_file in self._directory.glob("*.cache"):
            try:
                total_size += cache_file.stat().st_size
            except:
                pass
        
        self._stats["size"] = total_size
    
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
            
        Raises:
            CacheError: If writing to the cache file fails.
        """
        cache_path = self._get_cache_path(key)
        
        # Check cache size and evict if necessary
        if self._stats["size"] > self._max_size:
            self._evict_items()
            
        expiry_time = None
        if ttl is not None:
            expiry_time = int(time.time() + ttl)
            
        # Serialize the value
        try:
            serialized = pickle.dumps(value)
            original_size = len(serialized)
            
            # Compress if enabled
            if self._compressor:
                serialized, is_compressed = self._compressor.compress(serialized)
            else:
                is_compressed = False
                
            # Create metadata
            metadata = {
                "key": key,
                "expiry_time": expiry_time,
                "compressed": is_compressed,
                "original_size": original_size,
                "created": time.time()
            }
            
            # Write to file
            with open(cache_path, "wb") as f:
                # First write metadata length as 4 bytes
                metadata_bytes = json.dumps(metadata).encode()
                f.write(len(metadata_bytes).to_bytes(4, byteorder='little'))
                
                # Write metadata
                f.write(metadata_bytes)
                
                # Write data
                f.write(serialized)
                
            # Update stats
            file_size = cache_path.stat().st_size
            self._stats["size"] += file_size
            
        except Exception as e:
            raise CacheError(f"Failed to write cache file: {str(e)}", cache_key=key)
    
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
            self._stats["misses"] += 1
            return None
            
        try:
            with open(cache_path, "rb") as f:
                # Read metadata length
                metadata_length_bytes = f.read(4)
                if not metadata_length_bytes:
                    self.delete(key)
                    self._stats["misses"] += 1
                    return None
                    
                metadata_length = int.from_bytes(metadata_length_bytes, byteorder='little')
                
                # Read metadata
                metadata_bytes = f.read(metadata_length)
                metadata = json.loads(metadata_bytes.decode())
                
                # Check if expired
                expiry_time = metadata.get("expiry_time")
                if expiry_time is not None and time.time() > expiry_time:
                    self.delete(key)
                    self._stats["misses"] += 1
                    return None
                    
                # Read data
                serialized = f.read()
                
                # Decompress if necessary
                if metadata.get("compressed"):
                    if self._compressor:
                        serialized = self._compressor.decompress(serialized, True)
                    else:
                        # Fall back if compressor not available but data is compressed
                        serialized = zlib.decompress(serialized)
                        
                # Update access time
                cache_path.touch()
                
                # Update stats
                self._stats["hits"] += 1
                
                # Return deserialized value
                return pickle.loads(serialized)
                
        except (pickle.PickleError, IOError, EOFError, json.JSONDecodeError) as e:
            # If file is corrupted, remove it
            self.delete(key)
            self._stats["misses"] += 1
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
                # Get file size for stats update
                file_size = cache_path.stat().st_size
                
                # Delete the file
                cache_path.unlink()
                
                # Update stats
                self._stats["size"] -= file_size
                
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
                
        # Reset stats
        self._stats["size"] = 0
    
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
                # Read metadata length
                metadata_length_bytes = f.read(4)
                if not metadata_length_bytes:
                    self.delete(key)
                    return False
                    
                metadata_length = int.from_bytes(metadata_length_bytes, byteorder='little')
                
                # Read metadata
                metadata_bytes = f.read(metadata_length)
                metadata = json.loads(metadata_bytes.decode())
                
                # Check if expired
                expiry_time = metadata.get("expiry_time")
                if expiry_time is not None and time.time() > expiry_time:
                    self.delete(key)
                    return False
                    
                return True
        except:
            # If file is corrupted, remove it
            self.delete(key)
            return False
    
    def _evict_items(self) -> None:
        """
        Evict least recently used items from the cache.
        """
        try:
            # Get all cache files with their access times
            cache_files = []
            for cache_file in self._directory.glob("*.cache"):
                try:
                    # Use both modified time and access time
                    atime = cache_file.stat().st_atime
                    mtime = cache_file.stat().st_mtime
                    # Use the more recent of the two
                    time_val = max(atime, mtime)
                    size = cache_file.stat().st_size
                    cache_files.append((cache_file, time_val, size))
                except:
                    continue
                    
            # Sort by access time (oldest first)
            cache_files.sort(key=lambda x: x[1])
            
            # Calculate how much space to free (aim to get to 75% of max)
            target_size = self._max_size * 0.75
            space_to_free = max(0, self._stats["size"] - target_size)
            freed_space = 0
            
            # Delete files until we've freed enough space
            for cache_file, _, size in cache_files:
                if freed_space >= space_to_free:
                    break
                    
                try:
                    cache_file.unlink()
                    freed_space += size
                    self._stats["evictions"] += 1
                except:
                    continue
                    
            # Update size stats
            self._update_size_stats()
            
        except Exception as e:
            # If eviction fails, just log and continue
            pass
    
    def get_stats(self) -> Dict[str, Any]:
       """
       Get cache statistics.
       
       Returns:
           dict: Cache statistics.
       """
       return {
           "type": "file",
           "directory": str(self._directory),
           "size_bytes": self._stats["size"],
           "max_size_bytes": self._max_size,
           "hits": self._stats["hits"],
           "misses": self._stats["misses"],
           "evictions": self._stats["evictions"],
           "usage_percent": (self._stats["size"] / self._max_size) * 100 if self._max_size > 0 else 0,
           "compression": self._compressor is not None
       }