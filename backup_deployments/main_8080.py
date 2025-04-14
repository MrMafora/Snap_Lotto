"""
This is a modified version of main.py that forces Flask to run on port 8080
for compatibility with Replit's port forwarding configuration.
"""
from main import app

if __name__ == "__main__":
    print("Starting Flask application on port 8080...")
    # Explicitly bind to port 8080, ignoring any other configuration
    app.run(host="0.0.0.0", port=8080, debug=True)