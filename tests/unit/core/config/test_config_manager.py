import os
import json
import pytest
from pathlib import Path
import core.config.config_manager as config_manager

class TestConfigManager:
    """Test suite for ConfigManager."""
    
    def __init__(self):
        self.config_manager = config_manager.ConfigManager()
    
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
                "port": 5432
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
            
        with open(config_path / "local.json", "w") as f:
            json.dump(local_config, f)
            
        return config_path
    
    def test_hierarchical_config_loading(self, config_dir, monkeypatch):
        """Test loading of configuration in hierarchical order."""
        
        # Set environment to test
        monkeypatch.setenv("PYTHON_ENV", "test")
        
        # Initialize ConfigManager with config directory
        config = self.config_manager(config_dir=config_dir)
        
        # Test environment override
        assert config.get("app.name") == "TestApp"
        
        # Test base config values that aren't overridden
        assert config.get("app.version") == "1.0.0"
        
        # Test merged values from multiple files
        assert config.get("database.host") == "localhost"
        assert config.get("database.name") == "test_db"
        assert config.get("database.user") == "dev_user"
    
    def test_environment_specific_loading(self, config_dir):
        """Test loading configuration specific to an environment."""
        # Test environment
        config_test = self.config_manager(config_dir=config_dir, environment="test")
        assert config_test.get("app.name") == "TestApp"
        
        # Prod environment (falls back to base since no prod.json exists)
        config_prod = self.config_manager(config_dir=config_dir, environment="prod")
        assert config_prod.get("app.name") == "BaseApp"
    
    def test_environment_detection(self, config_dir, monkeypatch):
        """Test environment detection from PYTHON_ENV variable."""
        # Set environment variable
        monkeypatch.setenv("PYTHON_ENV", "test")
        
        # Initialize without explicit environment
        config = self.config_manager(config_dir=config_dir)
        
        # Should detect test environment
        assert config.get_environment() == "test"
        assert config.is_test_environment() is True
    
    def test_env_variable_override(self, config_dir, monkeypatch):
        """Test environment variables override file-based config."""
        # Set environment variable
        monkeypatch.setenv("APP_NAME", "EnvApp")
        
        # Initialize with config dir
        config = self.config_manager(config_dir=config_dir, environment="test")
        
        # Environment variable should override file config
        assert config.get("app.name") == "EnvApp"
    
    def test_type_conversion_from_env(self, monkeypatch):
        """Test automatic type conversion from environment variables."""
        # Set various typed environment variables
        monkeypatch.setenv("SERVER_PORT", "8080")
        monkeypatch.setenv("FEATURE_ENABLED", "true")
        monkeypatch.setenv("TIMEOUT_SECONDS", "30.5")
        
        config = self.config_manager
        config.load_from_env()
        
        # Check type conversions
        assert config.get("server.port") == 8080
        assert isinstance(config.get("server.port"), int)
        
        assert config.get("feature.enabled") is True
        assert isinstance(config.get("feature.enabled"), bool)
        
        assert config.get("timeout.seconds") == 30.5
        assert isinstance(config.get("timeout.seconds"), float)