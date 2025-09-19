"""
Application factory module for the lottery data app.
This module serves as a bridge for gunicorn to load the app from main.py
"""

from main import app

def create_app():
    """
    Application factory function that creates and configures the Flask app.
    This just returns the pre-configured app from main.py
    """
    return app

# For gunicorn and WSGI compatibility
application = app

# Note: For development, use main.py directly
# For production, use gunicorn with this file as the entry point