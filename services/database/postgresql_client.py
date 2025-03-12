"""
PostgreSQL database client implementation.
"""

import time
import threading
from typing import List, Dict, Any, Optional, Union, Tuple, Iterator, ContextManager
from contextlib import contextmanager

from ...core.base.base_client import BaseClient
from ...core.interfaces.configurable import Configurable
from ...core.interfaces.loggable import Loggable
from ...core.interfaces.database import DatabaseInterface
from ...core.exceptions import DatabaseError, ConnectionError
from ...core.data import ConnectionInfo, QueryResult, DatabaseType

class PostgreSQLClient(DatabaseInterface):
    """
    Client for PostgreSQL database operations.
    
    Provides methods for connecting to and querying PostgreSQL databases.
    """
    
    def __init__(self, config=None):
        """
        Initialize the PostgreSQLClient.
        
        Args:
            config: Configuration for the client.
        """
        self.configure(config)
        self.initialize_logger("postgresql_client")
        
        self._host = self.config.get("services.database.postgresql.host", "localhost")
        self._port = self.config.get("services.database.postgresql.port", 5432)
        self._database = self.config.get("services.database.postgresql.database")
        self._user = self.config.get("services.database.postgresql.user")
        self._password = self.config.get("services.database.postgresql.password")
        self._connection = None
        
        # Connection pool settings
        self._min_connections = self.config.get("services.database.postgresql.pool.min_connections", 1)
        self._max_connections = self.config.get("services.database.postgresql.pool.max_connections", 5)
        
        # Thread-local storage for transactions
        self._local = threading.local()
        self._local.connection = None
        self._local.transaction_level = 0
        
        # Check if psycopg2 is available
        try:
            import psycopg2
            import psycopg2.pool
            import psycopg2.extras
            self._psycopg2_available = True
        except ImportError:
            self._psycopg2_available = False
            self.logger.warning("psycopg2 not available. Please install with: pip install psycopg2-binary")
    
    def connect(self):
        """
        Connect to the PostgreSQL database.
        
        Returns:
            Connection: Database connection.
            
        Raises:
            ConnectionError: If connection fails.
            ImportError: If psycopg2 is not installed.
        """
        # If already in a transaction, return the existing connection
        if hasattr(self._local, 'connection') and self._local.connection is not None:
            return self._local.connection
            
        if not self._psycopg2_available:
            raise ImportError("psycopg2 module not found. Please install it with: pip install psycopg2-binary")
            
        try:
            import psycopg2
            import psycopg2.extras
            
            connection = psycopg2.connect(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._user,
                password=self._password
            )
            
            # Enable dictionary access for rows
            connection.cursor_factory = psycopg2.extras.DictCursor
            
            self.logger.info(f"Connected to PostgreSQL database: {self._host}:{self._port}/{self._database}")
            return connection
        except Exception as e:
            self.logger.error(f"PostgreSQL connection error: {str(e)}")
            raise ConnectionError(
                "PostgreSQLClient",
                f"Failed to connect to PostgreSQL database: {str(e)}",
                "POSTGRES-001"
            )
    
    def close(self):
        """
        Close the database connection.
        """
        if self._connection is not None:
            try:
                self._connection.close()
                self._connection = None
                self.logger.info("PostgreSQL connection closed")
            except Exception as e:
                self.logger.error(f"Error closing PostgreSQL connection: {str(e)}")
    
    def execute(self, query, parameters=None):
        """
        Execute a query that doesn't return results.
        
        Args:
            query: SQL query string.
            parameters: Query parameters.
            
        Returns:
            int: Number of affected rows.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        connection = None
        
        try:
            # Get connection (from transaction or new)
            if hasattr(self._local, 'connection') and self._local.connection is not None:
                connection = self._local.connection
            else:
                connection = self.connect()
                self._connection = connection
                
            self.logger.debug(f"Executing query: {query}")
            
            cursor = connection.cursor()
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
                
            affected_rows = cursor.rowcount
            cursor.close()
            
            # Only commit if not in a transaction
            if not hasattr(self._local, 'transaction_level') or self._local.transaction_level == 0:
                connection.commit()
                
            return affected_rows
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            raise DatabaseError(
                f"Query execution failed: {str(e)}",
                query=query,
                error_code="POSTGRES-002"
            )
    
    def query(self, query, parameters=None):
        """
        Execute a query that returns results.
        
        Args:
            query: SQL query string.
            parameters: Query parameters.
            
        Returns:
            list: Query results as a list of dictionaries.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        connection = None
        start_time = time.time()
        
        try:
            # Get connection (from transaction or new)
            if hasattr(self._local, 'connection') and self._local.connection is not None:
                connection = self._local.connection
            else:
                connection = self.connect()
                self._connection = connection
                
            self.logger.debug(f"Executing query: {query}")
            
            cursor = connection.cursor()
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
                
            # Fetch all rows and convert to dictionaries
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                result.append(dict(row))
                
            cursor.close()
            
            execution_time = time.time() - start_time
            self.logger.debug(f"Query executed in {execution_time:.4f} seconds")
            
            return result
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            raise DatabaseError(
                f"Query execution failed: {str(e)}",
                query=query,
                error_code="POSTGRES-003"
            )
    
    def query_one(self, query, parameters=None):
        """
        Execute a query and return a single result.
        
        Args:
            query: SQL query string.
            parameters: Query parameters.
            
        Returns:
            dict: First row of results as a dictionary or None if no results.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        results = self.query(query, parameters)
        return results[0] if results else None
    
    def executemany(self, query, parameters_list):
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string.
            parameters_list: List of parameter sets.
            
        Returns:
            int: Number of affected rows.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        if not parameters_list:
            return 0
            
        connection = None
        batch_size = self.config.get("services.database.postgresql.batch_size", 100)
        total_affected = 0
        
        try:
            # Get connection (from transaction or new)
            if hasattr(self._local, 'connection') and self._local.connection is not None:
                connection = self._local.connection
            else:
                connection = self.connect()
                self._connection = connection
                
            self.logger.debug(f"Executing batch query: {query} with {len(parameters_list)} parameter sets")
            
            cursor = connection.cursor()
            
            # Process in batches
            for i in range(0, len(parameters_list), batch_size):
                batch = parameters_list[i:i + batch_size]
                
                # Use executemany for PostgreSQL
                cursor.executemany(query, batch)
                total_affected += cursor.rowcount
                
            cursor.close()
            
            # Only commit if not in a transaction
            if not hasattr(self._local, 'transaction_level') or self._local.transaction_level == 0:
                connection.commit()
                
            return total_affected
        except Exception as e:
            self.logger.error(f"Batch query execution error: {str(e)}")
            raise DatabaseError(
                f"Batch query execution failed: {str(e)}",
                query=query,
                error_code="POSTGRES-004"
            )
    
    @contextmanager
    def transaction(self):
        """
        Create a transaction context.
        
        Usage:
            with db_client.transaction():
                db_client.execute("INSERT INTO ...")
                db_client.execute("UPDATE ...")
                
        Raises:
            DatabaseError: If transaction operations fail.
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = self.connect()
            self._local.transaction_level = 0
            
        # Increment transaction level (for nested transactions)
        self._local.transaction_level += 1
        
        self.logger.debug(f"Starting transaction (level {self._local.transaction_level})")
        
        try:
            yield
            
            # Only commit if this is the outermost transaction
            if self._local.transaction_level == 1:
                self._local.connection.commit()
                self.logger.debug("Transaction committed")
        except Exception as e:
            # Rollback on error
            if self._local.transaction_level == 1:
                self._local.connection.rollback()
                self.logger.debug(f"Transaction rolled back: {str(e)}")
            raise
        finally:
            # Decrement transaction level
            self._local.transaction_level -= 1
            
            # Release connection if this is the outermost transaction
            if self._local.transaction_level == 0:
                self._local.connection = None