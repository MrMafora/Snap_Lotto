"""
Fixed main application entry point with Flask application defined for deployment.

This file is imported by gunicorn using the 'main:app' notation.
"""
import logging
import os
import io
import re
import time
import threading
import traceback
from datetime import datetime, timedelta
from functools import wraps
import json

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, send_file, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize database
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "snap-lotto-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize the app with the database extension
db.init_app(app)

# Import models and create database tables
with app.app_context():
    import models
    db.create_all()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Admin access decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Home route
@app.route('/')
def index():
    """Homepage with latest lottery results"""
    return render_template('simple.html', title="South African Lottery Results")

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:  # Make sure we have both values
            from models import User
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'danger')
        else:
            flash('Please enter both username and password', 'warning')
    
    return render_template('login.html', title="Login")

# Logout route
@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# Admin dashboard
@app.route('/admin')
@login_required
@admin_required
def admin():
    """Admin dashboard page"""
    return render_template('simple.html', title="Admin Dashboard")

# Health check route
@app.route('/health')
def health_check():
    """Simple endpoint for health checks in Replit deployment"""
    return jsonify({"status": "OK", "version": "1.0.0"})

# Port check route
@app.route('/port-check')
def port_check():
    """Special endpoint to check which port the application is responding on"""
    return jsonify({
        "server_port": request.environ.get('SERVER_PORT', 'unknown'),
        "request_host": request.host,
        "request_url": request.url,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)