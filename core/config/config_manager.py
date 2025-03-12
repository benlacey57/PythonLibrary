import os
import json
import base64
from pathlib import Path
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..exceptions import ConfigurationError

class ConfigManager:
    """
    Manages application configuration from multiple sources with security features.
    
    Handles loading configuration from JSON files, environment variables,
    supports hierarchical overrides, and provides encryption for sensitive values.
    """
    
    def __init__(self, config_dir=None, environment=None, encryption_key=None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_dir (str, optional): Directory containing configuration files.
            environment (str, optional): Current environment ('test', 'dev', 'prod', etc.)
                                         Defaults to value of PYTHON_ENV environment variable
                                         or 'prod' if not set.
            encryption_key (str, optional): Key for encrypting/decrypting sensitive values.
                                           If not provided, uses PYTHON_CONFIG_KEY env var.
        """
        self._config = {}
        self._config_dir = Path(config_dir) if config_dir else None
        self._environment = environment or os.environ.get('PYTHON_ENV', 'prod')
        
        # Set up encryption
        self._encryption_key = encryption_key or os.environ.get('PYTHON_CONFIG_KEY')
        self._cipher = None
        
        if self._encryption_key:
            self._setup_encryption()
        
        # Load configuration files in order if config_dir is provided
        if self._config_dir and self._config_dir.exists():
            self._load_configuration_hierarchy()
    
    def _setup_encryption(self):
        """
        Set up encryption for sensitive configuration values.
        """
        try:
            # Convert the key to bytes
            key_bytes = self._encryption_key.encode()
            
            # Use PBKDF2 to derive a secure key
            salt = b'python_library_salt'  # In production, this should be stored securely
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            
            # Generate the Fernet key
            key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
            self._cipher = Fernet(key)
        except Exception as e:
            raise ConfigurationError(f"Failed to set up encryption: {str(e)}")
    
    def _load_configuration_hierarchy(self):
        """
        Load configuration files in hierarchical order:
        1. base.json (common settings)
        2. {environment}.json (environment-specific settings)
        3. .env.{environment} (environment-specific env vars)
        4. local.json (developer-specific overrides, not in version control)
        5. .env.local (local environment overrides)
        """
        # Base configuration (common settings)
        base_config = self._config_dir / 'base.json'
        if base_config.exists():
            self.load_from_file(base_config)
            
        # Environment-specific configuration
        env_config = self._config_dir / f'{self._environment}.json'
        if env_config.exists():
            self.load_from_file(env_config)
            
        # Environment-specific .env file
        env_file = self._config_dir / f'.env.{self._environment}'
        if env_file.exists():
            self.load_from_dotenv(env_file)
            
        # Local development overrides (gitignored)
        local_config = self._config_dir / 'local.json'
        if local_config.exists():
            self.load_from_file(local_config)
            
        # Local .env overrides
        local_env = self._config_dir / '.env.local'
        if local_env.exists():
            self.load_from_dotenv(local_env)
            
        # Finally, load from environment variables
        self.load_from_env()
    
    def load_from_file(self, file_path: Union[str, Path]) -> bool:
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the JSON configuration file.
            
        Returns:
            bool: True if the file was loaded successfully, False otherwise.
            
        Raises:
            ConfigurationError: If the file cannot be read or parsed.
        """
        try:
            file_path = Path(file_path)
            with open(file_path, 'r') as f:
                file_config = json.load(f)
                self._merge_config(file_config)
            return True
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in config file: {str(e)}",
                "CONFIG-002",
                {"file": str(file_path), "position": f"line {e.lineno}, column {e.colno}"}
            )
        except FileNotFoundError:
            # Not raising an error for missing files - may be optional
            return False
        except Exception as e:
            raise ConfigurationError(
                f"Error loading config file: {str(e)}",
                "CONFIG-003",
                {"file": str(file_path)}
            )
    
    def load_from_dotenv(self, file_path: Union[str, Path]) -> bool:
        """
        Load configuration from a .env file.
        
        Args:
            file_path: Path to the .env file.
            
        Returns:
            bool: True if the file was loaded successfully, False otherwise.
            
        Raises:
            ConfigurationError: If the file cannot be read.
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False
                
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                        
                    # Parse key-value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value and value[0] == value[-1] and value[0] in ('"', "'"):
                            value = value[1:-1]
                            
                        # Set environment variable and config
                        os.environ[key] = value
                        
                        # Convert environment variable name to config key
                        # e.g., APP_NAME -> app.name
                        config_key = key.lower().replace('_', '.')
                        self.set(config_key, self._parse_value(value))
                        
            return True
        except Exception as e:
            raise ConfigurationError(
                f"Error loading .env file: {str(e)}",
                "CONFIG-004",
                {"file": str(file_path)}
            )
    
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
            
            # Parse and set the value
            self.set(config_key, self._parse_value(value))
    
    def _parse_value(self, value: str) -> Any:
        """
        Parse a string value to an appropriate type.
        
        Args:
            value: String value to parse.
            
        Returns:
            Parsed value with appropriate type.
        """
        # Boolean values
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
            
        # None values
        if value.lower() in ('null', 'none'):
            return None
            
        # Try numeric values
        try:
            # Integer
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                return int(value)
                
            # Float
            if '.' in value:
                return float(value)
        except ValueError:
            pass
            
        # Return as string
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key using dot notation (e.g., "app.name").
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
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key using dot notation (e.g., "app.name").
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
    
    def is_test_environment(self) -> bool:
        """
        Check if current environment is a test environment.
        
        Returns:
            bool: True if in test environment, False otherwise.
        """
        return self._environment == 'test'
    
    def get_environment(self) -> str:
        """
        Get current environment name.
        
        Returns:
            str: Environment name.
        """
        return self._environment
    
    def encrypt_value(self, value: str) -> str:
        """
        Encrypt a sensitive configuration value.
        
        Args:
            value: Value to encrypt.
            
        Returns:
            str: Encrypted value as a base64 string.
            
        Raises:
            ConfigurationError: If encryption is not set up.
        """
        if not self._cipher:
            raise ConfigurationError(
                "Encryption key not set. Please provide an encryption key.",
                "CONFIG-005"
            )
            
        try:
            # Encrypt the value
            encrypted = self._cipher.encrypt(value.encode())
            
            # Return as base64 string
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise ConfigurationError(
                f"Encryption failed: {str(e)}",
                "CONFIG-006"
            )
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt a sensitive configuration value.
        
        Args:
            encrypted_value: Encrypted value as a base64 string.
            
        Returns:
            str: Decrypted value.
            
        Raises:
            ConfigurationError: If decryption fails or key is not set.
        """
        if not self._cipher:
            raise ConfigurationError(
                "Encryption key not set. Please provide an encryption key.",
                "CONFIG-007"
            )
            
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value)
            
            # Decrypt the value
            decrypted = self._cipher.decrypt(encrypted_bytes)
            
            return decrypted.decode()
        except Exception as e:
            raise ConfigurationError(
                f"Decryption failed: {str(e)}",
                "CONFIG-008"
            )
    
    def get_encrypted(self, key: str, default: Any = None) -> str:
        """
        Get and decrypt a sensitive configuration value.
        
        Args:
            key: Configuration key using dot notation.
            default: Value to return if the key is not found.
            
        Returns:
            str: Decrypted value or default.
            
        Raises:
            ConfigurationError: If decryption fails.
        """
        encrypted_value = self.get(key)
        
        if encrypted_value is None:
            return default
            
        return self.decrypt_value(encrypted_value)
    
    def set_encrypted(self, key: str, value: str) -> None:
        """
        Encrypt and set a sensitive configuration value.
        
        Args:
            key: Configuration key using dot notation.
            value: Value to encrypt and store.
            
        Raises:
            ConfigurationError: If encryption fails.
        """
        encrypted_value = self.encrypt_value(value)
        self.set(key, encrypted_value)
        
    def _merge_config(self, new_config: Dict[str, Any], target: Optional[Dict[str, Any]] = None, 
                    path: Optional[str] = None) -> None:
        """
        Recursively merge configuration dictionaries.
        
        Args:
            new_config: New configuration to merge.
            target: Target dictionary to merge into.
            path: Current path for logging.
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