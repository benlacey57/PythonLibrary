"""
Airtable client implementation.
"""

import time
import json
from typing import List, Dict, Any, Optional, Union, Tuple, Iterator, ContextManager
from contextlib import contextmanager
import urllib.parse
import requests
from datetime import datetime

from ...core.base.base_client import BaseClient
from ...core.interfaces.configurable import Configurable
from ...core.interfaces.loggable import Loggable
from ...core.interfaces.database import DatabaseInterface
from ...core.exceptions import DatabaseError, ConnectionError, AuthenticationError
from ...core.data import AirtableRecord, DatabaseType


class AirtableClient(DatabaseInterface):
    """
    Client for Airtable API operations.
    
    Provides methods for interacting with Airtable bases and tables.
    """
    
    def __init__(self, config=None):
        """
        Initialize the AirtableClient.
        
        Args:
            config: Configuration for the client.
        """
        self.configure(config)
        self.initialize_logger("airtable_client")
        
        self._api_key = self.config.get("services.database.airtable.api_key")
        self._base_id = self.config.get("services.database.airtable.base_id")
        self._api_url = "https://api.airtable.com/v0"
        self._session = None
    
    def connect(self):
        """
        Create a connection to Airtable API.
        
        Returns:
            requests.Session: Session for API requests.
            
        Raises:
            ConnectionError: If connection fails.
            AuthenticationError: If authentication fails.
        """
        if self._session is not None:
            return self._session
            
        if not self._api_key:
            raise AuthenticationError(
                "AirtableClient", 
                "API key is required", 
                "AIRTABLE-001"
            )
            
        if not self._base_id:
            raise ConnectionError(
                "AirtableClient", 
                "Base ID is required", 
                "AIRTABLE-002"
            )
            
        try:
            # Create session with headers
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            })
            
            # Test connection by getting base schema
            url = f"{self._api_url}/{self._base_id}"
            response = session.get(url, params={"metabase": "1"})
            
            if response.status_code == 401:
                raise AuthenticationError(
                    "AirtableClient", 
                    "Authentication failed: Invalid API key", 
                    "AIRTABLE-003"
                )
                
            if response.status_code != 200:
                raise ConnectionError(
                    "AirtableClient", 
                    f"Failed to connect to Airtable API: {response.text}", 
                    "AIRTABLE-004"
                )
                
            self._session = session
            self.logger.info(f"Connected to Airtable base: {self._base_id}")
            return session
        except requests.RequestException as e:
            self.logger.error(f"Airtable API connection error: {str(e)}")
            raise ConnectionError(
                "AirtableClient",
                f"Failed to connect to Airtable API: {str(e)}",
                "AIRTABLE-005"
            )
    
    def close(self):
        """
        Close the Airtable connection.
        """
        if self._session is not None:
            try:
                self._session.close()
                self._session = None
                self.logger.info("Airtable connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Airtable connection: {str(e)}")
    
    def execute(self, query, parameters=None):
        """
        Execute a non-query operation on Airtable.
        
        For Airtable, this is used for create, update, and delete operations.
        The "query" parameter is used to specify the table and operation.
        
        Format: "TABLE:OPERATION" where OPERATION is one of:
        - CREATE: Create new records
        - UPDATE: Update existing records
        - DELETE: Delete records
        
        Args:
            query: String in format "TABLE:OPERATION" specifying table and operation.
            parameters: For CREATE/UPDATE: List of record data dictionaries.
                       For DELETE: List of record IDs to delete.
            
        Returns:
            int: Number of affected records.
            
        Raises:
            DatabaseError: If operation fails.
        """
        if not query or ":" not in query:
            raise DatabaseError(
                "Invalid query format. Expected 'TABLE:OPERATION'",
                query=query,
                error_code="AIRTABLE-006"
            )
            
        table, operation = query.split(":", 1)
        table = table.strip()
        operation = operation.strip().upper()
        
        if not table or not operation:
            raise DatabaseError(
                "Invalid query format. Table and operation are required",
                query=query,
                error_code="AIRTABLE-007"
            )
            
        if operation not in ["CREATE", "UPDATE", "DELETE"]:
            raise DatabaseError(
                f"Invalid operation '{operation}'. Must be CREATE, UPDATE, or DELETE",
                query=query,
                error_code="AIRTABLE-008"
            )
            
        if not parameters:
            return 0
            
        session = self.connect()
        
        try:
            if operation == "CREATE":
                return self._create_records(table, parameters)
            elif operation == "UPDATE":
                return self._update_records(table, parameters)
            elif operation == "DELETE":
                return self._delete_records(table, parameters)
        except Exception as e:
            self.logger.error(f"Airtable operation error: {str(e)}")
            raise DatabaseError(
                f"Airtable operation failed: {str(e)}",
                query=query,
                error_code="AIRTABLE-009"
            )
    
    def query(self, query, parameters=None):
        """
        Query records from an Airtable table.
        
        The query parameter is the table name, and parameters can be used for filtering.
        
        Args:
            query: Table name to query.
            parameters: Optional dictionary with query parameters:
                       - fields: List of field names to include
                       - filterByFormula: Airtable formula for filtering
                       - maxRecords: Maximum number of records to return
                       - sort: List of sort objects (field, direction)
                       - view: Name of view to use
            
        Returns:
            list: Records as dictionaries with id and fields.
            
        Raises:
            DatabaseError: If query fails.
        """
        session = self.connect()
        table = query.strip()
        
        if not table:
            raise DatabaseError(
                "Table name is required",
                query=query,
                error_code="AIRTABLE-010"
            )
            
        try:
            url = f"{self._api_url}/{self._base_id}/{urllib.parse.quote(table)}"
            params = parameters or {}
            
            # Handle pagination
            all_records = []
            offset = None
            
            while True:
                # Add offset if we have one
                if offset:
                    params["offset"] = offset
                    
                # Make the request
                response = session.get(url, params=params)
                
                if response.status_code != 200:
                    raise DatabaseError(
                        f"Airtable query failed: {response.text}",
                        query=query,
                        error_code="AIRTABLE-011"
                    )
                    
                data = response.json()
                
                # Add records to our result
                records = data.get("records", [])
                
                # Convert to normalized format
                for record in records:
                    all_records.append({
                        "id": record.get("id"),
                        "fields": record.get("fields", {}),
                        "created_time": record.get("createdTime")
                    })
                
                # Check if we need to paginate
                offset = data.get("offset")
                if not offset:
                    break
                    
            return all_records
        except Exception as e:
            self.logger.error(f"Airtable query error: {str(e)}")
            raise DatabaseError(
                f"Airtable query failed: {str(e)}",
                query=query,
                error_code="AIRTABLE-012"
            )
    
    def query_one(self, query, parameters=None):
        """
        Get a single record from Airtable.
        
        If the query is a record ID, retrieves that specific record.
        Otherwise, returns the first record matching the query.
        
        Args:
            query: Table name or "TABLE/RECORD_ID" to get a specific record.
            parameters: Optional filter parameters.
            
        Returns:
            dict: Record data or None if not found.
            
        Raises:
            DatabaseError: If query fails.
        """
        if "/" in query:
            # Get specific record by ID
            table, record_id = query.split("/", 1)
            table = table.strip()
            record_id = record_id.strip()
            
            try:
                session = self.connect()
                url = f"{self._api_url}/{self._base_id}/{urllib.parse.quote(table)}/{record_id}"
                
                response = session.get(url)
                
                if response.status_code == 404:
                    return None
                    
                if response.status_code != 200:
                    raise DatabaseError(
                        f"Airtable query failed: {response.text}",
                        query=query,
                        error_code="AIRTABLE-013"
                    )
                    
                record = response.json()
                return {
                    "id": record.get("id"),
                    "fields": record.get("fields", {}),
                    "created_time": record.get("createdTime")
                }
            except Exception as e:
                self.logger.error(f"Airtable query error: {str(e)}")
                raise DatabaseError(
                    f"Airtable query failed: {str(e)}",
                    query=query,
                    error_code="AIRTABLE-014"
                )
        else:
            # Get first record from table
            if parameters is None:
                parameters = {}
                
            # Limit to one record
            parameters["maxRecords"] = 1
            
            records = self.query(query, parameters)
            return records[0] if records else None
    
    def _create_records(self, table, records):
        """
        Create records in an Airtable table.
        
        Args:
            table: Table name.
            records: List of record data dictionaries.
            
        Returns:
            int: Number of created records.
            
        Raises:
            DatabaseError: If creation fails.
        """
        session = self.connect()
        url = f"{self._api_url}/{self._base_id}/{urllib.parse.quote(table)}"
        
        # Airtable can only process up to 10 records at a time
        batch_size = 10
        created_count = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # Format the records for Airtable API
            airtable_records = []
            for record in batch:
                # Skip 'id' field if present
                fields = {k: v for k, v in record.items() if k != 'id'}
                airtable_records.append({"fields": fields})
            
            # Make the request
            response = session.post(url, data=json.dumps({"records": airtable_records}))
            
            if response.status_code != 200:
                raise DatabaseError(
                    f"Failed to create records: {response.text}",
                    query=f"{table}:CREATE",
                    error_code="AIRTABLE-015"
                )
                
            data = response.json()
            created_count += len(data.get("records", []))
            
        return created_count
    
    def _update_records(self, table, records):
        """
        Update records in an Airtable table.
        
        Args:
            table: Table name.
            records: List of record data dictionaries with 'id' field.
            
        Returns:
            int: Number of updated records.
            
        Raises:
            DatabaseError: If update fails.
        """
        session = self.connect()
        url = f"{self._api_url}/{self._base_id}/{urllib.parse.quote(table)}"
        
        # Airtable can only process up to 10 records at a time
        batch_size = 10
        updated_count = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # Format the records for Airtable API
            airtable_records = []
            for record in batch:
                # Ensure record has ID
                if 'id' not in record:
                    raise DatabaseError(
                        "Record is missing 'id' field required for update",
                        query=f"{table}:UPDATE",
                        error_code="AIRTABLE-016"
                    )
                    
                # Extract ID and rest of fields
                record_id = record['id']
                fields = {k: v for k, v in record.items() if k != 'id'}
                
                airtable_records.append({
                    "id": record_id,
                    "fields": fields
                })
            
            # Make the request
            response = session.patch(url, data=json.dumps({"records": airtable_records}))
            
            if response.status_code != 200:
                raise DatabaseError(
                    f"Failed to update records: {response.text}",
                    query=f"{table}:UPDATE",
                    error_code="AIRTABLE-017"
                )
                
            data = response.json()
            updated_count += len(data.get("records", []))
            
        return updated_count
    
    def _delete_records(self, table, record_ids):
        """
        Delete records from an Airtable table.
        
        Args:
            table: Table name.
            record_ids: List of record IDs to delete.
            
        Returns:
            int: Number of deleted records.
            
        Raises:
            DatabaseError: If deletion fails.
        """
        session = self.connect()
        url = f"{self._api_url}/{self._base_id}/{urllib.parse.quote(table)}"
        
        # Airtable can only process up to 10 IDs at a time
        batch_size = 10
        deleted_count = 0
        
        for i in range(0, len(record_ids), batch_size):
            batch = record_ids[i:i + batch_size]
            
            # Make the request
            params = {"records[]": batch}
            response = session.delete(url, params=params)
            
            if response.status_code != 200:
                raise DatabaseError(
                    f"Failed to delete records: {response.text}",
                    query=f"{table}:DELETE",
                    error_code="AIRTABLE-018"
                )
                
            data = response.json()
            deleted_count += len(data.get("records", []))
            
        return deleted_count
    
    def transaction(self):
        """
        Create a transaction context.
        
        Note: Airtable does not support transactions, so this is a dummy implementation.
        
        Raises:
            DatabaseError: Always raises an error when used.
        """
        raise DatabaseError(
            "Airtable does not support transactions",
            query="transaction",
            error_code="AIRTABLE-019"
        )