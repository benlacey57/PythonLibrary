class LibraryError(Exception):
    """Base exception for all library errors."""
    
    def __init__(self, message, error_code=None, details=None):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            error_code: Optional error code.
            details: Optional additional error details.
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        
        # Format the error message
        formatted_message = message
        if error_code:
            formatted_message = f"[{error_code}] {formatted_message}"
            
        super().__init__(formatted_message)


class ConfigurationError(LibraryError):
    """Error related to configuration issues."""
    
    def __init__(self, message, error_code=None, details=None):
        error_code = error_code or "CONFIG-001"
        super().__init__(message, error_code, details)


class ServiceError(LibraryError):
    """Base error for service-related issues."""
    
    def __init__(self, service_name, message, error_code=None, details=None):
        self.service_name = service_name
        error_code = error_code or "SERVICE-001"
        
        # Add service name to details
        details = details or {}
        details["service"] = service_name
        
        # Format message with service name
        full_message = f"{service_name}: {message}"
        
        super().__init__(full_message, error_code, details)


class ConnectionError(ServiceError):
    """Error connecting to an external service."""
    
    def __init__(self, service_name, message, error_code=None, details=None):
        error_code = error_code or "CONN-001"
        super().__init__(service_name, message, error_code, details)


class AuthenticationError(ServiceError):
    """Error authenticating with an external service."""
    
    def __init__(self, service_name, message, error_code=None, details=None):
        error_code = error_code or "AUTH-001"
        super().__init__(service_name, message, error_code, details)


class DataError(LibraryError):
    """Base error for data-related issues."""
    
    def __init__(self, message, error_code=None, details=None):
        error_code = error_code or "DATA-001"
        super().__init__(message, error_code, details)


class ValidationError(DataError):
    """Error validating data."""
    
    def __init__(self, message, field=None, error_code=None, details=None):
        self.field = field
        error_code = error_code or "VALID-001"
        
        # Add field to details
        details = details or {}
        if field:
            details["field"] = field
            message = f"{field}: {message}"
            
        super().__init__(message, error_code, details)


class FileError(LibraryError):
    """Base error for file-related issues."""
    
    def __init__(self, file_path, message, error_code=None, details=None):
        self.file_path = file_path
        error_code = error_code or "FILE-001"
        
        # Add file path to details
        details = details or {}
        details["file_path"] = str(file_path)
        
        # Format message with file path
        full_message = f"{file_path}: {message}"
        
        super().__init__(full_message, error_code, details)


class CacheError(ServiceError):
    """Error related to caching operations."""
    
    def __init__(self, message, cache_key=None, error_code=None, details=None):
        self.cache_key = cache_key
        error_code = error_code or "CACHE-001"
        
        # Add cache key to details
        details = details or {}
        if cache_key:
            details["cache_key"] = cache_key
            message = f"Cache key '{cache_key}': {message}"
            
        super().__init__("CachingService", message, error_code, details)


class DatabaseError(ServiceError):
    """Error related to database operations."""
    
    def __init__(self, message, query=None, error_code=None, details=None):
        self.query = query
        error_code = error_code or "DB-001"
        
        # Add query to details (but limit length for security)
        details = details or {}
        if query:
            if len(query) > 100:
                details["query"] = query[:100] + "..."
            else:
                details["query"] = query
            
        super().__init__("DatabaseClient", message, error_code, details)