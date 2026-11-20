import os
import mysql.connector
from mysql.connector import pooling, Error
from contextlib import contextmanager
from config import Config

_pool = None

def get_db_pool():
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="it_asset_pool",
                pool_size=10,
                pool_reset_session=True,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                autocommit=False
            )
        except Error as e:
            # Fallback if database doesn't exist yet
            print(f"[Database Pool Error] {e}")
            return None
    return _pool

def get_db_connection():
    """Returns a direct or pooled MySQL connection."""
    pool = get_db_pool()
    if pool:
        try:
            conn = pool.get_connection()
            return conn
        except Error:
            pass
    
    # Direct fallback connection
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False
    )

@contextmanager
def get_db_cursor(commit=False, dictionary=True):
    """
    Context manager that yields (cursor, connection).
    Automatically commits if commit=True and no exception.
    Automatically rolls back on exception.
    Always cleans up cursor and connection.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor, conn
        if commit:
            conn.commit()
    except Exception as e:
        if conn.is_connected():
            conn.rollback()
        raise e
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def execute_query(sql, params=None, fetch_all=True, fetch_one=False, commit=False, return_id=False, dictionary=True):
    """
    Executes a parameterized SQL query with automatic cursor/connection lifecycle.
    """
    with get_db_cursor(commit=commit, dictionary=dictionary) as (cursor, conn):
        cursor.execute(sql, params or ())
        if commit and return_id:
            return cursor.lastrowid
        if commit:
            return cursor.rowcount
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        return None

def check_db_health():
    """Verifies that MySQL can be reached and queried."""
    try:
        with get_db_cursor(commit=False, dictionary=True) as (cursor, _):
            cursor.execute("SELECT 1 AS health_check")
            row = cursor.fetchone()
            return row and row["health_check"] == 1
    except Exception as e:
        print(f"[DB Health Check Failed] {e}")
        return False
