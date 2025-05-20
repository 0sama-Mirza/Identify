import sqlite3
from datetime import datetime
# Function to get a database connection
def get_db_connection(db_path='database.db', timeout=10):
    conn = sqlite3.connect(db_path, timeout=timeout)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_deepface_jobs_table(db_path='database.db'):
    conn = get_db_connection(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deepface_jobs (
            event_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'unsorted',
            retinaface_time TEXT,
            facenet_time TEXT,
            hdbscan_time TEXT
        )
    """)
    conn.commit()
    conn.close()

# Function to insert or update the deepface_jobs table
def insert_event_into_deepface_jobs(event_id, db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO deepface_jobs (event_id, status)
        VALUES (?, 'waiting')
    """, (event_id,))
    conn.commit()
    conn.close()

# Function to get unsorted/cropped events from deepface_jobs table
def get_unsorted_event(db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT event_id
        FROM deepface_jobs
        WHERE status = 'unsorted'
        LIMIT 1
    """)
    events = cursor.fetchall()

    conn.close()
    return events

def get_cropped_event(db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT event_id
        FROM deepface_jobs
        WHERE status = 'cropped'
        LIMIT 1
    """)
    events = cursor.fetchall()

    conn.close()
    return events


def get_embeding_extracted_event(db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT event_id
        FROM deepface_jobs
        WHERE status = 'emb_ext'
        LIMIT 1
    """)
    events = cursor.fetchall()

    conn.close()
    return events

# Function to update the status of an event in deepface_jobs table
def update_event_status(event_id, status, db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE deepface_jobs 
        SET status = ?
        WHERE event_id = ?
    """, (status, event_id))
    conn.commit()
    conn.close()

def delete_sorted_event(event_id, db_path='database.db'):
    """
    Deletes the entire row for a given event_id from the deepface_jobs table
    if its status is 'sorted'.

    Args:
        event_id (str): The ID of the event to potentially delete.
        db_path (str, optional): The path to the SQLite database file.
                                   Defaults to 'database.db'.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Check if the event exists and its status is 'sorted'
    cursor.execute("""
        SELECT status 
        FROM deepface_jobs 
        WHERE event_id = ?
    """, (event_id,))
    result = cursor.fetchone()

    if result:
        status = result[0]
        if status == 'sorted':
            cursor.execute("""
                DELETE FROM deepface_jobs 
                WHERE event_id = ?
            """, (event_id,))
            conn.commit()
            print(f"Successfully deleted row for event_id '{event_id}' (status was 'sorted').")
        else:
            print(f"Event ID '{event_id}' exists, but its status is '{status}', not 'sorted'. No deletion performed.")
    else:
        print(f"Event ID '{event_id}' not found in the deepface_jobs table.")

    conn.close()

def update_retinaface_time(event_id, timestamp, db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE deepface_jobs
        SET retinaface_time = ?
        WHERE event_id = ?
    """, (timestamp, event_id))
    conn.commit()
    conn.close()


def update_facenet_time(event_id, timestamp, db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE deepface_jobs
        SET facenet_time = ?
        WHERE event_id = ?
    """, (timestamp, event_id))
    conn.commit()
    conn.close()


def update_hdbscan_time(event_id, timestamp, db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE deepface_jobs
        SET hdbscan_time = ?
        WHERE event_id = ?
    """, (timestamp, event_id))
    conn.commit()
    conn.close()

def get_duration_string(start_time_str, end_time_str):
    """
    Returns the duration between two ISO 8601 datetime strings as a formatted string (e.g., '1h 23m 45s').

    :param start_time_str: ISO format start time (e.g., '2025-05-20T15:30:00.123456')
    :param end_time_str: ISO format end time
    :return: Duration string in the format 'Xh Ym Zs'
    """
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str)
    duration = end_time - start_time

    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"