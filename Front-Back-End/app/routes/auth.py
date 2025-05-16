from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from app.services.auth_service import register_user, login_user, logout_user
from app.utils.helpers import validate_required_fields, is_logged_in, get_logged_in_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET'])
def register_form():
    """
    Displays the registration form for users to register.
    """
    return render_template('register.html')  # Render the registration form

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Handles user registration.
    Processes form submission and renders the template with error messages if validation fails.
    """
    data = request.form  # Use form data

    username = data.get('username')
    password = data.get('password')

    # Validate input
    if not username or not password:
        error = "Username and password are required"
        return render_template('register.html', error=error)  # Render the form with an error message

    # Call the service function
    response, status_code = register_user(username, password)

    if status_code == 201:  # Registration successful
        return render_template('login.html', success="Registration successful! Please log in.")  # Redirect to login
    elif status_code == 409:  # Username already taken
        error = response.get("error", "An unknown error occurred.")
        return render_template('register.html', error=error)  # Render the form with the error message
    else:  # Other errors
        error = response.get("error", "An unknown error occurred.")
        return render_template('register.html', error=error)  # Render the form with the error message




@auth_bp.route('/login', methods=['GET'])
def login_form():
    """
    Displays the login form for users.
    """
    return render_template('login.html')  # Render the login form


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user login.
    Processes form submission and redirects to the dashboard on success.
    """
    data = request.form  # Use form data instead of JSON

    username = data.get('username')
    password = data.get('password')

    # Validate input
    if not username or not password:
        error = "Username and password are required."
        return render_template('login.html', error=error)  # Render the form with an error message

    # Call the service function
    response, status_code = login_user(username, password)

    if status_code == 200:  # Login successful
        session['user_id'] = response['user_id']
        session['username'] = response['username']
        # Redirect to the dashboard route
        return redirect(url_for('main.dashboard'))
    elif status_code == 401:  # Invalid credentials
        error = response.get("error", "Invalid username or password.")
        return render_template('login.html', error=error)  # Render the form with an error message
    else:  # Other errors
        error = response.get("error", "An unknown error occurred.")
        return render_template('login.html', error=error)  # Render the form with an error message

@auth_bp.route('/logout', methods=['GET'])
def logout_get():
    """
    Logs the user out via GET request and redirects to the home page.
    """
    session.clear()  # Clear the session
    return redirect(url_for('main.landing_page'))  # Redirect to the landing page


@auth_bp.route('/logout', methods=['POST'])
def logout_post():
    """
    Logs out the user via POST request by clearing the session.
    """
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200
