import os
import json
import pytest
import tempfile
from pathlib import Path

# Import will be available once we create the module
# from core.config.config_manager import ConfigManager

class TestConfigManager:
    """Test suite for ConfigManager."""
    
    @pytest.fixture
    def sample_config_file(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp:
            config = {
                "app": {
                    "name": "TestApp",
                    "version": "1.0.0"
                },
                "services": {
                    "google": {
                        "enabled": True
                    }
                }
            }
            json.dump(config, temp)
            temp_path = temp.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_load_config_from_file(self, sample_config_file):
        """Test loading configuration from a file."""
        from core.config.config_manager import ConfigManager
        
        config = ConfigManager()
        config.load_from_file(sample_config_file)
        
        assert config.get("app.name") == "TestApp"
        assert config.get("services.google.enabled") is True
    
    def test_get_nested_config_value(self, sample_config_file):
        """Test retrieving nested configuration values using dot notation."""
        from core.config.config_manager import ConfigManager
        
        config = ConfigManager()
        config.load_from_file(sample_config_file)
        
        assert config.get("app.version") == "1.0.0"
        assert config.get("services.google.enabled") is True
    
    def test_get_with_default_value(self):
        """Test retrieving non-existent value returns the default."""
        from core.config.config_manager import ConfigManager
        
        config = ConfigManager()
        assert config.get("non.existent.key", default="default_value") == "default_value"
    
    def test_set_config_value(self):
        """Test setting a configuration value."""
        from core.config.config_manager import ConfigManager
        
        config = ConfigManager()
        config.set("new.key", "new_value")
        
        assert config.get("new.key") == "new_value"
    
    def test_env_variable_override(self, monkeypatch):
        """Test environment variables override config values."""
        from core.config.config_manager import ConfigManager
        
        # Set environment variable
        monkeypatch.setenv("APP_NAME", "EnvApp")
        
        config = ConfigManager()
        config.set("app.name", "ConfigApp")
        config.load_from_env()
        
        assert config.get("app.name") == "EnvApp"