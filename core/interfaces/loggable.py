from ..logging.log_manager import LogManager

class Loggable:
    """
    Interface for components that need logging.
    
    Provides standard methods for logger initialization and access.
    """
    
    def initialize_logger(self, name, log_file=None, level=None, format_str=None):
        """
        Initialize a logger for this component.
        
        Args:
            name (str): Logger name.
            log_file (str, optional): Path to log file.
            level (int, optional): Logging level.
            format_str (str, optional): Log format string.
        """
        import logging
        level = level or logging.INFO
        
        self.logger = LogManager.get_logger(name, log_file, level, format_str)