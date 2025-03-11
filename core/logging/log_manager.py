import os
import logging
from pathlib import Path

class LogManager:
    """
    Manages application logging.
    
    Provides centralized configuration for logging across the application
    with support for different log levels and output formats.
    """
    
    # Store configured loggers by name
    _loggers = {}
    
    # Default format includes timestamp, level, and message
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_logger(cls, name, log_file=None, level=logging.INFO, format_str=None):
        """
        Get or create a logger with the specified configuration.
        
        Args:
            name (str): Name of the logger.
            log_file (str, optional): Path to log file.
            level (int, optional): Logging level. Defaults to INFO.
            format_str (str, optional): Log format string.
            
        Returns:
            logging.Logger: Configured logger instance.
        """
        # Return existing logger if already configured
        if name in cls._loggers:
            return cls._loggers[name]
            
        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Clear any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Set format
        formatter = logging.Formatter(format_str or cls.DEFAULT_FORMAT)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Store logger
        cls._loggers[name] = logger
        return logger