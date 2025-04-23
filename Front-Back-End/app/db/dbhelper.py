import sqlite3
from flask import g, current_app


def get_db_connection():
    """
    Establishes a connection to the SQLite database and uses Flask's `g` for connection management.
    Reuses the same connection for the current request.
    Enables foreign key constraints and sets row access to dictionary format.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],  # Path defined in `config.py`
            detect_types=sqlite3.PARSE_DECLTYPES  # Enable support for advanced types like DATE
        )
        g.db.row_factory = sqlite3.Row  # Access query results as dictionaries
        g.db.execute("PRAGMA foreign_keys = ON;")  # Enforce foreign key constraints
    return g.db


def close_db_connection(e=None):
    """
    Closes the SQLite database connection at the end of the request lifecycle, if it exists.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    """
    Initializes the database with the required tables.
    """
    with app.app_context():
        conn = get_db_connection()
        cur = conn.cursor()

        # Define table schemas
        tables = {
            "users": '''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''',
            "events": '''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,                -- Links to the user who created the event
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    event_date TEXT,
                    location TEXT,
                    status TEXT NOT NULL DEFAULT 'unsorted',
                    num_attendees INTEGER,
                    is_public INTEGER DEFAULT 1,
                    banner_image INTEGER,                -- Links to the banner image in event_images table
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) -- Ensures the event belongs to a user
                    FOREIGN KEY(banner_image) REFERENCES event_images(id) -- Ensures banner image is valid
                )
            ''',
            "event_images": '''
                CREATE TABLE IF NOT EXISTS event_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,               -- Links to the event
                    image_path TEXT NOT NULL,                -- Path to the image file
                    uploaded_at TEXT NOT NULL,               -- Timestamp of upload
                    status TEXT NOT NULL DEFAULT 'unsorted',
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )
            ''',
            "albums": '''
                CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,               -- Links to the associated event
                    user_id INTEGER,                         -- Links to the owner user (can be NULL if no user owns it)
                    name TEXT NOT NULL,                      -- Album name
                    visibility TEXT NOT NULL CHECK (visibility IN ('public', 'private')), -- Restricts allowed values
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES events(id),  -- Ensures the album belongs to an event
                    FOREIGN KEY(user_id) REFERENCES users(id),    -- Ensures the album belongs to a user (optional)
                    UNIQUE(event_id, name),                    -- Ensures unique album names per event
                    UNIQUE(event_id, user_id)                  -- Ensures one user can have one album per event
                )
            ''',
            "album_images": '''
                CREATE TABLE IF NOT EXISTS album_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    album_id INTEGER NOT NULL,               -- Links to the associated album
                    event_image_id INTEGER NOT NULL,         -- Links to an image from the event
                    added_at TEXT NOT NULL,                  -- Timestamp when the image was added
                    FOREIGN KEY(album_id) REFERENCES albums(id),
                    FOREIGN KEY(event_image_id) REFERENCES event_images(id)
                )
            '''
        }


        # Iterate over the table definitions and execute them
        for table_name, create_stmt in tables.items():
            print(f"Creating table: {table_name}")  # Debugging
            cur.execute(create_stmt)

        conn.commit()
        conn.close()
        