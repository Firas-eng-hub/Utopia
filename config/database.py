"""
Database connection and utility functions for UtopiaHire
This module handles all PostgreSQL database operations
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from psycopg2.extensions import parse_dsn
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_config() -> Dict[str, Any]:
    """
    Get database configuration from DATABASE_URL or individual env vars.
    DATABASE_URL takes precedence if set.
    """
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Preserve hosted-database options such as sslmode and decode credentials.
        parsed = parse_dsn(database_url)
        parsed['database'] = parsed.pop('dbname', 'utopiahire')
        parsed.setdefault('host', 'localhost')
        parsed.setdefault('port', '5432')
        parsed.setdefault('user', '')
        return parsed
    else:
        # Fallback to individual env vars
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'utopiahire'),
            'user': os.getenv('DB_USER', ''),
            'password': os.getenv('DB_PASSWORD', '')
        }


# Database configuration - loaded dynamically
DB_CONFIG = get_db_config()

logger.info(f"Database config: host={DB_CONFIG['host']}, port={DB_CONFIG['port']}, database={DB_CONFIG['database']}, user={DB_CONFIG['user']}")

# Connection pool for efficient database connections
connection_pool = None


def initialize_connection_pool(min_connections: int = 1, max_connections: int = 10):
    """
    Initialize database connection pool
    
    WHY: Connection pooling reuses database connections instead of creating new ones each time,
    which significantly improves performance
    
    Args:
        min_connections: Minimum number of connections to maintain
        max_connections: Maximum number of connections allowed
    """
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            min_connections,
            max_connections,
            **DB_CONFIG
        )
        logger.info("✓ Database connection pool initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize connection pool: {e}")
        return False


def get_connection():
    """
    Get a connection from the pool
    
    Returns:
        Database connection object
    """
    if connection_pool is None:
        initialize_connection_pool()
    return connection_pool.getconn()


def release_connection(connection):
    """
    Return connection back to the pool
    
    Args:
        connection: Database connection to release
    """
    if connection_pool:
        connection_pool.putconn(connection)


def execute_query(query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
    """
    Execute a SQL query with parameters
    
    WHY: This function prevents SQL injection attacks by using parameterized queries
    
    Args:
        query: SQL query string with %s placeholders
        params: Tuple of parameters to safely insert into query
        fetch: Whether to return results (True) or just execute (False)
    
    Returns:
        List of dictionaries representing rows, or None
    
    Example:
        results = execute_query("SELECT * FROM users WHERE email = %s", ("user@example.com",))
    """
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(query, params)
        
        if fetch:
            results = cursor.fetchall()
            connection.commit()
            return [dict(row) for row in results]
        else:
            connection.commit()
            return None
            
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Query execution error: {e}")
        logger.error(f"Query: {query}")
        raise
    finally:
        if connection:
            cursor.close()
            release_connection(connection)


def insert_one(table: str, data: Dict[str, Any]) -> Optional[int]:
    """
    Insert a single row into a table
    
    Args:
        table: Table name
        data: Dictionary of column: value pairs
    
    Returns:
        ID of inserted row
    
    Example:
        user_id = insert_one('users', {
            'name': 'John Doe',
            'email': 'john@example.com',
            'region': 'Tunisia'
        })
    """
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
    
    result = execute_query(query, tuple(data.values()))
    return result[0]['id'] if result else None


def update_one(table: str, data: Dict[str, Any], where: Dict[str, Any]) -> bool:
    """
    Update a single row in a table
    
    Args:
        table: Table name
        data: Dictionary of column: value pairs to update
        where: Dictionary of column: value pairs for WHERE clause
    
    Returns:
        True if successful
    
    Example:
        update_one('users', 
            {'name': 'Jane Doe'}, 
            {'id': 1}
        )
    """
    set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
    where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    
    params = tuple(list(data.values()) + list(where.values()))
    execute_query(query, params, fetch=False)
    return True


def get_one(table: str, where: Dict[str, Any]) -> Optional[Dict]:
    """
    Get a single row from a table
    
    Args:
        table: Table name
        where: Dictionary of column: value pairs for WHERE clause
    
    Returns:
        Dictionary representing the row, or None
    
    Example:
        user = get_one('users', {'email': 'john@example.com'})
    """
    where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
    query = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 1"
    
    results = execute_query(query, tuple(where.values()))
    return results[0] if results else None


def get_many(table: str, where: Dict[str, Any] = None, limit: int = 100) -> List[Dict]:
    """
    Get multiple rows from a table
    
    Args:
        table: Table name
        where: Optional dictionary for WHERE clause
        limit: Maximum number of rows to return
    
    Returns:
        List of dictionaries representing rows
    
    Example:
        users = get_many('users', {'region': 'Tunisia'}, limit=50)
    """
    query = f"SELECT * FROM {table}"
    params = None
    
    if where:
        where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
        query += f" WHERE {where_clause}"
        params = tuple(where.values())
    
    query += f" LIMIT {limit}"
    
    return execute_query(query, params) or []


def test_connection() -> bool:
    """
    Test database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        result = execute_query("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            logger.info("✓ Database connection test successful")
            return True
        return False
    except Exception as e:
        logger.error(f"✗ Database connection test failed: {e}")
        return False


if __name__ == '__main__':
    # Test the database connection
    print("Testing database connection...")
    if test_connection():
        print("✓ Database is ready!")
    else:
        print("✗ Database connection failed. Check your .env configuration.")
