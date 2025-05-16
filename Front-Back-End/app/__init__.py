# app/__init__.py
import os
import sys
from flask import Flask
from config import Config
from flask_session import Session
from app.db.dbhelper import init_db, close_db_connection
# --- 1. Import APScheduler ---
from flask_apscheduler import APScheduler
import traceback
import atexit
import logging

# Optional: Configure Logging
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# --- 2. Initialize APScheduler (outside the factory) ---
# Create the global scheduler instance. It's not started here.
scheduler = APScheduler()
print(f"[PID {os.getpid()}] Global APScheduler instance created (ID: {id(scheduler)})", flush=True)


# --- create_app Function (Simplified) ---
def create_app():
    """
    Application factory: Creates and configures the Flask app.
    Initializes extensions (including APScheduler with app config)
    but DOES NOT start the scheduler or add jobs.
    """
    app_process_pid = os.getpid()
    print(f"[PID {app_process_pid}] Starting create_app...", flush=True)

    app = Flask( __name__, static_folder=Config.STATIC_FOLDER, template_folder=Config.TEMPLATE_FOLDER )
    print(f"[PID {app_process_pid}] create_app: Flask instance created.", flush=True)
    app.config.from_object(Config)
    print(f"[PID {app_process_pid}] create_app: Config loaded.", flush=True)

    # --- Initialize Scheduler with App Config ---
    # Links the global scheduler instance to this app instance's config
    # IMPORTANT: This does NOT start the scheduler.
    print(f"[PID {app_process_pid}] create_app: Calling scheduler.init_app(app)...", flush=True)
    scheduler.init_app(app)
    print(f"[PID {app_process_pid}] create_app: scheduler.init_app completed.", flush=True)
    # --- End Scheduler Init ---

    Session(app)
    print(f"[PID {app_process_pid}] create_app: Session initialized.", flush=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print(f"[PID {app_process_pid}] create_app: Initializing database...", flush=True)
    with app.app_context(): init_db(app)
    print(f"[PID {app_process_pid}] create_app: Database initialized.", flush=True)
    app.teardown_appcontext(close_db_connection)

    print(f"[PID {app_process_pid}] create_app: Registering blueprints...", flush=True)
    from app.routes.auth import auth_bp
    from app.routes.event import event_bp
    from app.routes.album import album_bp
    from app.routes.main import main_bp
    from app.routes.uploads import uploads_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(event_bp, url_prefix='/events')
    app.register_blueprint(album_bp, url_prefix='/albums')
    app.register_blueprint(uploads_bp, url_prefix='/uploads')
    app.register_blueprint(main_bp)
    print(f"[PID {app_process_pid}] create_app: Blueprints registered.", flush=True)

    # REMOVED configure_scheduler call and the helper function itself

    print(f"[PID {app_process_pid}] create_app: Finished.", flush=True)
    return app
