"""
Main application entry point with Flask application defined for deployment.

This file is imported by gunicorn using the 'main:app' notation.
"""
import logging
from app import create_app

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask application using the factory function
app = create_app()

# When running directly, not through gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)