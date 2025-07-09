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

# For gunicorn compatibility
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)