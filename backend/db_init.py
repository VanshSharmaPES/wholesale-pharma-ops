"""
Expiry Return Reminder System - Database Initializer

Connects to the SQLite database specified by DATABASE_PATH in the .env file
and runs the schema.sql migration file to initialize the tables.
"""

import os
import sqlite3
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def initialize_database() -> None:
    """Loads environment settings and runs schema initialization SQL script."""
    # Find .env at workspace root relative to backend directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(base_dir, ".env")
    
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logger.info(f"Loaded environment variables from: {dotenv_path}")
    else:
        logger.warning(f"No .env file found at {dotenv_path}. Using environment defaults.")
        
    db_path = os.getenv("DATABASE_PATH", "data/pharma_ops.db")
    # Resolve path relative to workspace root if it is a relative path
    if not os.path.isabs(db_path):
        db_path = os.path.join(base_dir, db_path)
        
    logger.info(f"Initializing SQLite database at: {db_path}")
    
    # Ensure parent directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Verified directory exists: {db_dir}")
        except Exception as e:
            logger.error(f"Failed to create database directory {db_dir}: {str(e)}")
            raise
            
    # Locate schema.sql relative to db_init.py
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    if not os.path.exists(schema_path):
        error_msg = f"Schema SQL file not found at: {schema_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
        
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Read and run schema.sql
        logger.info(f"Reading schema definition from {schema_path}...")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            
        logger.info("Executing database schema migration...")
        cursor.executescript(schema_sql)
        
        conn.commit()
        logger.info("Database migration completed successfully!")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite database initialization error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    initialize_database()
