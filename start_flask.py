"""
Simple starter script that runs Flask directly.
This is optimized for faster startup time in Replit.
"""
from main import app

if __name__ == "__main__":
    print("Starting Flask application directly (bypassing gunicorn)...")
    print("Server is ready and listening on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)