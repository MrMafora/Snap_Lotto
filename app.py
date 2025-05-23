"""
Application factory module for the lottery data app.
This module serves as a bridge for gunicorn to load the app from main.py
"""

# These imports are needed to create the app object
from main import app

# This function isn't needed by gunicorn directly but we include it for completeness
def create_app():
    """
    Application factory function that creates and configures the Flask app.
    This just returns the pre-configured app from main.py
    """
    return app