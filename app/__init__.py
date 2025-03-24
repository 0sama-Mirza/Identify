from flask import Flask
from config import Config
from flask_session import Session
from app.db.dbhelper import init_db, close_db_connection
import os


def create_app():
    """
    Application factory to create and configure the Flask app.
    """
    # Initialize Flask app with custom static and template folders
    app = Flask(
        __name__,
        static_folder=Config.STATIC_FOLDER,
        template_folder=Config.TEMPLATE_FOLDER
    )

    # Load configurations from the Config class
    app.config.from_object(Config)

    # Set up Flask-Session
    Session(app)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Debugging outputs to ensure folder paths are correct (optional, can be removed in production)
    print(f"UPLOAD_FOLDER is set to: {app.config['UPLOAD_FOLDER']}")
    print(f"Static folder is set to: {app.static_folder}")
    print(f"Template folder is set to: {app.template_folder}")

    # Initialize the database
    with app.app_context():
        init_db(app)  # Ensure the database is initialized when the app context is active

    # Register teardown callback for cleaning up database connections
    app.teardown_appcontext(close_db_connection)

    # Register blueprints for route modules
    from app.routes.auth import auth_bp
    from app.routes.event import event_bp
    from app.routes.album import album_bp
    from app.routes.main import main_bp
    from app.routes.uploads import uploads_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')  # Authentication routes
    app.register_blueprint(event_bp, url_prefix='/events')  # Event routes
    app.register_blueprint(album_bp, url_prefix='/albums')  # Album routes
    app.register_blueprint(uploads_bp, url_prefix='/uploads')  # Upload routes
    app.register_blueprint(main_bp)  # General routes (no URL prefix)

    return app
