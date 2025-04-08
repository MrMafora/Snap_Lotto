"""
Main application entry point
"""
# Import the app from app.py directly so it's available as main:app for gunicorn
from app import app

# This section only runs when the file is executed directly, not when imported by gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
