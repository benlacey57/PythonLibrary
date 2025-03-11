import os
import csv
import json
import shutil
from pathlib import Path
from typing import Union, List, Dict, Any, Optional, BinaryIO, TextIO

from core.base.base_client import BaseClient
from core.interfaces.configurable import Configurable
from core.interfaces.loggable import Loggable

class FileClient(BaseClient, Configurable, Loggable):
    """
    Client for file system operations.
    
    Provides methods for reading, writing, and manipulating files and directories.
    """
    
    def __init__(self, config=None):
        """
        Initialize the FileClient.
        
        Args:
            config: Configuration for the client.
        """
        self.configure(config)
        self.initialize_logger("file_client")
    
    def read_text(self, path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        Read text from a file.
        
        Args:
            path: Path to the file.
            encoding: Text encoding to use.
            
        Returns:
            str: The contents of the file.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be read.
        """
        path = Path(path)
        self.logger.debug(f"Reading text file: {path}")
        
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {path}: {str(e)}")
            raise
    
    def write_text(self, path: Union[str, Path], content: str, 
                  encoding: str = 'utf-8', create_dirs: bool = True) -> None:
        """
        Write text to a file.
        
        Args:
            path: Path to the file.
            content: Text content to write.
            encoding: Text encoding to use.
            create_dirs: Whether to create parent directories if they don't exist.
            
        Raises:
            IOError: If the file cannot be written.
        """
        path = Path(path)
        self.logger.debug(f"Writing text file: {path}")
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Error writing file {path}: {str(e)}")
            raise
    
    def read_binary(self, path: Union[str, Path]) -> bytes:
        """
        Read binary data from a file.
        
        Args:
            path: Path to the file.
            
        Returns:
            bytes: The binary contents of the file.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be read.
        """
        path = Path(path)
        self.logger.debug(f"Reading binary file: {path}")
        
        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading binary file {path}: {str(e)}")
            raise
    
    def write_binary(self, path: Union[str, Path], content: bytes, 
                    create_dirs: bool = True) -> None:
        """
        Write binary data to a file.
        
        Args:
            path: Path to the file.
            content: Binary content to write.
            create_dirs: Whether to create parent directories if they don't exist.
            
        Raises:
            IOError: If the file cannot be written.
        """
        path = Path(path)
        self.logger.debug(f"Writing binary file: {path}")
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            with open(path, 'wb') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Error writing binary file {path}: {str(e)}")
            raise
    
    def read_json(self, path: Union[str, Path], encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Read JSON data from a file.
        
        Args:
            path: Path to the file.
            encoding: Text encoding to use.
            
        Returns:
            dict: The parsed JSON data.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        path = Path(path)
        self.logger.debug(f"Reading JSON file: {path}")
        
        try:
            with open(path, 'r', encoding=encoding) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file {path}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading JSON file {path}: {str(e)}")
            raise
    
    def write_json(self, path: Union[str, Path], data: Dict[str, Any], 
                  encoding: str = 'utf-8', indent: int = 2, 
                  create_dirs: bool = True) -> None:
        """
        Write JSON data to a file.
        
        Args:
            path: Path to the file.
            data: Data to serialize to JSON.
            encoding: Text encoding to use.
            indent: Number of spaces for indentation.
            create_dirs: Whether to create parent directories if they don't exist.
            
        Raises:
            TypeError: If the data cannot be serialized to JSON.
            IOError: If the file cannot be written.
        """
        path = Path(path)
        self.logger.debug(f"Writing JSON file: {path}")
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            with open(path, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent)
        except Exception as e:
            self.logger.error(f"Error writing JSON file {path}: {str(e)}")
            raise
    
    def read_csv(self, path: Union[str, Path], delimiter: str = ',', 
                encoding: str = 'utf-8') -> List[List[str]]:
        """
        Read data from a CSV file.
        
        Args:
            path: Path to the file.
            delimiter: Column delimiter character.
            encoding: Text encoding to use.
            
        Returns:
            list: A list of rows, where each row is a list of values.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            csv.Error: If the file contains invalid CSV.
        """
        path = Path(path)
        self.logger.debug(f"Reading CSV file: {path}")
        
        try:
            with open(path, 'r', newline='', encoding=encoding) as f:
                reader = csv.reader(f, delimiter=delimiter)
                return list(reader)
        except Exception as e:
            self.logger.error(f"Error reading CSV file {path}: {str(e)}")
            raise
    
    def write_csv(self, path: Union[str, Path], rows: List[List[str]], 
                 headers: Optional[List[str]] = None, delimiter: str = ',', 
                 encoding: str = 'utf-8', create_dirs: bool = True) -> None:
        """
        Write data to a CSV file.
        
        Args:
            path: Path to the file.
            rows: Data rows to write.
            headers: Optional column headers.
            delimiter: Column delimiter character.
            encoding: Text encoding to use.
            create_dirs: Whether to create parent directories if they don't exist.
            
        Raises:
            IOError: If the file cannot be written.
        """
        path = Path(path)
        self.logger.debug(f"Writing CSV file: {path}")
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            with open(path, 'w', newline='', encoding=encoding) as f:
                writer = csv.writer(f, delimiter=delimiter)
                
                if headers:
                    writer.writerow(headers)
                
                writer.writerows(rows)
        except Exception as e:
            self.logger.error(f"Error writing CSV file {path}: {str(e)}")
            raise
    
    def copy(self, source: Union[str, Path], destination: Union[str, Path], 
            create_dirs: bool = True) -> None:
        """
        Copy a file from source to destination.
        
        Args:
            source: Source file path.
            destination: Destination file path.
            create_dirs: Whether to create parent directories if they don't exist.
            
        Raises:
            FileNotFoundError: If the source file does not exist.
            IOError: If the file cannot be copied.
        """
        source = Path(source)
        destination = Path(destination)
        self.logger.debug(f"Copying file: {source} to {destination}")
        
        if create_dirs:
            destination.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            shutil.copy2(source, destination)
        except Exception as e:
            self.logger.error(f"Error copying file {source} to {destination}: {str(e)}")
            raise
    
    def move(self, source: Union[str, Path], destination: Union[str, Path], 
            create_dirs: bool = True) -> None:
        """
        Move a file from source to destination.
        
        Args:
            source: Source file path.
            destination: Destination file path.
            create_dirs: Whether to create parent directories if they don't exist.
            
        Raises:
            FileNotFoundError: If the source file does not exist.
            IOError: If the file cannot be moved.
        """
        source = Path(source)
        destination = Path(destination)
        self.logger.debug(f"Moving file: {source} to {destination}")
        
        if create_dirs:
            destination.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            shutil.move(source, destination)
        except Exception as e:
            self.logger.error(f"Error moving file {source} to {destination}: {str(e)}")
            raise
    
    def delete(self, path: Union[str, Path]) -> None:
        """
        Delete a file.
        
        Args:
            path: Path to the file.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be deleted.
        """
        path = Path(path)
        self.logger.debug(f"Deleting file: {path}")
        
        try:
            path.unlink()
        except Exception as e:
            self.logger.error(f"Error deleting file {path}: {str(e)}")
            raise
    
    def create_directory(self, path: Union[str, Path]) -> None:
        """
        Create a directory and any necessary parent directories.
        
        Args:
            path: Path to the directory.
            
        Raises:
            IOError: If the directory cannot be created.
        """
        path = Path(path)
        self.logger.debug(f"Creating directory: {path}")
        
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Error creating directory {path}: {str(e)}")
            raise
    
    def delete_directory(self, path: Union[str, Path], 
                        recursive: bool = True) -> None:
        """
        Delete a directory.
        
        Args:
            path: Path to the directory.
            recursive: Whether to recursively delete the directory contents.
            
        Raises:
            FileNotFoundError: If the directory does not exist.
            IOError: If the directory cannot be deleted.
        """
        path = Path(path)
        self.logger.debug(f"Deleting directory: {path}")
        
        try:
            if recursive:
                shutil.rmtree(path)
            else:
                path.rmdir()
        except Exception as e:
            self.logger.error(f"Error deleting directory {path}: {str(e)}")
            raise
    
    def list_directory(self, path: Union[str, Path], 
                      pattern: str = "*") -> List[Path]:
        """
        List the contents of a directory.
        
        Args:
            path: Path to the directory.
            pattern: Glob pattern for filtering results.
            
        Returns:
            list: A list of Path objects for the directory contents.
            
        Raises:
            FileNotFoundError: If the directory does not exist.
        """
        path = Path(path)
        self.logger.debug(f"Listing directory: {path} with pattern: {pattern}")
        
        try:
            return list(path.glob(pattern))
        except Exception as e:
            self.logger.error(f"Error listing directory {path}: {str(e)}")
            raise