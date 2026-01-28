
from models.database import init_db, get_session, User
from config import Config
import os

def create_database():
    print(f"Initializing database at: {Config.DATABASE_URL}")
    engine = init_db(Config.DATABASE_URL)
    print("Database tables created successfully.")
    
    # Check for tables
    import sqlite3
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")
        conn.close()
    else:
        print("Database file still not found. Check path.")

if __name__ == "__main__":
    create_database()
