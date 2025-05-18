"""
Direct Flask application starter running on port 8080
"""
import os
import logging
from main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    logging.info(f"Starting direct Flask application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)