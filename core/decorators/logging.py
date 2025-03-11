import functools
import inspect

def log_execution(logger):
    """
    Decorator that logs function execution.
    
    Args:
        logger: Logger instance to use for logging.
        
    Returns:
        Decorated function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get argument names and values for logging
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            arg_str = ", ".join(f"{key}={repr(value)}" 
                               for key, value in bound_args.arguments.items())
            
            logger.debug(f"Executing {func.__name__}({arg_str})")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {str(e)}")
                raise
                
        return wrapper
    return decorator