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
    Fetch details and images of a specific album and render the album.html page.
    """
    # Use the service function
    response, status_code = get_album(album_id)

    if status_code != 200:
        # Handle errors gracefully
        return jsonify(response), status_code
    is_owner = response["album"]["event_user_id"] == session.get('user_id')
    print("==============================\n\n\n\t\t\tResponse: ",response,"\n\n===========")
    print("==============================\n\n\n\t\t\tsession.get(\'user_id\'): ",session.get('user_id'),"\n\n===========")
    # print(f"\n========================================================\n\n\n\t\t\tresponse[\"album\"][\"user_id\"]:", response["user_id"],"\n========================================================")
    print(f"\n========================================================\n\n\n\t\t\tIs Owner: {is_owner}\n========================================================")
    # Render the album.html template with album details and images
    return render_template('album.html', album=response["album"], images=response["images"], is_owner=is_owner)


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