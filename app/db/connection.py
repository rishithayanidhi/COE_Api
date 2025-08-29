# app/db/connection.py
import os
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from core.logger import log_error
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "blogpost_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rishi1023")

# Initialize connection pool
try:
    DB_POOL = pool.SimpleConnectionPool(
        1, 20,  # min and max connections
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor
    )
except Exception as e:
    log_error(f"Failed to create DB pool: {e}")
    raise e

def get_db():
    """
    Generator function to get a PostgreSQL cursor as dict-like rows.
    Usage: Depends(get_db) in FastAPI routes.
    """
    conn = None
    cursor = None
    try:
        conn = DB_POOL.getconn()
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        log_error(f"DB operation error: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            DB_POOL.putconn(conn)
















































