from flask import Blueprint, request, jsonify, session, current_app, send_from_directory, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app.services.image_service import add_images_to_event_db, link_image_to_album
from app.utils.helpers import validate_required_fields, is_logged_in, rename_new_upload_event_images
from app.services.album_service import add_images_to_album_service
from app.services.event_service import set_banner_image, update_event_status
from app.db.dbhelper import get_db_connection
import os

uploads_bp = Blueprint('uploads', __name__, url_prefix='/uploads')



@uploads_bp.route('/event/<int:event_id>/image/<path:filename>', methods=['GET'])
def serve_event_image(event_id, filename):
    """
    Serve an image from the 'original_images' folder for a specific event.
    """
    try:
        # Use UPLOAD_FOLDER from the app configuration
        uploads_dir = current_app.config['UPLOAD_FOLDER']
        
        # Construct the path for the event-specific folder
        event_folder = f"event_{event_id}"
        image_folder = os.path.join(uploads_dir, event_folder, "original_images")

        # Ensure the image exists in the correct folder
        image_path = os.path.join(image_folder, filename)
        
        # Check if the file exists, and return it
        if not os.path.exists(image_path):
            raise FileNotFoundError
        
        return send_from_directory(image_folder, filename)
    
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404



@uploads_bp.route('/event/<int:event_id>/upload', methods=['POST'])
def upload_event_images(event_id):
    """
    Handles uploading images to a specific event and adds them to the "all_photos" album.
    """
    print(f"[INFO] Upload request received for event ID: {event_id}")

    # Step 1: Check user login
    print("\n\n\t\t\t# Step 1: Check user login\n")
    if not is_logged_in():
        print("[ERROR] User not logged in.")
        flash("You must be logged in to upload images.", "error")  # Flash an error message
        return redirect(url_for('auth.login_route'))  # Redirect to login page

    # Step 2: Check if files are included in the request
    print("\n\n\t\t\t# Step 2: Check if files are included in the request\n")
    if 'event_images' not in request.files:
        print("[ERROR] No 'event_images' part found in the request.")
        flash("No file part in the request. Please try again.", "error")  # Flash an error message
        return redirect(url_for('event.get_event_route', event_id=event_id))

    files = request.files.getlist('event_images')
    files = rename_new_upload_event_images(files,event_id)
    print(f"[INFO] Files received: {[file.filename for file in files]}")

    # Step 3: Validate files
    print("\n\n\t\t\t# Step 3: Validate files\n")
    if not files or any(file.filename == '' for file in files):
        print("[ERROR] One or more files are missing a filename.")
        flash("No file(s) selected for upload. Please try again.", "error")  # Flash an error message
        return redirect(url_for('event.get_event_route', event_id=event_id))

    # Step 4: Upload images to the event
    print("\n\n\t\t\t# Step 4: Upload images to the event\n")
    try:
        print(f"[INFO] Uploading images to event ID: {event_id}")
        print("\n***** files: ",files)
        response = add_images_to_event_db(event_id, files)

        # Check for errors from add_images_to_event_db
        if isinstance(response, dict) and response.get('error'):
            print(f"[ERROR] Error during image upload: {response['error']}")
            flash(f"Error uploading images: {response['error']}", "error")  # Flash an error message
            return redirect(url_for('event.get_event_route', event_id=event_id))

        print("[INFO] Images successfully uploaded and added to the database.")

        # ====> Step 4.5: UPDATE EVENT STATUS VIA GENERAL SERVICE <====
        print("\n# Step 4.5: Update event status via service")
        print(f"[ROUTE-INFO] Calling update_event_status for event ID: {event_id} with status 'unsorted'")
        status_updated = update_event_status(event_id, 'unsorted') # Call the new function
        if not status_updated:
            print(f"[ROUTE-WARN] Failed to set event {event_id} status to 'unsorted', but continuing process.")
            # flash("Could not reset event sorting status, processing might be delayed.", "warning")
        else:
            print(f"[ROUTE-INFO] Event status set to 'unsorted' successfully (or event not found).")

    except Exception as e:
        print(f"[ERROR] Exception occurred during image upload: {str(e)}")
        flash(f"An error occurred while uploading images: {str(e)}", "error")  # Flash an error message
        return redirect(url_for('event.get_event_route', event_id=event_id))

    # Step 5: Fetch the "all_photos" album ID for the event
    print("\n\n\t\t\t# Step 5: Fetch the all_photos album ID for the event\n")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        print("[INFO] Fetching 'all_photos' album ID for the event.")
        query = '''
        SELECT id FROM albums WHERE event_id = ? AND name = 'all_photos';
        '''
        cur.execute(query, (event_id,))
        album = cur.fetchone()

        if album is None:
            print("[ERROR] 'all_photos' album not found.")
            flash("Could not find the 'all_photos' album for this event.", "error")  # Flash an error message
            return redirect(url_for('event.get_event_route', event_id=event_id))

        album_id = album['id']
        print(f"[INFO] 'all_photos' album ID: {album_id}")

        # Step 6: Get the IDs of newly uploaded images
        print("\n\n\t\t\t# Step 6: Get the IDs of newly uploaded images\n")
        cur.execute('''
        SELECT id FROM event_images WHERE event_id = ? ORDER BY id DESC LIMIT ?;
        ''', (event_id, len(files)))
        event_image_ids = [row['id'] for row in cur.fetchall()]
        print(f"[INFO] Newly uploaded image IDs: {event_image_ids}")

        # Step 7: Add images to the "all_photos" album
        print("\n\n\t\t\t# Step 7: Add images to the all_photos album\n")
        user_id = session.get('user_id')
        print(f"[INFO] Adding images to 'all_photos' album for user ID: {user_id}")
        album_response = add_images_to_album_service(album_id, event_image_ids, user_id)

        # Check for errors from add_images_to_album_service
        if isinstance(album_response, dict) and album_response.get('error'):
            print(f"[ERROR] Error while adding images to album: {album_response['error']}")
            flash(f"Error adding images to album: {album_response['error']}", "error")  # Flash an error message
            return redirect(url_for('event.get_event_route', event_id=event_id))

    except Exception as e:
        print(f"[ERROR] Exception occurred while processing album: {str(e)}")
        flash(f"An error occurred while adding images to the album: {str(e)}", "error")  # Flash an error message
        return redirect(url_for('event.get_event_route', event_id=event_id))

    finally:
        print("[INFO] Closing database connection.")
        conn.close()

    print("[INFO] Images successfully uploaded and added to 'all_photos' album.")
    flash("Images uploaded successfully!", "success")  # Flash a success message
    return redirect(url_for('event.get_event_route', event_id=event_id))

@uploads_bp.route('/album/<int:album_id>/link', methods=['POST'])
def link_album_image(album_id):
    """
    Links an image to a specific album by creating a symbolic link.
    """
    # Check if user is logged in
    if not is_logged_in():
        return jsonify({"error": "User not logged in"}), 401

    # Validate required fields in the request JSON
    data = request.get_json()
    missing_fields = validate_required_fields(data, ["event_id", "filename"])
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    event_id = data.get('event_id')
    filename = data.get('filename')

    # Call the image service to link the image to the album
    response, status_code = link_image_to_album(event_id, album_id, filename)
    return jsonify(response), status_code
