import pytest

class TestInterfaces:
    """Test suite for core interfaces."""
    
    def test_configurable_interface(self):
        """Test the Configurable interface."""
        from core.interfaces.configurable import Configurable
        from core.config.config_manager import ConfigManager
        
        # Create a concrete implementation of Configurable
        class ConfigurableService(Configurable):
            def __init__(self, config=None):
                self.configure(config)
            
            def get_config_value(self, key, default=None):
                return self.config.get(key, default)
        
        # Test with a ConfigManager
        config = ConfigManager()
        config.set("test.key", "test_value")
        
        service = ConfigurableService(config)
        assert service.get_config_value("test.key") == "test_value"
        
        # Test with a dictionary
        service = ConfigurableService({"test": {"key": "dict_value"}})
        assert service.get_config_value("test.key") == "dict_value"
        
        # Test with no config
        service = ConfigurableService()
        assert service.get_config_value("test.key") is None
    
    def test_loggable_interface(self):
        """Test the Loggable interface."""
        import tempfile
        import os
        from core.interfaces.loggable import Loggable
        
        # Create a concrete implementation of Loggable
        class LoggableService(Loggable):
            def __init__(self, log_file=None):
                self.initialize_logger("test_service", log_file)
            
            def perform_action(self):
                self.logger.info("Action performed")
                return "done"
        
        # Test with a log file
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            service = LoggableService(log_file)
            
            result = service.perform_action()
            assert result == "done"
            
            # Verify the log was written
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert "Action performed" in log_content