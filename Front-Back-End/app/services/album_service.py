from flask import jsonify
import os
from app.db.dbhelper import get_db_connection
from app.utils.file_utils import (
    create_event_folder, 
    add_image_to_album, 
    delete_album, 
    create_album_folder,
    delete_image_files
    ) 
import sqlite3

def create_album(event_id, name, visibility="private", user_id=None):
    """
    Creates a new album for a given event. Verifies permissions and ensures unique constraints.
    Creates a corresponding folder for the album.
    Returns a dictionary with the result and a 'status_code'.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()

            # Verify that the event exists and belongs to the logged-in user
            cur.execute("SELECT user_id FROM events WHERE id = ?;", (event_id,))
            event = cur.fetchone()

            if event is None:
                return {"error": "Event not found", "status_code": 404}
            
            # Check authorization (if the event requires ownership verification)
            if user_id is not None and event['user_id'] != user_id:
                return {"error": "Unauthorized to create an album for this event", "status_code": 403}

            # Check if an album with the same name already exists for the event
            cur.execute("SELECT id FROM albums WHERE event_id = ? AND name = ?;", (event_id, name))
            if cur.fetchone():
                return {"error": f"An album with the name '{name}' already exists for this event.", "status_code": 400}

            # Insert the album into the database
            cur.execute('''
                INSERT INTO albums (event_id, user_id, name, visibility, created_at)
                VALUES (?, ?, ?, ?, datetime('now'));
            ''', (event_id, user_id, name, visibility))
            conn.commit()

            # Retrieve the newly created album ID
            album_id = cur.lastrowid

            # Create a folder for the album
            folder_creation_result = create_album_folder(event_id, name)
            if "error" in folder_creation_result:
                # Roll back the database transaction if folder creation fails
                conn.rollback()
                return {
                    "error": f"Failed to create folder for album: {folder_creation_result['error']}",
                    "status_code": 500
                }

            # Success response
            print(f"Album '{name}' created successfully for Event ID: {event_id} (Album ID: {album_id})")
            return {"success": True, "album_id": album_id, "status_code": 201}

    except Exception as e:
        print(f"Error creating album: {e}")
        return {"error": "An internal server error occurred while creating the album.", "status_code": 500}


def get_album(album_id):
    """
    Fetches details and images of a specific album, including the associated event_id 
    and event's user_id.
    """
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Fetch album details
        query_album = '''
        SELECT a.id AS album_id, a.name AS album_name, a.visibility, a.created_at, a.user_id AS album_user_id,
               e.user_id AS event_user_id, e.name AS event_name, e.id AS event_id
        FROM albums a
        JOIN events e ON a.event_id = e.id
        WHERE a.id = ?;
        '''
        cur.execute(query_album, (album_id,))
        album = cur.fetchone()

        if album is None:
            return {"error": "Album not found"}, 404

        # Fetch images
        query_images = '''
        SELECT ei.id AS image_id, ei.image_path
        FROM album_images ai
        JOIN event_images ei ON ai.event_image_id = ei.id
        WHERE ai.album_id = ?;
        '''
        cur.execute(query_images, (album_id,))
        images = [{"id": row["image_id"], "path": row["image_path"]} for row in cur.fetchall()]

        return {
            "album": {
                "id": album["album_id"],
                "name": album["album_name"],
                "visibility": album["visibility"],
                "created_at": album["created_at"],
                "album_user_id": album["album_user_id"],
                "event_user_id": album["event_user_id"],
                "event_name": album["event_name"],
                "event_id": album["event_id"]
            },
            "images": images
        }, 200

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, 500



def delete_album_service(album_id, user_id):
    """
    Deletes an album and its associated symbolic links and images.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()  # Manually create the cursor
            
            # Verify the album exists and belongs to the user's event
            query = '''
            SELECT a.event_id, a.name, e.user_id
            FROM albums a
            JOIN events e ON a.event_id = e.id
            WHERE a.id = ? AND e.user_id = ?;
            '''
            cur.execute(query, (album_id, user_id))
            album = cur.fetchone()

            if album is None:
                return {"error": "Unauthorized or album not found"}, 404

            # Extract event_id and album_name
            event_id = album['event_id']
            album_name = album['name']

            # Delete related records from album_images
            try:
                cur.execute("DELETE FROM album_images WHERE album_id = ?;", (album_id,))
            except Exception as album_images_error:
                print(f"Error deleting related images for album_id {album_id}: {album_images_error}")
                return {"error": "Failed to delete related images"}, 500

            # Delete symbolic links/files associated with the album
            try:
                delete_album(event_id=event_id, album_name=album_name)  # Pass event_id and album_name
            except Exception as file_error:
                print(f"Error deleting album files for album '{album_name}' in event {event_id}: {file_error}")
                return {"error": "Failed to delete album files"}, 500

            # Delete the album entry from the database
            cur.execute("DELETE FROM albums WHERE id = ?;", (album_id,))
            conn.commit()

        return {"success": True}, 200
    except Exception as e:
        print(f"Error in delete_album_service: {e}")
        return {"error": str(e)}, 500


def add_images_to_album_service(album_id, event_image_ids, user_id):
    """
    Adds multiple images to a specific album by managing database entries only.
    :param album_id: The ID of the album where the images will be added.
    :param event_image_ids: A list of IDs of images in the event_images table to be added.
    :param user_id: The ID of the current user to verify album ownership.
    :return: A dictionary with a success or error message, and a status code.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Verify the album belongs to the user's event
        query_album = '''
        SELECT e.id AS event_id, e.user_id
        FROM albums a
        JOIN events e ON a.event_id = e.id
        WHERE a.id = ?;
        '''
        cur.execute(query_album, (album_id,))
        album = cur.fetchone()

        if album is None:
            return {"error": "Album not found"}, 404

        if album['user_id'] != user_id:
            return {"error": "Unauthorized access to this album"}, 403

        # Verify that each event_image_id exists in event_images for the album's event
        valid_image_ids = []
        for event_image_id in event_image_ids:
            query_image = '''
            SELECT id
            FROM event_images
            WHERE id = ? AND event_id = ?;
            '''
            cur.execute(query_image, (event_image_id, album['event_id']))
            if cur.fetchone():
                valid_image_ids.append(event_image_id)

        # If no valid images are found, return an error
        if not valid_image_ids:
            return {"error": "No valid images found to add to the album"}, 400

        # Insert all valid images into the album_images table
        query_insert = '''
        INSERT INTO album_images (album_id, event_image_id, added_at)
        VALUES (?, ?, datetime('now'));
        '''
        for event_image_id in valid_image_ids:
            cur.execute(query_insert, (album_id, event_image_id))

        conn.commit()

        return {"success": True, "added_images": len(valid_image_ids)}, 200

    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        conn.close()



def add_all_photos_to_album_db(event_id, user_id):
    """
    Adds all event images to the 'all_photos' album in the database.
    
    :param event_id: The ID of the event to which the images belong.
    :param user_id: The ID of the current user to verify ownership of the event.
    :return: A dictionary with either a success message or an error message.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch the 'all_photos' album_id for the given event and user
        query_album = '''
        SELECT a.id AS album_id
        FROM albums a
        JOIN events e ON a.event_id = e.id
        WHERE a.event_id = ? AND a.name = 'all_photos' AND e.user_id = ?;
        '''
        cur.execute(query_album, (event_id, user_id))
        album_result = cur.fetchone()

        if album_result is None:
            return {"error": "Could not find 'all_photos' album for the event."}

        album_id = album_result[0]  # Fetch the first column (album_id)

        # Fetch all event_image_ids linked to this event
        query_event_images = '''
        SELECT id
        FROM event_images
        WHERE event_id = ?;
        '''
        cur.execute(query_event_images, (event_id,))
        event_images_results = cur.fetchall()

        if not event_images_results:
            return {"error": "No images found for the event."}

        # Insert all event_image_ids into the album_images table
        query_insert = '''
        INSERT INTO album_images (album_id, event_image_id, added_at)
        VALUES (?, ?, datetime('now'));
        '''
        for image in event_images_results:
            cur.execute(query_insert, (album_id, image[0]))  # Access the first column (event_image_id)
        
        conn.commit()
        return {"success": f"All event images added to 'all_photos' album (album_id: {album_id})."}

    except Exception as e:
        return {"error": f"Database error occurred: {str(e)}"}

    finally:
        conn.close()


def delete_images_all(image_ids, event_id):
    """
    Deletes images from both event_images and album_images tables,
    and removes the actual image files from the filesystem.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()

            # Fetch image paths before deletion
            cur.execute(
                "SELECT image_path FROM event_images WHERE id IN ({}) AND event_id = ?".format(
                    ','.join('?' * len(image_ids))
                ),
                (*image_ids, event_id)
            )
            image_paths = [row['image_path'] for row in cur.fetchall()]

            # Delete from album_images first to satisfy foreign key constraints
            cur.execute(
                "DELETE FROM album_images WHERE event_image_id IN ({})".format(
                    ','.join('?' * len(image_ids))
                ),
                image_ids
            )

            # Then delete from event_images
            cur.execute(
                "DELETE FROM event_images WHERE id IN ({}) AND event_id = ?".format(
                    ','.join('?' * len(image_ids))
                ),
                (*image_ids, event_id)
            )

            # Remove the image files from disk
            delete_image_files(event_id, image_paths)

            conn.commit()
            return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Error in delete_images_all: {e}")
        return jsonify({"error": str(e)}), 500


def delete_images_album(image_ids, album_id):
    """
    Deletes images from album_images only, filtering by album_id and event_image_ids.
    """
    try:        
        with get_db_connection() as conn:
            cur = conn.cursor()
            print("\n===========================================================================================")
            print("\n\n\n\t\t\tdelete_images_album from album_service:")
            print("album_id:", album_id)
            print("image_ids:", image_ids)
            print("===========================================================================================\n")
            
            # Build placeholders for the image_ids
            placeholders = ','.join('?' * len(image_ids))
            # The query now filters both by album_id and event_image_id
            query = f"""
                DELETE FROM album_images 
                WHERE album_id = ? AND event_image_id IN ({placeholders});
            """
            # Parameters: album_id first, then all the image_ids
            params = [album_id] + image_ids
            
            cur.execute(query, params)
            conn.commit()
            return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Error in delete_images_album: {e}")
        return jsonify({"error": str(e)}), 500
