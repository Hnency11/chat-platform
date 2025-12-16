import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def init_db():
    conn = get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    public_key TEXT
                );
            """)
            
            # Group memberships table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS group_members (
                    group_name TEXT,
                    username TEXT,
                    PRIMARY KEY (group_name, username),
                    FOREIGN KEY (username) REFERENCES users(username)
                );
            """)
            conn.commit()
            print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

def add_user(username, public_key):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, public_key)
                VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE 
                SET public_key = EXCLUDED.public_key;
            """, (username, public_key))
        conn.commit()
    except Exception as e:
        print(f"Error adding user {username}: {e}")
    finally:
        conn.close()

def get_all_users():
    conn = get_connection()
    if not conn: return {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, public_key FROM users;")
            rows = cur.fetchall()
            return {row[0]: row[1] for row in rows}
    except Exception as e:
        print(f"Error fetching users: {e}")
        return {}
    finally:
        conn.close()

def add_to_group(username, group_name):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            # Ensure user exists first (FK constraint)
            # In a real app we might want to ensure they are registered, but 
            # our logic calls add_user on login so strict FK is fine.
            cur.execute("""
                INSERT INTO group_members (group_name, username)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (group_name, username))
        conn.commit()
    except Exception as e:
        print(f"Error adding {username} to group {group_name}: {e}")
    finally:
        conn.close()

def remove_user_from_group(username, group_name):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM group_members
                WHERE group_name = %s AND username = %s;
            """, (group_name, username))
        conn.commit()
    except Exception as e:
        print(f"Error removing {username} from group {group_name}: {e}")
    finally:
        conn.close()

def get_all_groups():
    conn = get_connection()
    if not conn: return {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT group_name, username FROM group_members;")
            rows = cur.fetchall()
            
            groups = {}
            for group_name, username in rows:
                if group_name not in groups:
                    groups[group_name] = set()
                groups[group_name].add(username)
            return groups
    except Exception as e:
        print(f"Error fetching groups: {e}")
        return {}
    finally:
        conn.close()
