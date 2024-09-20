import sqlite3
import os

DATABASE_FILE = 'people_counting.db'

def create_database():
    """Create a SQLite database and the 'logs' table."""
    if not os.path.exists(DATABASE_FILE):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE logs (
            timestamp TEXT,
            camera_ip TEXT,
            enter_count INTEGER,
            exit_count INTEGER,
            current_count INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()

def insert_log(timestamp, camera_ip, enter_count, exit_count, current_count):
    """Insert a new log entry into the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO logs (timestamp, camera_ip, enter_count, exit_count, current_count)
    VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, camera_ip, enter_count, exit_count, current_count))
    
    conn.commit()
    conn.close()

# Initialize the database
create_database()