"""
Direct Flask startup script for Replit as recommended by support engineers.
This starts the application with the Python built-in development server.
"""
import sys
import logging
from main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log startup
logger.info("Starting Flask application on 0.0.0.0:5000...")
print("Server is ready and listening on port 5000")
sys.stdout.flush()

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)