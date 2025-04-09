"""
WSGI entry point for deployment
"""
# Import the app instance directly
from app import app

# This file is used by gunicorn for deployment
# The app variable is imported from app.py