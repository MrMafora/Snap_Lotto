"""
Simple version of the main application for testing
"""
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from sqlalchemy.orm import DeclarativeBase
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "temporary_secret_key_for_development")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the database
db.init_app(app)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # This is a stub - in a real app, we'd load the user from the database
    return None

# Home route
@app.route('/')
def index():
    return render_template('simple.html', title="South African Lottery Results")

# Login route
@app.route('/login')
def login():
    flash('Login feature is under maintenance', 'info')
    return render_template('simple.html', title="Login")

# Health check route
@app.route('/health')
def health_check():
    return jsonify({"status": "OK", "version": "1.0.0"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)