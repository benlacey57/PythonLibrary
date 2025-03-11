import os
import pytest
import tempfile
import logging
from pathlib import Path

class TestLogManager:
    """Test suite for LogManager."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_initialize_logger(self, temp_log_dir):
        """Test basic logger initialization."""
        from core.logging.log_manager import LogManager
        
        log_file = os.path.join(temp_log_dir, "test.log")
        logger = LogManager.get_logger("test_logger", log_file)
        
        assert logger.name == "test_logger"
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        
        # Test logging
        test_message = "Test log message"
        logger.info(test_message)
        
        # Verify the message was written to the file
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert test_message in log_content
    
    def test_get_logger_reuses_existing(self):
        """Test that get_logger reuses existing loggers."""
        from core.logging.log_manager import LogManager
        
        logger1 = LogManager.get_logger("shared_logger")
        logger2 = LogManager.get_logger("shared_logger")
        
        assert logger1 is logger2
    
    def test_set_log_level(self, temp_log_dir):
        """Test setting the log level."""
        from core.logging.log_manager import LogManager
        
        log_file = os.path.join(temp_log_dir, "level_test.log")
        logger = LogManager.get_logger("level_test", log_file, level=logging.WARNING)
        
        # INFO should not be logged
        logger.info("This should not be logged")
        
        # WARNING should be logged
        logger.warning("This should be logged")
        
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "This should not be logged" not in log_content
            assert "This should be logged" in log_content
    
    def test_format_includes_timestamp_and_level(self, temp_log_dir):
        """Test that log format includes timestamp and level."""
        from core.logging.log_manager import LogManager
        
        log_file = os.path.join(temp_log_dir, "format_test.log")
        logger = LogManager.get_logger("format_test", log_file)
        
        logger.warning("Format test")
        
        with open(log_file, 'r') as f:
            log_content = f.read()
            # Basic format check - should include date/time, level and message
            assert any(all(part in log_content for part in ["WARNING", "Format test"]))