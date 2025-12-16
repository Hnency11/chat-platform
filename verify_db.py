import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL not found in .env")
    exit(1)

try:
    # 1. Try connecting as is
    print(f"Testing connection to: {db_url}")
    conn = psycopg2.connect(db_url, connect_timeout=5)
    conn.close()
    print("SUCCESS: Connection successful!")
    
except psycopg2.OperationalError as e:
    err_msg = str(e)
    # 2. Check if error is "database does not exist"
    if 'database "chatdb" does not exist' in err_msg:
        print("Database 'chatdb' does not exist. Attempting to create it...")
        
        # Parse connection string to connect to 'postgres' db instead
        result = urlparse(db_url)
        user = result.username
        password = result.password
        host = result.hostname
        port = result.port
        
        try:
            # Connect to default 'postgres' database to create new db
            con_postgres = psycopg2.connect(
                dbname='postgres', 
                user=user, 
                password=password, 
                host=host, 
                port=port
            )
            con_postgres.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = con_postgres.cursor()
            cur.execute("CREATE DATABASE chatdb;")
            cur.close()
            con_postgres.close()
            print("SUCCESS: Database 'chatdb' created successfully!")
            
        except Exception as create_err:
            print(f"FAILED to create database automatically: {create_err}")
            print("You may need to manually run: 'createdb -U postgres chatdb'")
    else:
        print(f"CONNECTION FAILED: {e}")
        print("\nPlease check your password and ensures PostgreSQL is running.")
