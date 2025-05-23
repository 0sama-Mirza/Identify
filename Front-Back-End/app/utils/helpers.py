from flask import session
import re
from datetime import datetime
from app.db.dbhelper import get_db_connection
from werkzeug.datastructures import FileStorage
import os

def allowed_file(filename):
    """
    Checks if the file extension is allowed.
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_required_fields(data, required_fields):
    """
    Validates that all required fields are present in the provided data dictionary.
    Returns a list of missing fields or an empty list if all fields are present.
    """
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    return missing_fields


def format_timestamp(timestamp, format="%Y-%m-%d %H:%M:%S"):
    """
    Converts a timestamp into a human-readable format.
    Example: "2025-03-17 23:31:00" -> "Mar 17, 2025 11:31 PM"
    """
    try:
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime(format)
    except ValueError:
        return timestamp  # Return the original timestamp if parsing fails


def is_logged_in():
    """
    Checks if the user is currently logged in based on the session.
    Returns True if logged in, False otherwise.
    """
    return 'user_id' in session


def get_logged_in_user():
    """
    Fetches details of the currently logged-in user from the session.
    Returns a dictionary: { "user_id": ..., "username": ... } or None if not logged in.
    """
    if is_logged_in():
        return {
            "user_id": session.get('user_id'),
            "username": session.get('username')
        }
    return None


def sanitize_string(input_string):
    """
    Sanitizes a string by removing leading/trailing whitespaces and any special characters.
    """
    return re.sub(r"[^\w\s]", "", input_string.strip()) if input_string else input_string

def get_event_image_id_via_image_path(image_path):
    """
    Fetches the event_image_id for the given image_path.
    """
    try:
        with get_db_connection() as conn:  # Automatically closes connection
            cur = conn.cursor()

            query = '''
            SELECT id 
            FROM event_images 
            WHERE image_path = ?;
            '''
            cur.execute(query, (image_path,))
            result = cur.fetchone()

            if result:
                print(f"[DEBUG] Event Image ID for '{image_path}': {result['id']}")
                return result['id']
            else:
                print(f"[ERROR] No entry found for image_path: {image_path}")
                return None

    except Exception as e:
        print(f"[ERROR] Exception occurred while fetching event_image_id: {str(e)}")
        return None


def get_next_image_index(event_id):
    """
    Returns the next index number for renaming images for the given event.
    """
    try:
        with get_db_connection() as conn:  # Reuses your helper
            cur = conn.cursor()

            query = '''
            SELECT COUNT(*) as count
            FROM event_images
            WHERE event_id = ?;
            '''
            cur.execute(query, (event_id,))
            result = cur.fetchone()

            if result:
                return result['count'] + 1  # Start from next index
            else:
                return 1  # Default fallback

    except Exception as e:
        print(f"[ERROR] Failed to get next image index: {str(e)}")
        return 1

def rename_event_images(file_list):
    renamed_files = []
    
    for index, file in enumerate(file_list, start=1):
        # Extract original extension
        _, ext = os.path.splitext(file.filename)
        new_filename = f"Imj{index}{ext}"
        
        # Create a new FileStorage object with the same stream and new filename
        renamed_file = FileStorage(
            stream=file.stream,
            filename=new_filename,
            content_type=file.content_type,
            content_length=file.content_length,
            headers=file.headers
        )
        renamed_files.append(renamed_file)

    return renamed_files

def rename_new_upload_event_images(file_list, event_id, db_path='database.db'):
    renamed_files = []
    start_index = get_next_image_index(event_id)

    for i, file in enumerate(file_list, start=start_index):
        _, ext = os.path.splitext(file.filename)
        new_filename = f"Imj{i}{ext}"

        renamed_file = FileStorage(
            stream=file.stream,
            filename=new_filename,
            content_type=file.content_type,
            content_length=file.content_length,
            headers=file.headers
        )
        renamed_files.append(renamed_file)

    return renamed_files

def get_user_album_for_event(user_id, event_id):
    """
    Checks if a user already has an album for a specific event.
    Returns a dict with 'user_album_id' and 'user_album_name' if found, otherwise None.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()

            query = '''
            SELECT id, name
            FROM albums
            WHERE user_id = ? AND event_id = ?
            LIMIT 1;
            '''
            cur.execute(query, (user_id, event_id))
            result = cur.fetchone()

            if result:
                user_album_id = result["id"]
                user_album_name = result["name"]
                print(f"[DEBUG] Found album for user {user_id} in event {event_id}: {user_album_name} (ID: {user_album_id})")
                return {
                    "user_album_id": user_album_id,
                    "user_album_name": user_album_name
                }
            else:
                print(f"[INFO] No album found for user {user_id} in event {event_id}")
                return None

    except Exception as e:
        print(f"[ERROR] Exception occurred while checking user album: {str(e)}")
        return None

def parse_datetime(dt_str):
    """Try parsing datetime string with two possible formats."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unknown datetime format: {dt_str}")

def get_time_difference_string(start_str, end_str):
    """
    Calculate difference between start_str and end_str
    and return as 'Xh Ym Zs' string.
    """
    if not start_str or not end_str:
        return None
    try:
        start = parse_datetime(start_str)
        end = parse_datetime(end_str)

        delta = end - start
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours}h {minutes}m {seconds}s"
    except Exception as e:
        print(f"Error in get_time_difference_string: {e}")
        return None
    

def get_all_users():
    """
    Returns a list of all users (id and username) ordered by username.
    Must be used within a Flask request context.
    """
    try:
        conn = get_db_connection()  # gets g.db
        cur = conn.cursor()
        query = '''
        SELECT id, username
        FROM users
        ORDER BY username;
        '''
        cur.execute(query)
        users = cur.fetchall()
        return [dict(user) for user in users]

    except Exception as e:
        print(f"[ERROR] Failed to fetch users: {str(e)}")
        return []
    
def get_username_by_id(user_id):
    """
    Returns the username for a given user_id.
    Returns None if the user is not found or an error occurs.
    Must be called within a Flask request context.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = "SELECT username FROM users WHERE id = ?;"
        cur.execute(query, (user_id,))
        row = cur.fetchone()
        return row["username"] if row else None
    except Exception as e:
        print(f"[ERROR] Failed to fetch username: {e}")
        return None
