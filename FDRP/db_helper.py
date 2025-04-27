import sqlite3

def init_deepface_jobs_table(db_path='database.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deepface_jobs (
            event_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'unsorted'
        )
    """)
    conn.commit()
    conn.close()
init_deepface_jobs_table()

# Function to get a database connection
def get_db_connection(db_path='database.db'):
    conn = sqlite3.connect(db_path)
    return conn

# Function to insert or update the deepface_jobs table
def insert_event_into_deepface_jobs(event_id, db_path='database.db'):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO deepface_jobs (event_id, status)
        VALUES (?, 'unsorted')
    """, (event_id,))
    conn.commit()
    conn.close()

# Function to get unsorted/cropped events from deepface_jobs table
def get_unsorted_event(db_path='database.db'):
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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

# Function to update the status of an event in deepface_jobs table
def update_event_status(event_id, status, db_path='database.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE deepface_jobs 
        SET status = ?
        WHERE event_id = ?
    """, (status, event_id))
    conn.commit()
    conn.close()
