import pytest
import time
import tempfile
import os

class TestDecorators:
    """Test suite for core decorators."""
    
    def test_log_execution_decorator(self):
        """Test the log_execution decorator."""
        from core.decorators.logging import log_execution
        from core.logging.log_manager import LogManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "decorator_test.log")
            logger = LogManager.get_logger("decorator_test", log_file)
            
            # Function with decorator
            @log_execution(logger)
            def test_function(a, b):
                return a + b
            
            # Call the function
            result = test_function(5, 3)
            assert result == 8
            
            # Verify the log contains function execution details
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert "Executing test_function" in log_content
                assert "test_function completed" in log_content
    
    def test_performance_monitor_decorator(self):
        """Test the performance_monitor decorator."""
        from core.decorators.performance import performance_monitor
        from core.logging.log_manager import LogManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "performance_test.log")
            logger = LogManager.get_logger("performance_test", log_file)
            
            # Function with decorator
            @performance_monitor(logger)
            def slow_function():
                time.sleep(0.1)  # Short delay for testing
                return "done"
            
            # Call the function
            result = slow_function()
            assert result == "done"
            
            # Verify the log contains timing information
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert "slow_function executed in" in log_content
                assert "seconds" in log_content