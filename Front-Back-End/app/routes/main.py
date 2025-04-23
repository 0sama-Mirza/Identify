from flask import Blueprint, render_template, session, redirect, url_for
from app.services.event_service import get_user_events, get_all_public_events

# Define the main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def landing_page():
    """
    Displays the landing page of the application.
    """
    return render_template('landing.html')  # Render the main landing page


@main_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Displays the user's dashboard after login.
    """
    # Ensure the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated

    user_id = session['user_id']

    # Fetch events for the user (use your service function)
    response, status_code = get_user_events(user_id)

    if status_code == 200:  # Success
        events = response.get('events', [])
    else:
        events = []  # Default to empty list if there's an error

    return render_template('dashboard.html', success="Welcome to your dashboard!", events=events)




@main_bp.route('/explore', methods=['GET'])
def explore():
    """
    Displays the explore page where users can browse events or content.
    """
    # Fetch public events
    response, status_code = get_all_public_events()
    print("\n\n================\n\nresponse: ",response)
    print("\n===================\n")
    if status_code == 200:
        public_events = response['events']
    else:
        public_events = []  # Default to empty if there's an issue

    return render_template('explore.html', events=public_events)



@main_bp.route('/about', methods=['GET'])
def about():
    """
    Displays the About page with information about the app.
    """
    return render_template('about.html')  # Render an "About" page


@main_bp.route('/contact', methods=['GET'])
def contact():
    """
    Displays the Contact page for user queries or support.
    """
    return render_template('contact.html')  # Render a "Contact" page
