from collections import defaultdict
import numpy as np  # Make sure numpy is imported if you're using np.int64
import re
import sqlite3  # Import the sqlite3 module
from datetime import datetime  # Import the datetime module


from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from app.services.album_service import (
    create_album,
    get_album,
    delete_album_service,
    add_images_to_album_service,
    delete_images_all,
    delete_images_album
)
from app.db.dbhelper import get_db_connection
album_bp = Blueprint('album', __name__, url_prefix='/albums')


@album_bp.route('/create', methods=['POST'])
def create_album_route():
    """
    Create a new album for a specific event.
    """
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    # Parse the incoming JSON data
    data = request.get_json()
    event_id = data.get('event_id')
    name = data.get('name')
    visibility = data.get('visibility', 'private')  # Default visibility to 'private'
    user_id = session['user_id']

    # Ensure required fields are present
    if not event_id or not name:
        return jsonify({"error": "Missing required fields: event_id and name"}), 400

    # Call the service function to create the album
    response = create_album(event_id, name, visibility)

    # Separate the response and status code explicitly
    status_code = response.pop("status_code", 500)
    return jsonify(response), status_code



@album_bp.route('/<int:album_id>', methods=['GET'])
def get_album_route(album_id):
    """
    Fetch details and images of a specific album and render the album.html page
    only if the user has permission.
    """
    # Use the service function
    response, status_code = get_album(album_id)

    if status_code != 200:
        return jsonify(response), status_code

    album = response["album"]
    user_id = session.get('user_id')
    is_event_owner = album["event_user_id"] == user_id
    is_album_owner = album.get("album_user_id") == user_id
    is_owner = is_event_owner or is_album_owner

    print("==============================\n\n\n\t\t\tResponse: ", response, "\n\n===========")
    print("==============================\n\n\n\t\t\tsession.get('user_id'): ", user_id, "\n\n===========")
    print(f"\n========================================================\n\n\n\t\t\tIs Owner: {is_owner}\n========================================================")

    # Check access permissions
    if album["visibility"] == "private":
        if not is_event_owner and not is_album_owner:
            return jsonify({"error": "You do not have access to this private album."}), 403

    # Render the album page
    return render_template('album.html', album=album, images=response["images"], is_owner=is_owner)


@album_bp.route('/add-images', methods=['GET', 'POST'])
def add_images_to_album_route():
    """
    Allow the user to add images to a specific album.
    """
    album_id = request.args.get('album_id', type=int)

    if not album_id:
        return "Album ID is required.", 400

    if request.method == 'GET':
        # Fetch album and event details
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Fetch the album and associated event
            query_album = '''
            SELECT a.id AS album_id, a.name AS album_name, e.id AS event_id
            FROM albums a
            JOIN events e ON a.event_id = e.id
            WHERE a.id = ?;
            '''
            cur.execute(query_album, (album_id,))
            album = cur.fetchone()

            if album is None:
                return "Album not found", 404

            # Fetch all event images for the associated event
            query_images = '''
            SELECT id AS image_id, image_path
            FROM event_images
            WHERE event_id = ?;
            '''
            cur.execute(query_images, (album['event_id'],))
            event_images = cur.fetchall()

            return render_template('add_images_to_album.html', album=album, event_images=event_images)

        except Exception as e:
            return {"error": str(e)}, 500

        finally:
            conn.close()

    elif request.method == 'POST':
        # Handle form submission to add images to album
        selected_image_ids = request.form.getlist('image_ids')  # Get selected image IDs
        user_id = session.get('user_id')  # Assuming user ID is stored in session

        # Use the add_images_to_album_service function
        result = add_images_to_album_service(album_id, selected_image_ids, user_id)

        if "error" in result:
            return result, 400  # Return the error message if something went wrong

        return redirect(url_for('album.get_album_route', album_id=album_id))



@album_bp.route('/<int:album_id>', methods=['DELETE'])
def delete_album_route(album_id):
    """
    Delete an album.
    """
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session['user_id']

    # Use the service function
    response, status_code = delete_album_service(album_id, user_id)
    return jsonify(response), status_code



@album_bp.route('/delete-images-all', methods=['POST'])
def delete_images_from_all():
    """
    Deletes images from both album_images and event_images for the all_photos album.
    """
    data = request.json
    image_ids = data.get('imageIds', [])
    event_id = data.get('eventId')

    if not image_ids or not event_id:
        return jsonify({"error": "Invalid request data"}), 400
    print("\n=========================================\n\t\t\tevent_id: ",event_id,"\n==================\n")
    return delete_images_all(image_ids, event_id)


@album_bp.route('/delete-images-album', methods=['POST'])
def delete_images_from_album():
    """
    Deletes images from album_images for a specific album.
    """
    data = request.json
    image_ids = data.get('imageIds', [])
    album_id = data.get('albumId')

    if not image_ids:
        return jsonify({"error": "Invalid request data"}), 400
    print("\n===========================================================================================")
    print("\n\n\n\t\t\tDeleting Selected Images From An Album(Not all_photos) Route\n\n")
    print("===========================================================================================\n")
    return delete_images_album(image_ids,album_id)


def get_event_image_id_by_path(conn, image_path):
    """Helper function to get the event_image_id from the base image path."""
    base_image_name = re.sub(r'_face_\d+\.jpg$', '', image_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM event_images WHERE image_path = ?", (base_image_name,))
    result = cursor.fetchone()
    return result['id'] if result else None

@album_bp.route('/process_album_data', methods=['POST'])
def process_album_data():
    """
    Takes a JSON payload with 'event_id' and 'albums' (where keys are album names
    and values are lists of image filenames). Creates albums and adds images.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    event_id = data.get('event_id')
    if event_id is None:
        return jsonify({'error': 'Missing event_id in the request'}), 400

    albums_data = data.get('albums')
    if not albums_data:
        return jsonify({'error': 'Missing album data in the request'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    results = {}

    for album_name_raw, image_filenames in albums_data.items():
        try:
            album_name = str(album_name_raw)

            # Use the event_id from the request
            cursor.execute("SELECT id FROM albums WHERE event_id = ? AND name = ?", (event_id, album_name))
            album_result = cursor.fetchone()

            if album_result:
                album_id = album_result['id']
                results[album_name] = {'status': 'existing', 'images_added': 0, 'errors': []}
            else:
                created_at = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO albums (event_id, name, visibility, created_at) VALUES (?, ?, ?, ?)",
                    (event_id, album_name, 'private', created_at),
                )
                album_id = cursor.lastrowid
                results[album_name] = {'status': 'created', 'images_added': 0, 'errors': []}

            added_count = 0
            errors = []
            for image_filename in image_filenames:
                image_path = image_filename
                event_image_id = get_event_image_id_by_path(conn, image_path)

                if event_image_id:
                    cursor.execute(
                        "SELECT id FROM album_images WHERE album_id = ? AND event_image_id = ?",
                        (album_id, event_image_id),
                    )
                    already_in_album = cursor.fetchone()
                    cursor.execute(
                        "UPDATE event_images SET status = ? WHERE id = ?",
                        ('sorted', event_image_id)
                    )
                    if already_in_album is None:
                        cursor.execute(
                            "INSERT INTO album_images (album_id, event_image_id, added_at) VALUES (?, ?, ?)",
                            (album_id, event_image_id, datetime.now().isoformat()),
                        )
                        added_count += 1
                    else:
                        errors.append(f"Image '{image_filename}' already in album '{album_name}'.")
                else:
                    errors.append(f"Event image with path '{image_path}' not found.")

            results[album_name]['images_added'] = added_count
            if errors:
                results[album_name]['errors'] = errors

            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            return jsonify({'error': f'Database error processing album {album_name}: {e}'}), 500
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Error processing album {album_name}: {e}'}), 500
        finally:
            pass
    try:
        cursor.execute(
            "UPDATE events SET status = ? WHERE id = ?",
            ('sorted', event_id)
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': f'Failed to update event status: {e}'}), 500
    finally:
        conn.close()
        
    return jsonify(results), 200


@album_bp.route('/<int:album_id>/claim', methods=['POST'])
def claim_album(album_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if album exists
        cursor.execute("SELECT id FROM albums WHERE id = ?", (album_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": "Album not found"}), 404

        # Claim the album
        cursor.execute("UPDATE albums SET user_id = ? WHERE id = ?", (user_id, album_id))
        db.commit()

        return redirect(url_for('album_bp.get_album_route', album_id=album_id))
    except Exception as e:
        db.rollback()
        print("Error claiming album:", e)
        return jsonify({"error": "Failed to claim album"}), 500
