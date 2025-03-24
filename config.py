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

    # Ensure critical folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

    # Debug settings
    DEBUG = os.environ.get('DEBUG', False)  # Enable/disable debug mode (useful for development)

    # Logging
    LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'INFO')  # Default logging level


class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE = os.environ.get('DEV_DATABASE_URL', os.path.join(basedir, 'dev_database.db'))


class ProductionConfig(Config):
    DEBUG = False
    DATABASE = os.environ.get('PROD_DATABASE_URL', os.path.join(basedir, 'prod_database.db'))
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Enforce secure secret keys in production!


class TestingConfig(Config):
    TESTING = True
    DATABASE = os.environ.get('TEST_DATABASE_URL', os.path.join(basedir, 'test_database.db'))
    SESSION_TYPE = 'filesystem'
