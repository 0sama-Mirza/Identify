from werkzeug.security import generate_password_hash, check_password_hash
from app.db.dbhelper import get_db_connection


def register_user(username, password):
    """
    Registers a new user in the database.
    """
    if not username or not password:
        return {"error": "Username and password are required"}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if the username already exists
        cur.execute("SELECT id FROM users WHERE username = ?;", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            return {"error": "Username already taken"}, 409

        # Hash the password and insert the user into the database
        hashed_password = generate_password_hash(password)
        query = '''
        INSERT INTO users (username, password, created_at) 
        VALUES (?, ?, datetime('now'));
        '''
        cur.execute(query, (username, hashed_password))
        conn.commit()

        return {"success": True, "message": "User registered successfully"}, 201
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        conn.close()


def login_user(username, password):
    """
    Authenticates a user and retrieves their session details.
    """
    if not username or not password:
        return {"error": "Username and password are required"}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch the user from the database
        cur.execute("SELECT id, password FROM users WHERE username = ?;", (username,))
        user = cur.fetchone()

        if user is None:
            return {"error": "Invalid username or password"}, 401

        # Verify the password
        if not check_password_hash(user['password'], password):
            return {"error": "Invalid username or password"}, 401

        # Return user details for session management
        return {"success": True, "user_id": user['id'], "username": username}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        conn.close()


def logout_user():
    """
    Logs out the user by clearing their session.
    """
    return {"success": True, "message": "Logged out successfully"}, 200
