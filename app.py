import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # NOTE: Change this for production use!

# Define the directory for uploaded images relative to the application root
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
# Create the directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Configure the upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
print(f"UPLOAD_FOLDER is set to: {app.config['UPLOAD_FOLDER']}")  # Debugging output

# Create folders for "All Photos" and "Albums" during event creation
def create_event_folders(event_id):
    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}")
    all_photos_folder = os.path.join(event_folder, "all_photos")
    albums_folder = os.path.join(event_folder, "albums")
    os.makedirs(all_photos_folder, exist_ok=True)
    os.makedirs(albums_folder, exist_ok=True)


# Allowed extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

DATABASE = os.path.join(app.root_path, 'database.db')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Users table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TEXT NOT NULL
                  )''')
    
    # Events table with is_public and banner_image
    cur.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    event_date TEXT,
                    location TEXT,
                    num_attendees INTEGER,
                    is_public INTEGER DEFAULT 1,
                    banner_image TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                  )''')

    # Event images table (All Photos folder automatically stores uploaded images)
    cur.execute('''CREATE TABLE IF NOT EXISTS event_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    image_path TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES events(id)
                  )''')

    # Albums table for organizing photos
    cur.execute('''CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    visibility TEXT NOT NULL CHECK (visibility IN ('public', 'private')),
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES events(id)
                  )''')

    # Album images table for associating images with albums
    cur.execute('''CREATE TABLE IF NOT EXISTS album_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    album_id INTEGER NOT NULL,
                    image_path TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    FOREIGN KEY(album_id) REFERENCES albums(id)
                  )''')

    conn.commit()
    conn.close()



# Initialize database
init_db()

# ============================
# User Registration & Login
# ============================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for('register'))

        if len(username) < 3 or len(username) > 20:
            flash("Username must be between 3 and 20 characters.")
            return redirect(url_for('register'))

        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return redirect(url_for('register'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                        (username, hashed_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose a different username.")
            conn.close()
            return redirect(url_for('register'))
        conn.close()
        flash("Registration successful. Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Logged in successfully.")
            return redirect(url_for('events'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))

# A simple decorator to ensure the user is logged in
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================
# Event Management Routes
# ============================
@app.route('/')
def home():
    # If the user is logged in, redirect to their events/dashboard page.
    if 'user_id' in session:
        return redirect(url_for('events'))
    # Otherwise, show the landing page.
    return render_template('landing.html')

@app.route('/events')
@login_required
def events():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    events = cur.fetchall()

    events_list = []
    for event in events:
        # Prepare event details (exclude images here to simplify)
        events_list.append({
            'id': event['id'],
            'name': event['name'],
            'description': event['description'],
            'category': event['category'],
            'event_date': event['event_date'],
            'location': event['location'],
            'num_attendees': event['num_attendees'],
            'is_public': event['is_public'],
            'banner_image': event['banner_image'],  # Include banner image for display
            'created_at': event['created_at']
        })
    
    conn.close()
    return render_template('events.html', events=events_list)


@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        # Collect and validate form data
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        event_date = request.form.get('event_date', '').strip()
        location = request.form.get('location', '').strip()
        num_attendees = request.form.get('num_attendees', '0').strip()
        
        # Validate input fields
        if not name:
            flash("Event name is required.")
            return redirect(url_for('create_event'))
        if len(name) > 50:
            flash("Event name must be less than 50 characters.")
            return redirect(url_for('create_event'))
        if len(description) > 500:
            flash("Description must be less than 500 characters.")
            return redirect(url_for('create_event'))
        
        try:
            num_attendees = int(num_attendees)
            if num_attendees < 0:
                raise ValueError("Negative attendees are not allowed.")
        except ValueError:
            flash("Number of attendees must be a positive number.")
            return redirect(url_for('create_event'))
        
        # Visibility setting
        visibility = request.form.get('visibility', 'public')
        is_public = 1 if visibility == 'public' else 0

        # Database operation
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Insert the event into the database
            cur.execute('''INSERT INTO events (user_id, name, description, category, event_date, location, num_attendees, is_public, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (session['user_id'], name, description, category, event_date, location, num_attendees, is_public, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            event_id = cur.lastrowid

            # Create folder structure for the event
            event_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}")
            all_photos_folder = os.path.join(event_folder, "all_photos")
            albums_folder = os.path.join(event_folder, "albums")
            os.makedirs(all_photos_folder, exist_ok=True)
            os.makedirs(albums_folder, exist_ok=True)

            # Process the Banner Image
            banner_file = request.files.get('banner')
            if banner_file and allowed_file(banner_file.filename):
                filename = secure_filename(banner_file.filename)
                unique_filename = f"{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(all_photos_folder, unique_filename)  # Save banner in all_photos folder
                banner_file.save(filepath)
                # Update the event's banner_image column
                cur.execute("UPDATE events SET banner_image = ? WHERE id = ?", (f"event_{event_id}/all_photos/{unique_filename}", event_id))
                # Add the banner image to the event_images table
                cur.execute('''INSERT INTO event_images (event_id, image_path, uploaded_at)
                            VALUES (?, ?, ?)''',
                            (event_id, f"event_{event_id}/all_photos/{unique_filename}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            # Process Additional Images
            if 'images' in request.files:
                images = request.files.getlist('images')
                for image in images:
                    if image and allowed_file(image.filename):
                        filename = secure_filename(image.filename)
                        unique_filename = f"{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                        filepath = os.path.join(all_photos_folder, unique_filename)  # Save images in all_photos folder
                        image.save(filepath)
                        cur.execute('''INSERT INTO event_images (event_id, image_path, uploaded_at)
                                    VALUES (?, ?, ?)''',
                                    (event_id, f"event_{event_id}/all_photos/{unique_filename}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            flash("Event created successfully.")
        except Exception as e:
            flash(f"An error occurred: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

        return redirect(url_for('events'))
    
    return render_template('create_event.html')

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch event details
    cur.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, session['user_id']))
    event = cur.fetchone()
    if not event:
        conn.close()
        flash("Event not found or unauthorized.")
        return redirect(url_for('events'))
    
    # Folder paths for the event
    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}")
    all_photos_folder = os.path.join(event_folder, "all_photos")
    albums_folder = os.path.join(event_folder, "albums")
    
    # Ensure folder structure exists
    try:
        os.makedirs(all_photos_folder, exist_ok=True)
        os.makedirs(albums_folder, exist_ok=True)
    except OSError as e:
        flash(f"Error creating folders: {e}")
        return redirect(url_for('events'))

    if request.method == 'POST':
        # Collect form data
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        event_date = request.form.get('event_date', '').strip()
        location = request.form.get('location', '').strip()
        num_attendees = request.form.get('num_attendees', '0').strip()
        try:
            num_attendees = int(num_attendees)
            if num_attendees < 0:
                raise ValueError("Number of attendees cannot be negative.")
        except ValueError:
            flash("Invalid number of attendees.")
            return redirect(url_for('edit_event', event_id=event_id))
        
        visibility = request.form.get('visibility', 'public')
        is_public = 1 if visibility == 'public' else 0
        
        if not name:
            flash("Event name is required.")
            return redirect(url_for('edit_event', event_id=event_id))
        
        # Update event details
        try:
            cur.execute('''UPDATE events SET name = ?, description = ?, category = ?, event_date = ?, location = ?, 
                           num_attendees = ?, is_public = ? WHERE id = ?''',
                        (name, description, category, event_date, location, num_attendees, is_public, event_id))
            
            # Handle new banner image upload
            banner_file = request.files.get('banner')
            if banner_file and allowed_file(banner_file.filename):
                filename = secure_filename(banner_file.filename)
                unique_filename = f"{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(all_photos_folder, unique_filename)  # Save banner to all_photos
                banner_file.save(filepath)
                banner_path = f"event_{event_id}/all_photos/{unique_filename}"
                cur.execute("UPDATE events SET banner_image = ? WHERE id = ?", (banner_path, event_id))
                # Add banner to event_images table
                cur.execute('''INSERT INTO event_images (event_id, image_path, uploaded_at)
                               VALUES (?, ?, ?)''',
                            (event_id, banner_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            # Handle additional image uploads
            if 'images' in request.files:
                images = request.files.getlist('images')
                for image in images:
                    if image and allowed_file(image.filename):
                        filename = secure_filename(image.filename)
                        unique_filename = f"{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                        filepath = os.path.join(all_photos_folder, unique_filename)
                        image.save(filepath)
                        image_path = f"event_{event_id}/all_photos/{unique_filename}"
                        cur.execute('''INSERT INTO event_images (event_id, image_path, uploaded_at)
                                       VALUES (?, ?, ?)''',
                                    (event_id, image_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            # Update banner selection
            banner_choice = request.form.get('banner_choice')
            if banner_choice:
                cur.execute("UPDATE events SET banner_image = ? WHERE id = ?", (banner_choice, event_id))
            
            # Delete selected images
            delete_image_ids = request.form.getlist('delete_images')
            if delete_image_ids:
                for photo_id in delete_image_ids:
                    cur.execute("SELECT * FROM event_images WHERE id = ? AND event_id = ?", (photo_id, event_id))
                    photo = cur.fetchone()
                    if photo:
                        photo_filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo['image_path'])
                        if os.path.exists(photo_filepath):
                            os.remove(photo_filepath)
                        cur.execute("DELETE FROM event_images WHERE id = ?", (photo_id,))
            
            conn.commit()
            flash("Event updated successfully.")
        except Exception as e:
            flash(f"An error occurred: {e}")
            conn.rollback()
        finally:
            conn.close()

        return redirect(url_for('events'))
    
    # For GET requests:
    # Fetch images from all_photos
    all_photos = [f for f in os.listdir(all_photos_folder) if os.path.isfile(os.path.join(all_photos_folder, f))]
    
    # Fetch albums
    albums = [d for d in os.listdir(albums_folder) if os.path.isdir(os.path.join(albums_folder, d))]
    
    # Fetch event images from the database
    cur.execute("SELECT * FROM event_images WHERE event_id = ?", (event_id,))
    images = cur.fetchall()
    
    conn.close()
    return render_template('edit_event.html', event=event, images=images, albums=albums)


@app.route('/create_album/<int:event_id>', methods=['POST'])
@login_required
def create_album(event_id):
    album_name = request.form.get('new_album', '').strip()
    privacy = request.form.get('privacy', 'private').strip()  # Default to private
    
    if not album_name:
        flash("Album name is required.")
        return redirect(url_for('edit_event', event_id=event_id))
    
    # Sanitize the album name
    safe_album_name = secure_filename(album_name)
    if not safe_album_name:
        flash("Invalid album name. Please use a different name.")
        return redirect(url_for('edit_event', event_id=event_id))

    # Path to the event's albums folder
    albums_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "albums")
    if not os.path.exists(albums_folder):
        flash("Event folders are missing.")
        return redirect(url_for('edit_event', event_id=event_id))

    # Create the album folder
    album_path = os.path.join(albums_folder, safe_album_name)
    try:
        os.makedirs(album_path, exist_ok=False)  # Fail if the folder already exists
        
        # Store album metadata in the database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''INSERT INTO albums (event_id, name, visibility, created_at)
                       VALUES (?, ?, ?, ?)''',
                    (event_id, safe_album_name, privacy, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        flash(f"Album '{album_name}' created successfully as '{privacy}'.")
    except FileExistsError:
        flash(f"Album '{album_name}' already exists.")
    except Exception as e:
        flash(f"An error occurred: {str(e)}")

    return redirect(url_for('edit_event', event_id=event_id))


@app.route('/move_photos_to_album/<int:event_id>', methods=['POST'])
@login_required
def move_photos_to_album(event_id):
    selected_photos = request.form.getlist('selected_photos')
    print("Selected Photos:", selected_photos)  # Debugging: Original list

    # Clean the photo paths
    cleaned_photos = []
    for photo in selected_photos:
        if "all_photos/" in photo:
            cleaned_photo = photo.split("all_photos/")[1]
            cleaned_photos.append(cleaned_photo)

    print("Cleaned Photos:", cleaned_photos)  # Debugging: Shows cleaned filenames

    target_album = request.form.get('target_album', '').strip()

    if not cleaned_photos or not target_album:
        flash("Please select photos and an album.")
        return redirect(url_for('edit_event', event_id=event_id))

    # Paths for "All Photos" and the target album
    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}")
    all_photos_folder = os.path.join(event_folder, "all_photos")
    target_album_folder = os.path.join(event_folder, "albums", target_album)

    # Ensure the target album folder exists
    if not os.path.exists(target_album_folder):
        os.makedirs(target_album_folder)

    # Create symbolic links for cleaned photos
    for photo in cleaned_photos:
        source_path = os.path.join(all_photos_folder, photo)
        link_path = os.path.join(target_album_folder, photo)

        if os.path.exists(source_path):
            try:
                os.symlink(source_path, link_path)  # Create symbolic link
                flash(f"Photo '{photo}' linked to album '{target_album}'.")
            except OSError as e:
                flash(f"Failed to link photo '{photo}': {e}")
        else:
            flash(f"Photo '{photo}' does not exist in 'All Photos'.")

    return redirect(url_for('edit_event', event_id=event_id))


@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch event details to ensure it exists and belongs to the user
    cur.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, session['user_id']))
    event = cur.fetchone()
    if not event:
        conn.close()
        flash("Event not found or unauthorized.")
        return redirect(url_for('events'))
    
    # Folder paths for the event
    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}")
    all_photos_folder = os.path.join(event_folder, "all_photos")
    albums_folder = os.path.join(event_folder, "albums")
    
    try:
        # Delete associated image files from the database and disk
        cur.execute("SELECT * FROM event_images WHERE event_id = ?", (event_id,))
        images = cur.fetchall()
        for img in images:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], img['image_path'])
            if os.path.exists(filepath):
                os.remove(filepath)

        # Delete the "All Photos" folder and its contents
        if os.path.exists(all_photos_folder):
            for file in os.listdir(all_photos_folder):
                file_path = os.path.join(all_photos_folder, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(all_photos_folder)

        # Delete the "Albums" folder and its subfolders
        if os.path.exists(albums_folder):
            for album in os.listdir(albums_folder):
                album_folder = os.path.join(albums_folder, album)
                if os.path.isdir(album_folder):
                    for file in os.listdir(album_folder):
                        file_path = os.path.join(album_folder, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    os.rmdir(album_folder)
            os.rmdir(albums_folder)

        # Delete records from the database
        cur.execute("DELETE FROM event_images WHERE event_id = ?", (event_id,))
        cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        flash("Event deleted successfully.")
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred while deleting the event: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('events'))



# Helper to get username from user_id
def get_username(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        print(f"Debug: No user found for user_id {user_id}")
    return row['username'] if row else "Unknown"

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch event details
    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cur.fetchone()
    
    if not event:
        flash("Event not found.")
        conn.close()
        return redirect(url_for('explore'))
    
    # Get the username of the creator
    username = get_username(event['user_id'])
    
    # Folder paths for the event
    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}")
    all_photos_folder = os.path.join(event_folder, "all_photos")
    albums_folder = os.path.join(event_folder, "albums")
    
    # Ensure folders exist
    if not os.path.exists(all_photos_folder):
        os.makedirs(all_photos_folder, exist_ok=True)
    if not os.path.exists(albums_folder):
        os.makedirs(albums_folder, exist_ok=True)
    
    # Fetch album names
    albums = [album for album in os.listdir(albums_folder) if os.path.isdir(os.path.join(albums_folder, album))]
    
    conn.close()
    
    return render_template('event_details.html', event=event, username=username, albums=albums)

@app.route('/event/<int:event_id>/all_photos')
@login_required
def view_all_photos(event_id):
    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Validate that the event exists
        cur.execute("SELECT user_id FROM events WHERE id = ?", (event_id,))
        event = cur.fetchone()

        if not event:
            flash("Event not found.")
            return redirect(url_for('events'))

        # Check if the current user is the owner of the event
        event_owner = session['user_id'] == event['user_id']

        # Check if the 'All Photos' folder exists for the event
        all_photos_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "all_photos")
        if not os.path.exists(all_photos_folder):
            flash("The 'All Photos' folder does not exist for this event.")
            return redirect(url_for('events'))

        # Fetch photos from the folder
        photos = [
            photo for photo in os.listdir(all_photos_folder)
            if os.path.isfile(os.path.join(all_photos_folder, photo))
        ]

    except Exception as e:
        flash(f"An error occurred: {e}")
        return redirect(url_for('events'))

    finally:
        conn.close()

    # Render the template with the event ownership context and photos
    return render_template('all_photos.html', event_id=event_id, photos=photos, event_owner=event_owner)




@app.route('/event/<int:event_id>/albums')
@login_required
def view_albums(event_id):
    # Path to the "albums" folder
    albums_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "albums")
    
    if not os.path.exists(albums_folder):
        flash("No albums found for this event.")
        return redirect(url_for('events'))
    
    # Fetch album names
    albums = [album for album in os.listdir(albums_folder) if os.path.isdir(os.path.join(albums_folder, album))]
    
    return render_template('albums.html', event_id=event_id, albums=albums)

@app.route('/event/<int:event_id>/delete_photo', methods=['POST'])
@login_required
def delete_photo(event_id):
    photo_name = request.form.get('photo_name')

    if not photo_name:
        flash("No photo specified for deletion.")
        return redirect(url_for('view_all_photos', event_id=event_id))

    # Path to the photo in the 'all_photos' folder
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "all_photos", photo_name)

    try:
        # Remove the photo file from disk
        if os.path.exists(photo_path):
            os.remove(photo_path)
            flash("Photo deleted successfully.")
        else:
            flash("Photo not found.")
    except Exception as e:
        flash(f"An error occurred while deleting the photo: {e}")

    return redirect(url_for('view_all_photos', event_id=event_id))

@app.route('/event/<int:event_id>/album/<string:album_name>')
@login_required
def view_album_photos(event_id, album_name):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Validate the existence of the event and fetch owner information
        cur.execute("SELECT user_id FROM events WHERE id = ?", (event_id,))
        event = cur.fetchone()
        if not event:
            flash("Event not found.")
            return redirect(url_for('events'))

        event_creator_id = event['user_id']

        # Validate the existence of the album and fetch its visibility
        cur.execute("SELECT visibility FROM albums WHERE event_id = ? AND name = ?", (event_id, album_name))
        album = cur.fetchone()
        if not album:
            flash("Album not found.")
            return redirect(url_for('events'))

        album_visibility = album['visibility']

        # Access control for private albums
        if album_visibility == 'private' and session['user_id'] != event_creator_id:
            flash("You are not authorized to view this private album.")
            return redirect(url_for('events'))

        # Validate the existence of the album folder
        album_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "albums", album_name)
        if not os.path.exists(album_folder):
            flash("Album folder does not exist.")
            return redirect(url_for('events'))

        # Fetch photos from the album folder
        photos = [
            photo for photo in os.listdir(album_folder)
            if os.path.isfile(os.path.join(album_folder, photo))
        ]

    except Exception as e:
        # Log any unexpected errors and redirect to the events page
        flash(f"An error occurred while loading the album: {e}")
        return redirect(url_for('events'))

    finally:
        # Ensure the database connection is always closed
        conn.close()

    # Pass the necessary context to the template
    return render_template(
        'album_photos.html',
        event_id=event_id,
        album_name=album_name,
        photos=photos,
        album_visibility=album_visibility,
        event_owner=(session['user_id'] == event_creator_id)
    )

@app.route('/event/<int:event_id>/album/<string:album_name>/update_privacy', methods=['POST'])
@login_required
def update_album_privacy(event_id, album_name):
    new_privacy = request.form.get('privacy', 'private').strip()  # Get the new visibility

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Update visibility in the SQL table
        cur.execute(
            "UPDATE albums SET visibility = ? WHERE event_id = ? AND name = ?",
            (new_privacy, event_id, album_name)
        )
        conn.commit()
        flash(f"Updated album privacy to: {new_privacy}")
    except Exception as e:
        conn.rollback()
        flash(f"Error updating album privacy: {e}")
    finally:
        conn.close()

    return redirect(url_for('view_album_photos', event_id=event_id, album_name=album_name))


@app.route('/manage_album/<int:event_id>/<string:album_name>', methods=['POST'])
@login_required
def manage_album(event_id, album_name):
    # Define folder paths
    albums_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "albums", album_name)
    all_photos_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "all_photos")
    action = request.form.get('action')

    # Validate event ownership
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM events WHERE id = ?", (event_id,))
        event = cur.fetchone()

        if not event:
            flash("Event not found.")
            return redirect(url_for('events'))

        # Ensure the current user is the event owner
        if session['user_id'] != event['user_id']:
            flash("You are not authorized to manage this album.")
            return redirect(url_for('view_album_photos', event_id=event_id, album_name=album_name))

        # Check if the album exists in the database
        cur.execute("SELECT * FROM albums WHERE event_id = ? AND name = ?", (event_id, album_name))
        album = cur.fetchone()
        if not album:
            flash("Album not found.")
            return redirect(url_for('view_album_photos', event_id=event_id, album_name=album_name))

    except Exception as e:
        flash(f"An error occurred while validating ownership: {e}")
        return redirect(url_for('view_album_photos', event_id=event_id, album_name=album_name))

    # Handle actions
    try:
        # Action: Delete Selected Photos
        if action == 'delete_selected':
            selected_photos = request.form.getlist('selected_photos')
            if not selected_photos:
                flash("No photos were selected for deletion.")
            else:
                for photo in selected_photos:
                    photo_path = os.path.join(albums_folder, photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                        flash(f"Deleted: {photo}")
                    else:
                        flash(f"Photo not found: {photo}")

        # Action: Add Images
        elif action == 'add_images':
            if 'new_images' in request.files:
                images = request.files.getlist('new_images')
                for image in images:
                    if image and allowed_file(image.filename):
                        filename = secure_filename(image.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                        all_photo_path = os.path.join(all_photos_folder, unique_filename)
                        album_photo_path = os.path.join(albums_folder, unique_filename)

                        # Save to All Photos and create symbolic link in the album
                        image.save(all_photo_path)
                        os.symlink(all_photo_path, album_photo_path)
                        flash(f"Added: {unique_filename}")
                    else:
                        flash("One or more files are invalid or unsupported.")

        # Action: Update Album Visibility
        elif action == 'update_visibility':
            new_privacy = request.form.get('privacy', 'private').strip()
            # Update the visibility in the SQL database
            cur.execute(
                "UPDATE albums SET visibility = ? WHERE event_id = ? AND name = ?",
                (new_privacy, event_id, album_name)
            )
            conn.commit()
            flash(f"Updated album privacy to: {new_privacy}")

        else:
            flash("Invalid action.")

    except Exception as e:
        flash(f"An error occurred while processing the action: {e}")
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for('view_album_photos', event_id=event_id, album_name=album_name))



@app.route('/manage_all_photos/<int:event_id>', methods=['POST'])
@login_required
def manage_all_photos(event_id):
    all_photos_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "all_photos")
    action = request.form.get('action')

    # Validate event ownership
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Fetch the event and verify ownership
        cur.execute("SELECT user_id FROM events WHERE id = ?", (event_id,))
        event = cur.fetchone()
        if not event:
            flash("Event not found.")
            return redirect(url_for('events'))
        if session['user_id'] != event['user_id']:
            flash("You are not authorized to manage this event's photos.")
            return redirect(url_for('view_all_photos', event_id=event_id))

        # Handle actions
        if action == 'delete_selected':
            handle_delete_selected_photos(request, all_photos_folder)
        elif action == 'add_images':
            handle_add_images(request, all_photos_folder)
        else:
            flash("Invalid action.")
    except Exception as e:
        flash(f"An error occurred: {e}")
    finally:
        conn.close()

    return redirect(url_for('view_all_photos', event_id=event_id))
def handle_delete_selected_photos(request, all_photos_folder):
    selected_photos = request.form.getlist('selected_photos')
    if not selected_photos:
        flash("No photos selected for deletion.")
        return

    try:
        for photo in selected_photos:
            photo_path = os.path.join(all_photos_folder, photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
                flash(f"Deleted: {photo}")
            else:
                flash(f"Photo not found: {photo}")
    except Exception as e:
        flash(f"Error deleting photos: {e}")
def handle_add_images(request, all_photos_folder):
    if 'new_images' not in request.files:
        flash("No images uploaded.")
        return

    images = request.files.getlist('new_images')
    if not images:
        flash("No valid images found.")
        return

    try:
        for image in images:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                photo_path = os.path.join(all_photos_folder, unique_filename)

                # Save image to All Photos
                image.save(photo_path)
                flash(f"Added: {unique_filename}")
            else:
                flash("Invalid image file uploaded.")
    except Exception as e:
        flash(f"Error adding photos: {e}")






@app.route('/event/<int:event_id>/album/<string:album_name>/delete_photo', methods=['POST'])
@login_required
def delete_album_photo(event_id, album_name):
    # Get the photo name from the form data
    photo_name = request.form.get('photo_name')

    # Construct the path to the symbolic link in the album folder
    album_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"event_{event_id}", "albums", album_name)
    photo_path = os.path.join(album_folder, photo_name)

    # Remove the symbolic link
    try:
        if os.path.islink(photo_path):
            os.unlink(photo_path)
            flash(f"Photo '{photo_name}' successfully removed from album '{album_name}'.")
        else:
            flash(f"Photo '{photo_name}' is not a valid symbolic link or does not exist.")
    except Exception as e:
        flash(f"Failed to delete photo '{photo_name}': {e}")

    # Redirect back to the album's photo list
    return redirect(url_for('view_album_photos', event_id=event_id, album_name=album_name))


# ============================
# Explore Route (Public)
# ============================
@app.route('/explore')
def explore():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Fetch all public events, include necessary fields in the main query
        cur.execute('''
            SELECT events.*, users.username 
            FROM events 
            INNER JOIN users ON events.user_id = users.id
            WHERE events.is_public = 1 
            ORDER BY events.created_at DESC
        ''')
        events = cur.fetchall()

        # Construct the events list
        events_list = []
        for event in events:
            # Use banner_image directly; if absent, fallback to a placeholder
            banner_image = event['banner_image'] or "https://via.placeholder.com/600x400?text=No+Image"
            events_list.append({
                'id': event['id'],
                'name': event['name'],
                'description': event['description'],
                'category': event['category'],
                'event_date': event['event_date'],
                'location': event['location'],
                'num_attendees': event['num_attendees'],
                'is_public': event['is_public'],
                'created_at': event['created_at'],
                'banner_image': banner_image,
                'username': event['username']
            })
    except Exception as e:
        flash(f"An error occurred while fetching events: {str(e)}")
        conn.rollback()
        events_list = []
    finally:
        conn.close()

    return render_template('explore.html', events=events_list)



if __name__ == '__main__':
    app.run(debug=True)
