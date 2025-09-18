"""
WSGI entry point for deployment
This file ensures the app starts correctly in production
"""
import os
from main import app

if __name__ == "__main__":
    # For local testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)