import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # NOTE: Change this for production use!

# Directory for uploaded images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    # Event images table
    cur.execute('''CREATE TABLE IF NOT EXISTS event_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    image_path TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES events(id)
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
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                        (username, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
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
        cur.execute("SELECT * FROM event_images WHERE event_id = ?", (event['id'],))
        images = cur.fetchall()
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
            'images': images
        })
    conn.close()
    return render_template('events.html', events=events_list)

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        event_date = request.form.get('event_date', '').strip()
        location = request.form.get('location', '').strip()
        num_attendees = request.form.get('num_attendees', '0').strip()
        try:
            num_attendees = int(num_attendees)
        except ValueError:
            num_attendees = 0
        
        visibility = request.form.get('visibility', 'public')
        is_public = 1 if visibility == 'public' else 0

        if not name:
            flash("Event name is required.")
            return redirect(url_for('create_event'))

        conn = get_db_connection()
        cur = conn.cursor()
        # Insert the event with banner_image as NULL initially
        cur.execute('''INSERT INTO events (user_id, name, description, category, event_date, location, num_attendees, is_public, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (session['user_id'], name, description, category, event_date, location, num_attendees, is_public, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        event_id = cur.lastrowid

        # Process the Banner Image if provided
        banner_file = request.files.get('banner')
        if banner_file and allowed_file(banner_file.filename):
            filename = secure_filename(banner_file.filename)
            unique_filename = f"{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            banner_file.save(filepath)
            # Update the event's banner_image column
            cur.execute("UPDATE events SET banner_image = ? WHERE id = ?", (unique_filename, event_id))
            # Also add the banner image to event_images table
            cur.execute('''INSERT INTO event_images (event_id, image_path, uploaded_at)
                           VALUES (?, ?, ?)''',
                        (event_id, unique_filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Process additional images if provided
        if 'images' in request.files:
            images = request.files.getlist('images')
            for image in images:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    unique_filename = f"{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    image.save(filepath)
                    
                    cur.execute('''INSERT INTO event_images (event_id, image_path, uploaded_at)
                                   VALUES (?, ?, ?)''',
                                (event_id, unique_filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        flash("Event created successfully.")
        return redirect(url_for('events'))
    return render_template('create_event.html')


@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, session['user_id']))
    event = cur.fetchone()
    if not event:
        conn.close()
        flash("Event not found or unauthorized.")
        return redirect(url_for('events'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        event_date = request.form.get('event_date', '').strip()
        location = request.form.get('location', '').strip()
        num_attendees = request.form.get('num_attendees', '0').strip()
        try:
            num_attendees = int(num_attendees)
        except ValueError:
            num_attendees = 0
        
        visibility = request.form.get('visibility', 'public')
        is_public = 1 if visibility == 'public' else 0
        
        if not name:
            flash("Event name is required.")
            return redirect(url_for('edit_event', event_id=event_id))
        
        cur.execute('''UPDATE events SET name = ?, description = ?, category = ?, event_date = ?, location = ?, num_attendees = ?, is_public = ?
                       WHERE id = ?''',
                    (name, description, category, event_date, location, num_attendees, is_public, event_id))
        
        # Handle banner image upload (if a new banner is provided)
        banner_file = request.files.get('banner')
        if banner_file and allowed_file(banner_file.filename):
            filename = secure_filename(banner_file.filename)
            unique_filename = f"{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            banner_file.save(filepath)
            cur.execute("UPDATE events SET banner_image = ? WHERE id = ?", (unique_filename, event_id))
            # Also add the new banner image to event_images
            cur.execute('''INSERT INTO event_images (event_id, image_path, uploaded_at)
                           VALUES (?, ?, ?)''',
                        (event_id, unique_filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Process additional image uploads as before
        if 'images' in request.files:
            images = request.files.getlist('images')
            for image in images:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    unique_filename = f"{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    image.save(filepath)
                    
                    cur.execute('''INSERT INTO event_images (event_id, image_path, uploaded_at)
                                   VALUES (?, ?, ?)''',
                                (event_id, unique_filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Process selection from existing images (radio group)
        banner_choice = request.form.get('banner_choice')
        if banner_choice:
            cur.execute("UPDATE events SET banner_image = ? WHERE id = ?", (banner_choice, event_id))
        
        # Handle deletion of selected images
        delete_image_ids = request.form.getlist('delete_images')
        if delete_image_ids:
            for photo_id in delete_image_ids:
                cur.execute("SELECT * FROM event_images WHERE id = ? AND event_id = ?", (photo_id, event_id))
                photo = cur.fetchone()
                if photo:
                    # Delete the image file from disk if it exists
                    photo_filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo['image_path'])
                    if os.path.exists(photo_filepath):
                        os.remove(photo_filepath)
                    # Delete the image record from the database
                    cur.execute("DELETE FROM event_images WHERE id = ?", (photo_id,))
        
        conn.commit()
        conn.close()
        flash("Event updated successfully.")
        return redirect(url_for('events'))
    
    # For GET: fetch event images as well
    cur.execute("SELECT * FROM event_images WHERE event_id = ?", (event_id,))
    images = cur.fetchall()
    conn.close()
    return render_template('edit_event.html', event=event, images=images)



@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, session['user_id']))
    event = cur.fetchone()
    if not event:
        conn.close()
        flash("Event not found or unauthorized.")
        return redirect(url_for('events'))
    
    # Delete associated image files from disk
    cur.execute("SELECT * FROM event_images WHERE event_id = ?", (event_id,))
    images = cur.fetchall()
    for img in images:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], img['image_path'])
        if os.path.exists(filepath):
            os.remove(filepath)
    
    # Delete image records and the event itself
    cur.execute("DELETE FROM event_images WHERE event_id = ?", (event_id,))
    cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    flash("Event deleted successfully.")
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
    
    # Fetch all images for the event
    cur.execute("SELECT * FROM event_images WHERE event_id = ?", (event_id,))
    images = cur.fetchall()
    
    # Get the username of the creator
    username = get_username(event['user_id'])
    conn.close()
    
    return render_template('event_details.html', event=event, images=images, username=username)



# ============================
# Explore Route (Public)
# ============================
@app.route('/explore')
def explore():
    conn = get_db_connection()
    cur = conn.cursor()
    # Only select events marked as public
    cur.execute("SELECT * FROM events WHERE is_public = 1 ORDER BY created_at DESC")
    events = cur.fetchall()
    events_list = []
    for event in events:
        cur.execute("SELECT * FROM event_images WHERE event_id = ? LIMIT 1", (event['id'],))
        image_row = cur.fetchone()
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
            'image': image_row,
            'banner_image': event['banner_image'],  # Include banner image
            'username': get_username(event['user_id'])
        })
    conn.close()
    return render_template('explore.html', events=events_list)


if __name__ == '__main__':
    app.run(debug=True)
