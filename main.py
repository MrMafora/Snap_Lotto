"""
Main application entry point

This file defines the Flask application in a deployment-friendly way.
It contains the main Flask app instance that Gunicorn/deployment services
can import directly using the "main:app" module path.
"""
# Import the Flask app instance from app.py
from app import app

# This is what gunicorn looks for by default: the variable named 'app'
# in the 'main' module (this file). No need to modify anything else.

# When running directly, not through gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
