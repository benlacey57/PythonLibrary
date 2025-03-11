import sqlite3
from typing import List, Dict, Any, Optional, Union, Tuple, Iterator, ContextManager
from contextlib import contextmanager

from core.base.base_client import BaseClient
from core.interfaces.configurable import Configurable
from core.interfaces.loggable import Loggable

class DatabaseClient(BaseClient, Configurable, Loggable):
    """
    Client for database operations.
    
    Supports multiple database types with a consistent interface.
    """
    
    def __init__(self, config=None):
        """
        Initialize the DatabaseClient.
        
        Args:
            config: Configuration for the client.
        """
        self.configure(config)
        self.initialize_logger("database_client")
        
        self._connection = None
        self._db_type = self.config.get("services.database.type", "sqlite").lower()
    
    def connect(self) -> Any:
        """
        Connect to the database.
        
        Returns:
            Connection object.
            
        Raises:
            ConnectionError: If connection fails.
        """
        if self._connection is not None:
            return self._connection
            
        try:
            if self._db_type == "sqlite":
                self._connection = self._connect_sqlite()
            elif self._db_type == "postgresql":
                self._connection = self._connect_postgresql()
            elif self._db_type == "mysql":
                self._connection = self._connect_mysql()
            else:
                raise ValueError(f"Unsupported database type: {self._db_type}")
                
            self.logger.info(f"Connected to {self._db_type} database")
            return self._connection
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise ConnectionError(f"Failed to connect to {self._db_type} database: {str(e)}")
    
    def close(self) -> None:
        """
        Close the database connection.
        """
        if self._connection is not None:
            try:
                self._connection.close()
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing database connection: {str(e)}")
            finally:
                self._connection = None
    
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
        if self._connection is None:
            self.connect()
            
        self.logger.debug(f"Executing query: {query}")
        
        try:
            cursor = self._connection.cursor()
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
                
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            raise
    
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
        if self._connection is None:
            self.connect()
            
        self.logger.debug(f"Executing query: {query}")
        
        try:
            cursor = self._connection.cursor()
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
                
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch all rows and convert to dictionaries
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                result.append(dict(zip(columns, row)))
                
            cursor.close()
            return result
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            raise
    
    @contextmanager
    def transaction(self) -> Iterator[None]:
        """
        Create a transaction context.
        
        Usage:
            with db_client.transaction():
                db_client.execute("INSERT INTO ...")
                db_client.execute("UPDATE ...")
                
        Raises:
            Exception: If transaction operations fail.
        """
        if self._connection is None:
            self.connect()
            
        self.logger.debug("Starting transaction")
        
        try:
            yield
            self._connection.commit()
            self.logger.debug("Transaction committed")
        except Exception as e:
            self._connection.rollback()
            self.logger.debug(f"Transaction rolled back: {str(e)}")
            raise
    
    def _connect_sqlite(self) -> sqlite3.Connection:
        """
        Connect to SQLite database.
        
        Returns:
            sqlite3.Connection: Database connection.
        """
        connection_string = self.config.get("services.database.connection")
        
        # Enable dictionary access for rows
        connection = sqlite3.connect(connection_string)
        connection.row_factory = sqlite3.Row
        
        return connection
    
    def _connect_postgresql(self) -> Any:
        """
        Connect to PostgreSQL database.
        
        Returns:
            Connection: Database connection.
            
        Raises:
            ImportError: If psycopg2 is not installed.
        """
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            self.logger.error("psycopg2 module not found. Please install it with: pip install psycopg2-binary")
            raise ImportError("psycopg2 module not found. Please install it with: pip install psycopg2-binary")
            
        host = self.config.get("services.database.host")
        port = self.config.get("services.database.port")
        database = self.config.get("services.database.name")
        user = self.config.get("services.database.user")
        password = self.config.get("services.database.password")
        
        # Connect with dictionary cursor
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # Enable dictionary access for rows
        connection.cursor_factory = psycopg2.extras.DictCursor
        
        return connection
    
    def _connect_mysql(self) -> Any:
        """
        Connect to MySQL database.
        
        Returns:
            Connection: Database connection.
            
        Raises:
            ImportError: If mysql-connector-python is not installed.
        """
        try:
            import mysql.connector
        except ImportError:
            self.logger.error("mysql-connector-python module not found. Please install it with: pip install mysql-connector-python")
            raise ImportError("mysql-connector-python module not found. Please install it with: pip install mysql-connector-python")
            
        host = self.config.get("services.database.host")
        port = self.config.get("services.database.port")
        database = self.config.get("services.database.name")
        user = self.config.get("services.database.user")
        password = self.config.get("services.database.password")
        
        connection = mysql.connector.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        return connection
    
    def __enter__(self):
        """
        Support for context manager.
        
        Returns:
            DatabaseClient: This instance.
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Support for context manager.
        
        Closes the connection when exiting the context.
        """
        self.close()