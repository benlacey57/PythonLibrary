import time
import logging
import functools
import signal
import threading
import json
import inspect
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

def cache(ttl=3600):
    """Cache function results with time-to-live."""
    def decorator(func):
        cache_data = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a key from the function arguments
            key = str(args) + str(sorted(kwargs.items()))
            
            # Check if result is in cache and not expired
            if key in cache_data:
                result, timestamp = cache_data[key]
                if datetime.now() - timestamp < timedelta(seconds=ttl):
                    return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_data[key] = (result, datetime.now())
            return result
        
        # Add function to clear cache
        def clear_cache():
            cache_data.clear()
        
        wrapper.clear_cache = clear_cache
        return wrapper
    return decorator