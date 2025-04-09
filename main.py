"""
Main application entry point
"""
from flask import Flask
from config import Config

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Import routes after app is created to avoid circular imports
from routes import register_routes

# Register all application routes
register_routes(app)

# This section only runs when the file is executed directly, not when imported by gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
