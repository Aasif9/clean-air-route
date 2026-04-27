import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get a database connection with SSL for Render PostgreSQL"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not set in environment variables")
        
        print(f"Connecting to database: {database_url[:20]}...")  # Print first 20 chars for debugging
        
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def test_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
