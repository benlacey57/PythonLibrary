import os
import json
from pathlib import Path

class ConfigManager:
    """
    Manages application configuration from multiple sources with fallback support.
    
    Handles loading configuration from multiple JSON files, environment variables,
    and supports hierarchical overrides between test and live environments.
    """
    
    def __init__(self, config_dir=None, environment=None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_dir (str, optional): Directory containing configuration files.
            environment (str, optional): Current environment ('test', 'dev', 'prod', etc.)
                                         Defaults to value of PYTHON_ENV environment variable
                                         or 'prod' if not set.
        """
        self._config = {}
        self._config_dir = Path(config_dir) if config_dir else None
        self._environment = environment or os.environ.get('PYTHON_ENV', 'prod')
        
        # Load configuration files in order if config_dir is provided
        if self._config_dir and self._config_dir.exists():
            self._load_configuration_hierarchy()
    
    def _load_configuration_hierarchy(self):
        """
        Load configuration files in hierarchical order:
        1. base.json (common settings)
        2. {environment}.json (environment-specific settings)
        3. local.json (developer-specific overrides, not in version control)
        """
        # Base configuration (common settings)
        base_config = self._config_dir / 'base.json'
        if base_config.exists():
            self.load_from_file(base_config)
            
        # Environment-specific configuration
        env_config = self._config_dir / f'{self._environment}.json'
        if env_config.exists():
            self.load_from_file(env_config)
            
        # Local development overrides (gitignored)
        local_config = self._config_dir / 'local.json'
        if local_config.exists():
            self.load_from_file(local_config)
            
        # Finally, load from environment variables
        self.load_from_env()
    
    def load_from_file(self, file_path):
        """
        Load configuration from a JSON file.
        
        Args:
            file_path (str or Path): Path to the JSON configuration file.
            
        Returns:
            bool: True if the file was loaded successfully, False otherwise.
        """
        try:
            file_path = Path(file_path)
            with open(file_path, 'r') as f:
                file_config = json.load(f)
                self._merge_config(file_config)
            return True
        except (json.JSONDecodeError, FileNotFoundError) as e:
            # In a real implementation, we would log this error
            return False
    
    def load_from_env(self, prefix=None):
        """
        Load configuration from environment variables.
        
        Environment variables are converted to nested configuration using
        underscores as separators. For example, APP_NAME becomes app.name.
        
        Args:
            prefix (str, optional): Only load variables starting with this prefix.
        """
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
                
            # Convert environment variable name to config key
            # e.g., APP_NAME -> app.name
            config_key = key.lower().replace('_', '.')
            
            # Try to convert value to appropriate type (bool, int, float)
            if value.lower() in ('true', 'yes', '1'):
                value = True
            elif value.lower() in ('false', 'no', '0'):
                value = False
            else:
                try:
                    # Try to convert to int or float
                    if value.isdigit():
                        value = int(value)
                    else:
                        value = float(value)
                except ValueError:
                    # Keep as string
                    pass
                    
            self.set(config_key, value)
    
    def get(self, key, default=None):
        """
        Get a configuration value using dot notation.
        
        Args:
            key (str): Configuration key using dot notation (e.g., "app.name").
            default: Value to return if the key is not found.
            
        Returns:
            The configuration value or the default if not found.
        """
        parts = key.split('.')
        current = self._config
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
            
        return current
    
    def set(self, key, value):
        """
        Set a configuration value using dot notation.
        
        Args:
            key (str): Configuration key using dot notation (e.g., "app.name").
            value: Value to set.
        """
        parts = key.split('.')
        current = self._config
        
        # Navigate to the innermost dictionary
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
            
        # Set the value
        current[parts[-1]] = value
    
    def is_test_environment(self):
        """Check if current environment is a test environment."""
        return self._environment == 'test'
    
    def get_environment(self):
        """Get current environment name."""
        return self._environment
        
    def _merge_config(self, new_config, target=None, path=None):
        """
        Recursively merge configuration dictionaries.
        
        Args:
            new_config (dict): New configuration to merge.
            target (dict, optional): Target dictionary to merge into.
            path (str, optional): Current path for logging.
        """
        if target is None:
            target = self._config
            
        for key, value in new_config.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively merge nested dictionaries
                self._merge_config(value, target[key], f"{path}.{key}" if path else key)
            else:
                # Set or override value
                target[key] = value