import sqlite3
from typing import List, Dict, Any, Optional, Union, Tuple, Iterator, ContextManager
from contextlib import contextmanager
import time
import threading
from queue import Queue, Empty

from core.base.base_client import BaseClient
from core.interfaces.configurable import Configurable
from core.interfaces.loggable import Loggable
from core.exceptions import DatabaseError, ConnectionError

class ConnectionPool:
    """
    Connection pool for database connections.
    
    Manages a pool of reusable database connections to improve performance.
    """
    
    def __init__(self, create_connection_func, min_connections=1, max_connections=5, 
                timeout=30, validation_interval=30):
        """
        Initialize the connection pool.
        
        Args:
            create_connection_func: Function to create a new connection.
            min_connections: Minimum number of connections to keep in the pool.
            max_connections: Maximum number of connections allowed in the pool.
            timeout: Timeout in seconds when waiting for a connection.
            validation_interval: Time in seconds between connection validation.
        """
        self._create_connection = create_connection_func
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._timeout = timeout
        self._validation_interval = validation_interval
        
        self._pool = Queue()
        self._active_connections = 0
        self._lock = threading.RLock()
        
        # Initialize the minimum number of connections
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize the connection pool with minimum connections."""
        for _ in range(self._min_connections):
            self._add_connection()
    
    def _add_connection(self):
        """
        Add a new connection to the pool.
        
        Returns:
            bool: True if a connection was added, False otherwise.
        """
        with self._lock:
            if self._active_connections >= self._max_connections:
                return False
                
            try:
                connection = self._create_connection()
                self._pool.put((connection, time.time()))
                self._active_connections += 1
                return True
            except:
                return False
    
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Returns:
            Connection object.
            
        Raises:
            ConnectionError: If unable to get a connection.
        """
        start_time = time.time()
        
        while time.time() - start_time < self._timeout:
            # Try to get a connection from the pool
            try:
                connection, last_used = self._pool.get(block=False)
                
                # Validate the connection
                if time.time() - last_used > self._validation_interval:
                    if self._validate_connection(connection):
                        return connection
                    else:
                        # Connection is invalid, create a new one
                        with self._lock:
                            self._active_connections -= 1
                        
                        if not self._add_connection():
                            continue
                else:
                    return connection
            except Empty:
                # Pool is empty, try to create a new connection
                if self._add_connection():
                    continue
                    
                # Wait a bit before trying again
                time.sleep(0.1)
                
        # Timeout reached
        raise ConnectionError("DatabaseClient", "Timeout waiting for database connection")
    
    def _validate_connection(self, connection):
        """
        Validate a connection to ensure it's still usable.
        
        Args:
            connection: Connection to validate.
            
        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        try:
            # For SQLite
            if hasattr(connection, 'cursor'):
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
                
            # For other databases, may need different validation
            return True
        except:
            return False
    
    def return_connection(self, connection):
        """
        Return a connection to the pool.
        
        Args:
            connection: Connection to return.
        """
        self._pool.put((connection, time.time()))
    
    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            while not self._pool.empty():
                try:
                    connection, _ = self._pool.get(block=False)
                    try:
                        connection.close()
                    except:
                        pass
                except Empty:
                    break
            
            self._active_connections = 0


class DatabaseClient(BaseClient, Configurable, Loggable):
    """
    Client for database operations.
    
    Supports multiple database types with a consistent interface.
    Uses connection pooling for improved performance.
    """
    
    def __init__(self, config=None):
        """
        Initialize the DatabaseClient.
        
        Args:
            config: Configuration for the client.
        """
        self.configure(config)
        self.initialize_logger("database_client")
        
        self._db_type = self.config.get("services.database.type", "sqlite").lower()
        self._batch_size = self.config.get("services.database.batch_size", 100)
        
        # Connection pool settings
        self._min_connections = self.config.get("services.database.pool.min_connections", 1)
        self._max_connections = self.config.get("services.database.pool.max_connections", 5)
        self._connection_timeout = self.config.get("services.database.pool.timeout", 30)
        
        # Initialize connection pool
        self._pool = None
        self._initialize_pool()
        
        # Thread-local storage for transactions
        self._local = threading.local()
        self._local.connection = None
        self._local.transaction_level = 0
    
    def _initialize_pool(self):
        """Initialize the connection pool."""
        if self._db_type == "sqlite":
            create_func = self._connect_sqlite
        elif self._db_type == "postgresql":
            create_func = self._connect_postgresql
        elif self._db_type == "mysql":
            create_func = self._connect_mysql
        else:
            raise DatabaseError(
                f"Unsupported database type: {self._db_type}",
                error_code="DB-002"
            )
            
        self._pool = ConnectionPool(
            create_func,
            min_connections=self._min_connections,
            max_connections=self._max_connections,
            timeout=self._connection_timeout
        )
        
        self.logger.info(f"Initialized connection pool for {self._db_type} database")
    
    def connect(self):
        """
        Get a connection from the pool.
        
        Returns:
            Connection object.
            
        Raises:
            ConnectionError: If connection fails.
        """
        # If already in a transaction, return the existing connection
        if hasattr(self._local, 'connection') and self._local.connection is not None:
            return self._local.connection
            
        try:
            # Get a connection from the pool
            connection = self._pool.get_connection()
            self.logger.debug("Obtained database connection from pool")
            return connection
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise ConnectionError(
                "DatabaseClient",
                f"Failed to connect to {self._db_type} database: {str(e)}",
                "DB-003"
            )
    
    def release(self, connection):
        """
        Release a connection back to the pool.
        
        Args:
            connection: Connection to release.
        """
        # Don't release if in a transaction
        if hasattr(self._local, 'transaction_level') and self._local.transaction_level > 0:
            return
            
        try:
            self._pool.return_connection(connection)
            self.logger.debug("Released database connection to pool")
        except Exception as e:
            self.logger.error(f"Error releasing connection: {str(e)}")
    
    def close(self):
        """
        Close all database connections.
        """
        if self._pool:
            try:
                self._pool.close_all()
                self.logger.info("Closed all database connections")
            except Exception as e:
                self.logger.error(f"Error closing database connections: {str(e)}")
    
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
            # Get connection (from transaction or pool)
            if hasattr(self._local, 'connection') and self._local.connection is not None:
                connection = self._local.connection
            else:
                connection = self.connect()
                
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
                error_code="DB-004"
            )
        finally:
            # Release connection if not in a transaction
            if connection and (not hasattr(self._local, 'transaction_level') or self._local.transaction_level == 0):
                self.release(connection)
    
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
        total_affected = 0
        
        try:
            # Get connection (from transaction or pool)
            if hasattr(self._local, 'connection') and self._local.connection is not None:
                connection = self._local.connection
            else:
                connection = self.connect()
                
            self.logger.debug(f"Executing batch query: {query} with {len(parameters_list)} parameter sets")
            
            cursor = connection.cursor()
            
            # Process in batches
            for i in range(0, len(parameters_list), self._batch_size):
                batch = parameters_list[i:i + self._batch_size]
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
                error_code="DB-005"
            )
        finally:
            # Release connection if not in a transaction
            if connection and (not hasattr(self._local, 'transaction_level') or self._local.transaction_level == 0):
                self.release(connection)