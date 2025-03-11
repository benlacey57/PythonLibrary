import os
import pytest
import json
import csv
from pathlib import Path

class TestFileClient:
    """Test suite for FileClient."""
    
    @pytest.fixture
    def file_client(self):
        """Create a FileClient instance for testing."""
        from services.storage.file_client import FileClient
        from core.config.config_manager import ConfigManager
        
        config = ConfigManager()
        return FileClient(config)
    
    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create a temporary directory for file operations."""
        return tmp_path
    
    def test_read_write_text_file(self, file_client, test_dir):
        """Test reading and writing text files."""
        # Define test file
        test_file = test_dir / "test.txt"
        test_content = "Hello, world!"
        
        # Write to file
        file_client.write_text(test_file, test_content)
        
        # Check file exists
        assert test_file.exists()
        
        # Read from file
        content = file_client.read_text(test_file)
        assert content == test_content
    
    def test_read_write_binary_file(self, file_client, test_dir):
        """Test reading and writing binary files."""
        # Define test file
        test_file = test_dir / "test.bin"
        test_content = b'\x00\x01\x02\x03'
        
        # Write to file
        file_client.write_binary(test_file, test_content)
        
        # Read from file
        content = file_client.read_binary(test_file)
        assert content == test_content
    
    def test_read_write_json_file(self, file_client, test_dir):
        """Test reading and writing JSON files."""
        # Define test file
        test_file = test_dir / "test.json"
        test_data = {"name": "Test", "value": 42, "items": [1, 2, 3]}
        
        # Write to file
        file_client.write_json(test_file, test_data)
        
        # Read from file
        data = file_client.read_json(test_file)
        assert data == test_data
    
    def test_read_write_csv_file(self, file_client, test_dir):
        """Test reading and writing CSV files."""
        # Define test file
        test_file = test_dir / "test.csv"
        headers = ["name", "age", "city"]
        rows = [
            ["Alice", "30", "New York"],
            ["Bob", "25", "Boston"],
            ["Charlie", "35", "Chicago"]
        ]
        
        # Write to file
        file_client.write_csv(test_file, rows, headers=headers)
        
        # Read from file
        data = file_client.read_csv(test_file)
        
        # Check headers
        assert data[0] == headers
        
        # Check data (excluding headers)
        assert data[1:] == rows
    
    def test_file_operations(self, file_client, test_dir):
        """Test file operations like copy, move, delete."""
        # Create a test file
        source_file = test_dir / "source.txt"
        file_client.write_text(source_file, "Test content")
        
        # Copy file
        dest_file = test_dir / "dest.txt"
        file_client.copy(source_file, dest_file)
        assert dest_file.exists()
        assert file_client.read_text(dest_file) == "Test content"
        
        # Move file
        moved_file = test_dir / "moved.txt"
        file_client.move(dest_file, moved_file)
        assert not dest_file.exists()
        assert moved_file.exists()
        
        # Delete file
        file_client.delete(moved_file)
        assert not moved_file.exists()
    
    def test_directory_operations(self, file_client, test_dir):
        """Test directory operations."""
        # Create directory
        new_dir = test_dir / "new_dir"
        file_client.create_directory(new_dir)
        assert new_dir.exists() and new_dir.is_dir()
        
        # Create a file in the directory
        test_file = new_dir / "test.txt"
        file_client.write_text(test_file, "Test content")
        
        # List directory
        files = file_client.list_directory(new_dir)
        assert len(files) == 1
        assert files[0].name == "test.txt"
        
        # Delete directory
        file_client.delete_directory(new_dir)
        assert not new_dir.exists()