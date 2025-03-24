from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from Evently.app import create_app
from app.db.dbhelper import init_db

# Create the Flask app using the application factory
app = create_app()

# Initialize the Flask-Script Manager
manager = Manager(app)

# Add migration support (if using migrations like Flask-Migrate)
migrate = Migrate(app, init_db)  # Bind Migrate to the app and db helper
manager.add_command('db', MigrateCommand)  # Adds migration commands under 'db'

@manager.command
def init_database():
    """
    Initializes the database by creating required tables.
    This command is executed with: python manage.py init_database
    """
    with app.app_context():
        init_db()
        print("Database initialized successfully!")

@manager.command
def runserver():
    """
    Runs the Flask development server.
    This command is executed with: python manage.py runserver
    """
    app.run(debug=True)

@manager.command
def custom_command(arg1=None):
    """
    A custom command for your CLI.
    Usage: python manage.py custom_command --arg1=value
    """
    print(f"Custom command executed with arg1={arg1}")


if __name__ == "__main__":
    manager.run()
