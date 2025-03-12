import os
import json
import pytest
import tempfile
from pathlib import Path

from core.exceptions import ConfigurationError

class TestConfigManager:
    """Test suite for ConfigManager."""
    
    @pytest.fixture
    def config_dir(self, tmp_path):
        """Create a temporary config directory with test files."""
        # Create base config
        base_config = {
            "app": {
                "name": "BaseApp",
                "version": "1.0.0"
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "encrypted": False
                }
            }
        }
        
        # Create test environment config
        test_config = {
            "app": {
                "name": "TestApp"
            },
            "database": {
                "name": "test_db"
            }
        }
        
        # Create prod environment config
        prod_config = {
            "app": {
                "name": "ProdApp"
            },
            "database": {
                "name": "prod_db"
            }
        }
        
        # Create local config
        local_config = {
            "database": {
                "user": "dev_user",
                "password": "dev_password"
            }
        }
        
        # Create directory and files
        config_path = tmp_path / "config"
        config_path.mkdir()
        
        with open(config_path / "base.json", "w") as f:
            json.dump(base_config, f)
            
        with open(config_path / "test.json", "w") as f:
            json.dump(test_config, f)
            
        with open(config_path / "prod.json", "w") as f:
            json.dump(prod_config, f)
            
        with open(config_path / "local.json", "w") as f:
            json.dump(local_config, f)
            
        # Create .env files
        with open(config_path / ".env.test", "w") as f:
            f.write("ENV_VAR1=test_value\n")
            f.write("ENV_VAR2=123\n")
            f.write("FEATURE_FLAG=true\n")
            
        with open(config_path / ".env.local", "w") as f:
            f.write("LOCAL_VAR=local_value\n")
            f.write("ENV_VAR1=local_override\n")
            
        return config_path
    
    def test_hierarchical_config_loading(self, config_dir, monkeypatch):
        """Test loading of configuration in hierarchical order."""
        from core.config import ConfigManager
        
        # Set environment to test
        monkeypatch.setenv("PYTHON_ENV", "test")
        
        # Initialize ConfigManager with config directory
        config = ConfigManager(config_dir=config_dir)
        
        # Test environment override
        assert config.get("app.name") == "TestApp"
        
        # Test .env file values
        assert config.get("env.var1") == "local_override"  # .env.local overrides .env.test
        assert config.get("env.var2") == 123  # Integer conversion
        assert config.get("feature.flag") is True  # Boolean conversion
        assert config.get("local.var") == "local_value"  # Local var
        
        # Test base config values that aren't overridden
        assert config.get("app.version") == "1.0.0"
        
        # Test merged values from multiple files
        assert config.get("database.host") == "localhost"
        assert config.get("database.name") == "test_db"
        assert config.get("database.user") == "dev_user"
    
    def test_environment_specific_loading(self, config_dir):
        """Test loading configuration specific to an environment."""
        from core.config import ConfigManager
        
        # Test environment
        config_test = ConfigManager(config_dir=config_dir, environment="test")
        assert config_test.get("app.name") == "TestApp"
        assert config_test.get("database.name") == "test_db"
        
        # Prod environment
        config_prod = ConfigManager(config_dir=config_dir, environment="prod")
        assert config_prod.get("app.name") == "ProdApp"
        assert config_prod.get("database.name") == "prod_db"
    
    def test_environment_detection(self, config_dir, monkeypatch):
        """Test environment detection from PYTHON_ENV variable."""
        from core.config import ConfigManager
        
        # Set environment variable
        monkeypatch.setenv("PYTHON_ENV", "test")
        
        # Initialize without explicit environment
        config = ConfigManager(config_dir=config_dir)
        
        # Should detect test environment
        assert config.get_environment() == "test"
        assert config.is_test_environment() is True
    
    def test_dotenv_loading(self, config_dir):
        """Test loading configuration from .env files."""
        from core.config import ConfigManager
        
        # Load with test environment
        config = ConfigManager(config_dir=config_dir, environment="test")
        
        # Check .env.test values
        assert config.get("env.var2") == 123
        assert config.get("feature.flag") is True
        
        # Load with explicit file
        config = ConfigManager()
        config.load_from_dotenv(config_dir / ".env.test")
        
        assert config.get("env.var1") == "test_value"
        assert config.get("env.var2") == 123
    
    def test_invalid_json_handling(self, tmp_path):
        """Test handling of invalid JSON files."""
        from core.config import ConfigManager
        
        # Create invalid JSON file
        invalid_path = tmp_path / "invalid.json"
        with open(invalid_path, "w") as f:
            f.write("{invalid json")
            
        # Loading should raise ConfigurationError
        config = ConfigManager()
        with pytest.raises(ConfigurationError) as exc_info:
            config.load_from_file(invalid_path)
            
        assert "Invalid JSON" in str(exc_info.value)
        assert exc_info.value.error_code == "CONFIG-002"
    
    def test_missing_file_handling(self, tmp_path):
        """Test handling of missing files."""
        from core.config import ConfigManager
        
        missing_path = tmp_path / "nonexistent.json"
        
        # Loading a missing file should return False, not raise an error
        config = ConfigManager()
        result = config.load_from_file(missing_path)
        
        assert result is False
    
    def test_type_conversion_from_env(self, monkeypatch):
        """Test automatic type conversion from environment variables."""
        from core.config import ConfigManager
        
        # Set various typed environment variables
        monkeypatch.setenv("INT_VAL", "8080")
        monkeypatch.setenv("BOOL_TRUE", "true")
        monkeypatch.setenv("BOOL_FALSE", "false")
        monkeypatch.setenv("FLOAT_VAL", "30.5")
        monkeypatch.setenv("NULL_VAL", "null")
        monkeypatch.setenv("NEG_INT", "-42")
        
        config = ConfigManager()
        config.load_from_env()
        
        # Check type conversions
        assert config.get("int.val") == 8080
        assert isinstance(config.get("int.val"), int)
        
        assert config.get("bool.true") is True
        assert isinstance(config.get("bool.true"), bool)
        
        assert config.get("bool.false") is False
        assert isinstance(config.get("bool.false"), bool)
        
        assert config.get("float.val") == 30.5
        assert isinstance(config.get("float.val"), float)
        
        assert config.get("null.val") is None
        
        assert config.get("neg.int") == -42
        assert isinstance(config.get("neg.int"), int)
    
    def test_encryption_decryption(self):
        """Test encryption and decryption of sensitive values."""
        from core.config import ConfigManager
        
        # Initialize with encryption key
        config = ConfigManager(encryption_key="test_encryption_key")
        
        # Encrypt a value
        password = "super_secret_password"
        encrypted = config.encrypt_value(password)
        
        # Value should be different
        assert encrypted != password
        
        # Decrypt should match original
        decrypted = config.decrypt_value(encrypted)
        assert decrypted == password
        
        # Test convenience methods
        config.set_encrypted("database.password", password)
        retrieved = config.get_encrypted("database.password")
        assert retrieved == password
        
        # Verify stored value is encrypted
        raw_value = config.get("database.password")
        assert raw_value != password
        
        # Test no encryption key
        config_no_key = ConfigManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_no_key.encrypt_value("test")
            
        assert "Encryption key not set" in str(exc_info.value)
        assert exc_info.value.error_code == "CONFIG-005"