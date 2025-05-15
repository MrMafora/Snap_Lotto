"""
Fixed main application entry point with Flask application defined for deployment.

This file is imported by gunicorn using the 'main:app' notation.
"""
import logging
import os
import time
import threading
from datetime import datetime, timedelta
from functools import wraps

from flask import render_template, request, redirect, url_for, flash, jsonify, abort, send_file, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Import app and db from app.py to avoid circular imports
from app import app, db, login_manager, logger

# Import models after app is created
import models

# Custom functions for handling lottery types
def standardize_lottery_type(lottery_type):
    """Convert various lottery type names to standardized format"""
    lottery_type = lottery_type.lower().strip()
    if lottery_type in ["lotto", "lottery"]:
        return "Lottery"
    elif lottery_type in ["lotto_plus_1", "lottery_plus_1", "lotto plus 1", "lottery plus 1"]:
        return "Lottery Plus 1"
    elif lottery_type in ["lotto_plus_2", "lottery_plus_2", "lotto plus 2", "lottery plus 2"]:
        return "Lottery Plus 2"
    elif lottery_type in ["powerball"]:
        return "Powerball"
    elif lottery_type in ["powerball_plus", "powerball plus"]:
        return "Powerball Plus"
    elif lottery_type in ["daily_lotto", "daily lottery", "daily_lottery"]:
        return "Daily Lottery"
    return lottery_type.title()

# Function to create initial admin user if not exists
def create_admin_user():
    """Create the default admin user if not already exists"""
    # Check if admin user exists
    admin = models.User.query.filter_by(username='admin').first()
    if admin is None:
        # Create default admin user with password St0n3@g3
        admin = models.User(
            username='admin',
            email='admin@snaplotto.co.za',
            is_admin=True
        )
        admin.set_password('St0n3@g3')
        db.session.add(admin)
        db.session.commit()
        logger.info("Default admin user created")
    else:
        logger.info("Admin user already exists")

# Create database tables and admin user
with app.app_context():
    db.create_all()
    create_admin_user()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

# Authorization decorator for admin routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Homepage with latest lottery results"""
    # Get latest results for each lottery type
    latest_results = {}
    lottery_types = ["Lottery", "Lottery Plus 1", "Lottery Plus 2", 
                     "Powerball", "Powerball Plus", "Daily Lottery"]
    
    for lottery_type in lottery_types:
        result = models.LotteryResult.query.filter_by(
            lottery_type=lottery_type
        ).order_by(models.LotteryResult.draw_date.desc()).first()
        
        if result:
            latest_results[lottery_type] = result
    
    return render_template('index.html', 
                          latest_results=latest_results,
                          lottery_types=lottery_types)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = models.User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
@admin_required
def admin():
    """Admin dashboard page"""
    return render_template('admin.html')

@app.route('/health')
def health_check():
    """Simple endpoint for health checks in Replit deployment"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/port')
def port_check():
    """Special endpoint to check which port the application is responding on"""
    return jsonify({
        "port": request.environ.get('SERVER_PORT', 'unknown'),
        "host": request.environ.get('HTTP_HOST', 'unknown'),
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)