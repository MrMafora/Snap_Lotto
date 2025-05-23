"""
Application factory module for the lottery data app.
"""
from flask import Flask

def create_app():
    """
    Application factory function that creates and configures the Flask app.
    This is used by gunicorn when starting the application.
    """
    # Import the main app from main.py
    from main import app as main_app
    
    return main_app