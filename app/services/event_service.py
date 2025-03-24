from app.db.dbhelper import get_db_connection
from app.utils.helpers import allowed_file                                      # Used in create_event
from app.utils.file_utils import create_event_folder, add_all_images_to_album   # Used in create_event
from app.services.album_service import create_album, add_all_photos_to_album_db # Used in create_event
from app.services.image_service import add_images_to_event_db                   # Used in create_event
from app.utils.file_utils import delete_event_folder                            # Used in delete_event
from flask import current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import random


def get_all_public_events():
    """
    Fetches all public events from the database, including the username of the creator and banner image path.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Query to fetch public events along with the creator's username and banner image path
        query = """
            SELECT 
                e.id, 
                e.user_id, 
                u.username, 
                e.name, 
                e.description, 
                e.category, 
                e.event_date, 
                e.location, 
                e.num_attendees, 
                e.is_public, 
                e.created_at, 
                ei.image_path AS banner_image_path  -- Resolve banner image path using event_images
            FROM events e
            INNER JOIN users u ON e.user_id = u.id  -- Join with users to fetch creator username
            LEFT JOIN event_images ei ON e.banner_image = ei.id  -- Join with event_images to fetch banner image path
            WHERE e.is_public = 1;
        """

        # Execute the query
        cur.execute(query)

        # Fetch all rows and convert each row into a dictionary
        events = [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "created_by": row["username"],
                "name": row["name"],
                "description": row["description"],
                "category": row["category"],
                "event_date": row["event_date"],
                "location": row["location"],
                "num_attendees": row["num_attendees"],
                "is_public": row["is_public"],
                "banner_image": row["banner_image_path"],  # Use resolved image path
                "created_at": row["created_at"]
            }
            for row in cur.fetchall()
        ]

        # Return the events as a JSON-like dictionary with a 200 status code
        return {"events": events}, 200
    except Exception as e:
        # Return the error in case of an exception
        return {"error": str(e)}, 500
    finally:
        # Close the database connection
        conn.close()




def get_event_by_id(event_id, conn):
    """
    Fetches details of a specific event by its ID using a shared connection.
    Includes the image path for the banner image by resolving the foreign key in event_images.
    """
    try:
        # Query to fetch event details including the banner image path
        query = """
            SELECT 
                e.id,
                e.user_id,
                e.name,
                e.description,
                e.category,
                e.event_date,
                e.location,
                e.num_attendees,
                e.is_public,
                e.created_at,
                u.username AS created_by, 
                ei.image_path AS banner_image_path  -- Resolve image path from event_images
            FROM events e
            INNER JOIN users u ON e.user_id = u.id  -- Join with users to fetch creator username
            LEFT JOIN event_images ei ON e.banner_image = ei.id  -- Match banner_image with event_images.id
            WHERE e.id = ?;
        """

        cur = conn.cursor()
        cur.execute(query, (event_id,))
        event = cur.fetchone()

        # Convert row to a dictionary if an event is found
        return {
            "id": event["id"],
            "user_id": event["user_id"],
            "name": event["name"],
            "description": event["description"],
            "category": event["category"],
            "event_date": event["event_date"],
            "location": event["location"],
            "num_attendees": event["num_attendees"],
            "is_public": event["is_public"],
            "created_at": event["created_at"],
            "created_by": event["created_by"],
            "banner_image": event["banner_image_path"],  # Return resolved image path
        } if event else None

    except Exception as e:
        print(f"Error fetching event: {e}")
        return None


def get_user_events(user_id):
    """
    Fetches events created by the user from the database, including the banner image path.
    """
    try:
        # Establish database connection
        with get_db_connection() as conn:
            query = '''
            SELECT e.id, e.name, e.description, e.category, e.event_date, e.location, 
                   e.num_attendees, e.is_public, e.created_at, 
                   ei.image_path AS banner_image_path
            FROM events e
            LEFT JOIN event_images ei ON e.banner_image = ei.id  -- Join with event_images using event_image_id
            WHERE e.user_id = ?
            ORDER BY e.event_date;
            '''
            cur = conn.cursor()
            cur.execute(query, (user_id,))
            rows = cur.fetchall()

            # Convert rows to list of dictionaries
            events = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "category": row["category"],
                    "event_date": row["event_date"],
                    "location": row["location"],
                    "num_attendees": row["num_attendees"],
                    "is_public": row["is_public"],
                    "banner_image": row["banner_image_path"],  # Path to the banner image
                    "created_at": row["created_at"]
                }
                for row in rows
            ]

            return {"events": events}, 200

    except Exception as e:
        print(f"Error fetching user events: {e}")
        return {"error": f"Unable to fetch events. Error: {str(e)}"}, 500



def create_event(user_id, name, description, category, event_date, location, num_attendees, is_public, event_images=None):
    """
    Creates a new event for the logged-in user:
    - Uses the 0th index image from event_images as the banner image.
    - Creates folder structure for the event.
    - Creates an 'all_photos' album for the event.
    - Saves and tracks event images in the event_images table.
    - Creates symbolic links in 'all_photos' album from 'original_images' folder.
    """
    print("\n===================================\nCreate Event Function Running\n===================================")

    banner_image = None
    try:
        # Step 1: Create the event in the database
        print("\n\n\t\t\t\t# Step 1: Create the event in the database\n\n")
        with get_db_connection() as conn:
            cur = conn.cursor()

            query = '''
            INSERT INTO events (user_id, name, description, category, event_date, location, num_attendees, is_public, banner_image, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            '''
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current timestamp
            cur.execute(query, (user_id, name, description, category, event_date, location, num_attendees, is_public, banner_image, created_at))
            conn.commit()

            # Retrieve the event ID
            event_id = cur.lastrowid
            print(f"Event created successfully with ID: {event_id}")

        # Step 2: Create the folder structure for the event
        print("\n\n\t\t\t\t# Step 2: Create the folder structure for the event\n\n")
        event_folders = create_event_folder(event_id)
        print(f"Created folder structure for event ID {event_id}: {event_folders}")

        # Step 3: Create the 'all_photos' album for the event
        print("\n\n\t\t\t\t# Step 3: Create the 'all_photos' album for the event\n\n")
        album_response = create_album(event_id, 'all_photos', 'public',)

        # Handle album creation response
        if album_response.get("status_code") != 201 or "error" in album_response:
            print(f"Error creating album: {album_response.get('error')}")
            return {"error": f"Event created, but failed to create album: {album_response.get('error')}"}, 500

        # Step 4: Handle event images using add_images_to_event_db
        print("\n\n\t\t\t\t# Step 4: Handle event images using add_images_to_event_db\n\n")
        print("\n===========================\nevent_images argument in event_service.py: ", event_images)
        print("\n===========================\n")
        if event_images:
            response = add_images_to_event_db(event_id, event_images)
            print("\n" + "="*50)
            print(f"🟢 RESPONSE TYPE DEBUG: {type(response)}")
            print("="*50 + "\n")
            if response.get("error"):
                print(f"Error handling event images: {response['error']}")
                return {"error": f"Event created, but failed to process images: {response['error']}"}, 500

            # Step 5: Call set_banner_image with the 0th index
            print("\n\n\t\t\t\t# Step 5: Call set_banner_image with the 0th index\n\n")
            banner_response = set_banner_image(event_id, select_image=-1)
            if "error" in banner_response:
                print(f"Error setting banner image: {banner_response['error']}")
                return {"error": f"Event created, but failed to set banner image: {banner_response['error']}"}, 500

        # Step 6: Create symbolic links in 'all_photos' album
        print("\n\n\t\t\t\t# Step 6: Create symbolic links in 'all_photos' album\n\n")
        print("\n===========================\nCreating symbolic links for 'all_photos' album\n===========================\n")
        add_all_images_to_album(event_id, album_name="all_photos")
        # Step 7: Insert records into album_images database
        print("\n\n\t\t\t\t# Step 7: Insert records into album_images database\n\n")
        add_all_photos_response = add_all_photos_to_album_db(event_id, user_id)

        if add_all_photos_response.get("error"):
            print(f"Error adding images to 'all_photos': {add_all_photos_response['error']}")
            return {"error": f"Event created, but failed to add images to 'all_photos' album: {add_all_photos_response['error']}"}, 500

        return {"success": True, "event_id": event_id, "album_id": album_response.get("album_id")}, 201

    except Exception as e:
        print(f"Database error while creating event: {e}")
        return {"error": f"Database error: {str(e)}"}, 500




def set_banner_image(event_id, select_image=-1):
    """
    Updates the banner image for a given event.

    Args:
        event_id (int): The ID of the event to update the banner image for.
        select_image (int): Either -1 to select the first image using LIMIT 1,
                            or the ID of the image from the event_images table.

    Returns:
        dict: A success or error response.
    """
    print(f"\n\n[DEBUG] Setting Banner Image for Event ID: {event_id}, select_image: {select_image}")

    try:
        # Case 1: select_image = -1
        if select_image == -1:
            with get_db_connection() as conn:
                cur = conn.cursor()
                print("[DEBUG] Fetching one image path using LIMIT 1...")
                query = '''
                SELECT id 
                FROM event_images 
                WHERE event_id = ? 
                LIMIT 1;
                '''
                cur.execute(query, (event_id,))
                result = cur.fetchone()

                if result:
                    selected_image = result["id"]
                    print(f"[DEBUG] Selected Image (LIMIT 1): {selected_image}")

                    # Update banner_image in the events table
                    update_query = '''
                    UPDATE events 
                    SET banner_image = ? 
                    WHERE id = ?;
                    '''
                    cur.execute(update_query, (selected_image, event_id))
                    conn.commit()
                    print(f"[INFO] Banner image updated to '{selected_image}' for Event ID {event_id}")
                    return {"success": True, "banner_image": selected_image}
                else:
                    print("[ERROR] No images found for the given event ID.")
                    return {"error": "No images found for the given event ID."}

        # Case 2: select_image is a specific ID in the event_images table
        else:
            with get_db_connection() as conn:
                cur = conn.cursor()
                print("[DEBUG] Fetching image path for the specific event_image ID...")
                query = '''
                SELECT image_path 
                FROM event_images 
                WHERE id = ?;
                '''
                cur.execute(query, (select_image,))
                result = cur.fetchone()

                if result:
                    selected_image = result["image_path"]
                    print(f"[DEBUG] Selected Image (event_image ID {select_image}): {selected_image}")

                    # Update banner_image in the events table
                    update_query = '''
                    UPDATE events 
                    SET banner_image = ? 
                    WHERE id = ?;
                    '''
                    cur.execute(update_query, (select_image, event_id))
                    conn.commit()
                    print(f"[INFO] Banner image updated to '{selected_image}' for Event ID {event_id}")
                    return {"success": True, "banner_image": selected_image}
                else:
                    print(f"[ERROR] No image found for event_image ID: {select_image}")
                    return {"error": f"No image found for event_image ID: {select_image}"}

    except Exception as e:
        print(f"[ERROR] Exception occurred while setting banner image for Event ID {event_id}: {e}")
        return {"error": f"Failed to set banner image: {str(e)}"}




def update_event(event_id, user_id, updates, conn):
    """
    Updates an event's details using a shared connection.
    """
    cur = conn.cursor()

    try:
        # Validate ownership of the event
        cur.execute("SELECT user_id FROM events WHERE id = ?;", (event_id,))
        event = cur.fetchone()

        if event is None:
            return {"error": "Event not found"}, 404
        if event["user_id"] != user_id:
            return {"error": "Unauthorized to update this event"}, 403

        if not updates:
            return {"error": "No valid fields to update"}, 400

        # Dynamic SQL query
        fields = ", ".join([f"{key} = COALESCE(?, {key})" for key in updates.keys()])
        values = list(updates.values()) + [event_id]
        query = f"UPDATE events SET {fields} WHERE id = ?;"
        cur.execute(query, values)
        conn.commit()

        return {"success": True}, 200
    except Exception as e:
        print(f"Error during update: {str(e)}")
        return {"error": "Database operation failed"}, 500




def delete_event(event_id, user_id):
    """
    Deletes an event, but only if the user owns it.
    Also deletes all related data (event_images, albums, album_images).
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        with conn:  # Wrap all operations in a transaction
            # Check event ownership
            print(f"[DEBUG] Checking ownership for event ID {event_id}")
            cur.execute("SELECT user_id FROM events WHERE id = ?;", (event_id,))
            event = cur.fetchone()

            if event is None:
                print(f"[ERROR] Event ID {event_id} not found")
                return {"error": "Event not found"}, 404
            if event['user_id'] != user_id:
                print(f"[ERROR] Unauthorized deletion attempt by user {user_id} for event ID {event_id}")
                return {"error": "Unauthorized to delete this event"}, 403

            # Cascade delete related data
            print(f"[DEBUG] Deleting related data for event ID {event_id}")

            # Delete album_images linked to this event
            cur.execute('''
                DELETE FROM album_images 
                WHERE album_id IN (SELECT id FROM albums WHERE event_id = ?);
            ''', (event_id,))

            # Delete albums linked to this event
            cur.execute("DELETE FROM albums WHERE event_id = ?;", (event_id,))

            # Delete event_images linked to this event
            cur.execute("DELETE FROM event_images WHERE event_id = ?;", (event_id,))

            # Finally, delete the event itself
            print(f"[DEBUG] Deleting event ID {event_id}")
            cur.execute("DELETE FROM events WHERE id = ?;", (event_id,))

            print(f"[INFO] Event ID {event_id} and its related data deleted successfully")
            delete_event_folder(event_id)
            return {"success": True}, 200

    except sqlite3.IntegrityError as e:
        print(f"[ERROR] Database integrity error: {str(e)}")
        return {"error": "Database integrity error occurred"}, 500
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    finally:
        conn.close()
        print(f"[DEBUG] Database connection closed")

