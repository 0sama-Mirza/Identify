import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Application configurations
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')  # Change this in production!
    DATABASE = os.environ.get('DATABASE_URL', os.path.join(basedir, 'database.db'))  # SQLite path or external DB URL
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')  # Ensure uploads are stored outside static/
    STATIC_FOLDER = os.path.join(basedir, 'static')  # Static files (CSS, JS, images)
    TEMPLATE_FOLDER = os.path.join(basedir, 'templates')  # HTML templates
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')  # Session backend (default is filesystem)

    # File size limit for uploads (in bytes)
    # MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit

    # --- ADDED Settings for Background Scheduler and FastAPI Integration ---
    SCHEDULER_API_ENABLED = True  # Optional: Enables an API endpoint to view scheduler status.
    FASTAPI_UPLOAD_URL = os.environ.get('FASTAPI_UPLOAD_URL', "http://127.0.0.1:8000/upload-images/") # URL of your FastAPI image upload endpoint. ADJUST IP/PORT AS NEEDED!
    # --- End ADDED Settings ---


    # Ensure critical folders exist
    # Note: Creating DB directory here assumes DATABASE path is finalized.
    db_path = os.environ.get('DATABASE_URL', os.path.join(basedir, 'database.db'))
    if db_path.startswith('sqlite:///'):
        db_path = db_path[len('sqlite:///'):]
    db_dir = os.path.dirname(db_path)
    if db_dir: # Only create if it's not just a filename in the basedir
        os.makedirs(db_dir, exist_ok=True)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    os.makedirs(TEMPLATE_FOLDER, exist_ok=True)


    # Debug settings
    # Safer way to handle boolean conversion from environment variable
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

    # Logging
    LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'INFO')  # Default logging level



# class DevelopmentConfig(Config):
#     DEBUG = True
#     DATABASE = os.environ.get('DEV_DATABASE_URL', os.path.join(basedir, 'dev_database.db'))


# class ProductionConfig(Config):
#     DEBUG = False
#     DATABASE = os.environ.get('PROD_DATABASE_URL', os.path.join(basedir, 'prod_database.db'))
#     SECRET_KEY = os.environ.get('SECRET_KEY')  # Enforce secure secret keys in production!


# class TestingConfig(Config):
#     TESTING = True
#     DATABASE = os.environ.get('TEST_DATABASE_URL', os.path.join(basedir, 'test_database.db'))
#     SESSION_TYPE = 'filesystem'
