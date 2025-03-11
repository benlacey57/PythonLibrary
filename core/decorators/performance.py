import time
import functools

def performance_monitor(logger):
    """
    Decorator that monitors and logs function execution time.
    
    Args:
        logger: Logger instance to use for logging.
        
    Returns:
        Decorated function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
                
        return wrapper
    return decorator