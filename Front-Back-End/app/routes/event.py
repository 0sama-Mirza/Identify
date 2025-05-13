from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from app.utils.helpers import (
    validate_required_fields, 
    is_logged_in, 
    get_logged_in_user, 
    get_event_image_id_via_image_path,
    rename_event_images
)
from app.services.event_service import (
    get_all_public_events,
    get_event_by_id,
    create_event,
    update_event,
    delete_event,
    get_user_events,
    set_banner_image
)
from app.db.dbhelper import get_db_connection


event_bp = Blueprint('event', __name__, url_prefix='/events')

@event_bp.route('/', methods=['GET'])
def get_user_events_route():
    """
    Fetches all events created by the logged-in user.
    """
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated

    user_id = session['user_id']
    response, status_code = get_user_events(user_id)  # Fetch user's events
    print("\n=========== Getting User Events! ===========\n")
    if status_code == 200:  # Success
        events = response.get('events', [])  # Extract events from response
        return render_template('my_events.html', events=events)  # Render the My Events page
    else:  # Handle errors
        error = response.get('error', 'Unable to fetch your events.')
        return render_template('my_events.html', events=[], error=error)


@event_bp.route('/create', methods=['GET', 'POST'])
def create_event_route():
    """
    Handles event creation:
    - GET: Displays the event creation form.
    - POST: Processes form submission to create a new event.
    """
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Redirect to login page if user is not authenticated

    if request.method == 'POST':
        # Ensure user is logged in (double-check for API calls)
        if not is_logged_in():
            return jsonify({"error": "User not logged in"}), 401

        # Retrieve submitted form data
        event_name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        event_date = request.form.get('event_date')
        location = request.form.get('location')
        num_attendees = request.form.get('num_attendees', 0)  # Default to 0 if not provided
        visibility = request.form.get('visibility', 'public')
        is_public = 1 if visibility == 'public' else 0
        event_images = request.files.getlist('event_images')  # Multiple images allowed
        event_images = rename_event_images(event_images)
        # Validate required fields
        required_fields = ["name", "event_date", "location"]
        missing_fields = validate_required_fields(request.form, required_fields)
        if missing_fields:
            return render_template('create_event.html', error=f"Missing required fields: {', '.join(missing_fields)}")

        # Convert num_attendees to an integer
        try:
            num_attendees = int(num_attendees)
        except ValueError:
            return render_template('create_event.html', error="Number of attendees must be a valid integer.")

        # Get the logged-in user's details
        user = get_logged_in_user()

        # Call the create_event service function
        response, status_code = create_event(
            user_id=user['user_id'], 
            name=event_name, 
            description=description, 
            category=category, 
            event_date=event_date, 
            location=location, 
            num_attendees=num_attendees, 
            is_public=is_public, 
            event_images=event_images
        )

        # Debugging output
        print("\n=========== Debugging Event Creation Data ===========\n")
        print(f"User: {user}, Visibility: {visibility}\n\n")
        print(f"Event Name: {event_name}, Description: {description}, Category: {category}\n")
        print(f"Event Date: {event_date}, Location: {location}, Attendees: {num_attendees}\n")
        print(f"Service Response: {response}, Status Code: {status_code}\n")
        print("=====================================================\n")

        if status_code == 201:
            # Redirect to "My Events" page on success
            return redirect(url_for('event.get_user_events_route'))
        else:
            # Render form with error message on failure
            error_message = response.get('error', 'Failed to create event.')
            return render_template('create_event.html', error=error_message)

    # Handle GET request: Render the event creation form
    return render_template('create_event.html')



@event_bp.route('/<int:event_id>', methods=['GET'])
def get_event_route(event_id):
    """
    Fetches and displays details for a specific event. Only allows the owner to edit the event.
    """
    # Open a database connection
    conn = get_db_connection()
    try:
        # Fetch the event details
        event = get_event_by_id(event_id, conn)

        # Get the logged-in user ID from the session
        user_id = session.get('user_id')  # Replace this with your authentication method
        print(f"Logged-in User ID: {user_id}")

        # Add an 'is_owner' flag to check ownership
        if event:
            is_owner = event["user_id"] == user_id  # Compare event's user_id with logged-in user_id
            print(f"Is Owner: {is_owner}")

            # Fetch albums associated with the event, filtering out "All Photos"
            cur = conn.cursor()
            cur.execute('''
                SELECT id, name, visibility, created_at
                FROM albums
                WHERE event_id = ? AND name != 'All Photos';
            ''', (event_id,))
            albums = cur.fetchall()

            # Format albums as a list of dictionaries
            album_list = [
                {
                    "id": album["id"],
                    # Render "all_photos" as "All Photos"
                    "name": "All Photos" if album["name"] == "all_photos" else album["name"],
                    "visibility": album["visibility"],
                    "created_at": album["created_at"]
                }
                for album in albums
            ]

            # Render the template with albums passed in context
            return render_template('event_detail.html', event=event, is_owner=is_owner, albums=album_list, user_id=user_id)
        else:
            return "Event not found", 404
    finally:
        # Ensure the database connection is closed
        conn.close()



@event_bp.route('/<int:event_id>', methods=['PUT'])
def update_event_route(event_id):
    """
    Updates an existing event by its ID using a shared database connection.
    """
    print(f"Request Method: {request.method}")
    print(f"Request JSON Data: {request.get_json()}")

    if not is_logged_in():
        return jsonify({"error": "User not logged in"}), 401

    user = get_logged_in_user()
    if not user or "user_id" not in user:
        return jsonify({"error": "User information is incomplete"}), 400

    data = request.get_json()

    # Open a shared database connection
    conn = get_db_connection()
    try:
        # Fetch event details using the shared connection
        event = get_event_by_id(event_id, conn)
        if event is None:
            return jsonify({"error": "Event not found"}), 404
        if event["user_id"] != user["user_id"]:
            return jsonify({"error": "Unauthorized"}), 403

        # Update the event using the shared connection
        response, status_code = update_event(event_id, user["user_id"], data, conn)
        return jsonify(response), status_code
    finally:
        conn.close()  # Ensure the connection is closed after all operations

@event_bp.route('/<int:event_id>', methods=['DELETE'])
def delete_event_route(event_id):
    """
    Deletes an event by its ID.
    """
    if not is_logged_in():
        return jsonify({"error": "User not logged in"}), 401

    user = get_logged_in_user()

    # Call the service function
    response, status_code = delete_event(event_id, user['user_id'])
    return jsonify(response), status_code


@event_bp.route('/event/<int:event_id>/photos', methods=['GET'])
def event_photos(event_id):
    """
    Displays all photos for a specific event.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Query to fetch all photos for the event
        query = """
            SELECT filename 
            FROM photos 
            WHERE event_id = %s;
        """
        cur.execute(query, (event_id,))
        photos = [row['filename'] for row in cur.fetchall()]  # List of photo filenames
    except Exception as e:
        print(f"Error fetching photos: {e}")
        photos = []  # Default to an empty list if there's an error
    finally:
        conn.close()

    return render_template('event_photos.html', event_id=event_id, photos=photos)



@event_bp.route('/<int:event_id>/select_banner', methods=['GET'])
def get_select_banner_page(event_id):
    """
    Renders the page to select a banner image for the event.
    """
    print(f"[DEBUG] Processing GET request for Event ID: {event_id}")

    try:
        # Fetch all images associated with the event
        conn = get_db_connection()
        print("[DEBUG] Database connection established.")
        cur = conn.cursor()

        # Fetch image paths for the event
        print(f"[DEBUG] Executing query to fetch images for Event ID: {event_id}")
        cur.execute('SELECT image_path FROM event_images WHERE event_id = ?', (event_id,))
        images = [row['image_path'] for row in cur.fetchall()]
        print(f"[DEBUG] Retrieved {len(images)} images for Event ID: {event_id}")
        conn.close()

        # Render the selection page template
        print(f"[DEBUG] Rendering select_banner.html for Event ID: {event_id}")
        return render_template('select_banner.html', event_id=event_id, images=images)

    except Exception as e:
        print(f"[ERROR] Exception occurred during GET request processing: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@event_bp.route('/<int:event_id>/select_banner', methods=['POST'])
def select_banner_post(event_id):
    """
    Handles the banner image update (POST) for an event.
    """
    print(f"[DEBUG] Received POST request for Event ID: {event_id}")

    try:
        # Parse request data
        data = request.get_json()
        print(f"[DEBUG] Received JSON payload: {data}")

        selected_image = data.get('banner_image')
        if not selected_image:
            print("[ERROR] No banner image selected in POST request.")
            return jsonify({"error": "No banner image selected."}), 400

        print(f"[DEBUG] Selected image: {selected_image}")

        # Update banner using set_banner_image function
        print(f"[DEBUG] Calling set_banner_image for Event ID: {event_id} with image: {selected_image}")
        event_image_idx = get_event_image_id_via_image_path(selected_image)
        result = set_banner_image(event_id, select_image=event_image_idx)

        if "error" in result:
            print(f"[ERROR] Failed to set banner image: {result['error']}")
            return jsonify({"error": result['error']}), 400

        print(f"[INFO] Banner image successfully updated to {result['banner_image']} for Event ID: {event_id}")
        return jsonify({"success": True, "banner_image": result['banner_image']}), 200

    except Exception as e:
        print(f"[ERROR] Exception occurred during POST request processing: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500



@event_bp.route('/confirm-identity', methods=['POST'])
def confirm_identity_route():
    """
    Handles identity confirmation from popup.
    Looks up album_id based on event_id and album_name.
    """
    data = request.json
    album_name = data.get('album_name')
    event_id = data.get('event_id')

    if not album_name or not event_id:
        return jsonify({'error': 'Missing album_name or event_id'}), 400

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT id FROM albums
            WHERE event_id = ? AND name = ?
            ''',
            (event_id, album_name)
        )
        album = cur.fetchone()

        if not album:
            return jsonify({'error': 'Album not found'}), 404

        return jsonify({'album_id': album['id']}), 200

    except Exception as e:
        print(f"Error during album lookup: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()
