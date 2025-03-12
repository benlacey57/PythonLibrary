# /home/{user}/python/python_library/services/database/db_interface.py
"""
Interface definitions for database clients.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple, Iterator, ContextManager
from contextlib import contextmanager

from ...core.base.base_client import BaseClient
from ...core.interfaces.configurable import Configurable
from ...core.interfaces.loggable import Loggable
from ...core.data import ConnectionInfo, QueryResult

class Database(BaseClient, Configurable, Loggable, ABC):
    """
    Abstract interface for database clients.
    
    Defines the common methods that all database clients should implement.
    """
    
    @abstractmethod
    def connect(self) -> Any:
        """
        Connect to the database.
        
        Returns:
            Connection object.
            
        Raises:
            ConnectionError: If connection fails.
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Close the database connection.
        """
        pass
    
    @abstractmethod
    def execute(self, query: str, parameters: Optional[List[Any]] = None) -> int:
        """
        Execute a query that doesn't return results.
        
        Args:
            query: SQL query string.
            parameters: Query parameters.
            
        Returns:
            int: Number of affected rows.
            
        Raises:
            Exception: If query execution fails.
        """
        pass
    
    @abstractmethod
    def query(self, query: str, parameters: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query that returns results.
        
        Args:
            query: SQL query string.
            parameters: Query parameters.
            
        Returns:
            list: Query results as a list of dictionaries.
            
        Raises:
            Exception: If query execution fails.
        """
        pass
    
    @abstractmethod
    def transaction(self) -> ContextManager:
        """
        Create a transaction context.
        
        Usage:
            with db_client.transaction():
                db_client.execute("INSERT INTO ...")
                db_client.execute("UPDATE ...")
                
        Raises:
            Exception: If transaction operations fail.
        """
        pass