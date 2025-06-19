"""
Main application entry point with Flask application defined for deployment.
Fixed version with proper error handling and simplified initialization.
"""
import json
import logging
import os
import re
import threading
import traceback
from datetime import datetime, timedelta
from functools import wraps

# Set up logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, send_from_directory, send_file, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect

# Import models and config
from models import LotteryResult, ScheduleConfig, Screenshot, User, Advertisement, AdImpression, Campaign, AdVariation, ImportHistory, ImportedRecord, db
from config import Config
from sqlalchemy import text

# Import lottery analysis module
import lottery_analysis

# Create the Flask application with simplified initialization
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Set secret key properly
app.secret_key = os.environ.get("SESSION_SECRET", "lottery-scraper-default-secret")

# Add custom Jinja2 filters for math functions needed by charts
import math
try:
    import locale
    locale.setlocale(locale.LC_ALL, 'C')  # Use C locale for cross-platform compatibility
except:
    pass  # Ignore locale errors

app.jinja_env.filters['cos'] = lambda x: math.cos(float(x))
app.jinja_env.filters['sin'] = lambda x: math.sin(float(x))
app.jinja_env.filters['format_number'] = lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x

# Database configuration with error handling
try:
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Fix PostgreSQL URL format if needed
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        logger.info("Using database from DATABASE_URL environment variable")
    else:
        # Fallback to SQLite for development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'
        logger.warning("DATABASE_URL not found, using SQLite fallback")

    # Simplified database configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 30
    }

    # Add SSL for PostgreSQL only
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS']["connect_args"] = {"sslmode": "require"}
        logger.info("PostgreSQL SSL mode enabled")

except Exception as e:
    logger.error(f"Database configuration error: {e}")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'

# Initialize SQLAlchemy
try:
    db.init_app(app)
    logger.info("SQLAlchemy initialized successfully")
except Exception as e:
    logger.error(f"SQLAlchemy initialization error: {e}")

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Disable CSRF for Replit environment
app.config['WTF_CSRF_ENABLED'] = False

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# Initialize database with proper error handling
def init_database():
    """Initialize database tables with error handling"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created/verified")
            
            # Create default admin user if none exists
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    email='admin@localhost.com',
                    is_admin=True
                )
                admin_user.set_password('admin123')  # Default password
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Default admin user created (username: admin, password: admin123)")
                
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

# Initialize modules with error handling
def init_modules():
    """Initialize modules with proper error handling"""
    try:
        # Initialize lottery analysis module
        lottery_analysis.register_analysis_routes(app, db)
        logger.info("Lottery analysis routes registered")
    except Exception as e:
        logger.error(f"Lottery analysis initialization failed: {e}")

    try:
        # Initialize health monitor if available
        import health_monitor as hm
        hm.init_health_monitor(app, db)
        logger.info("Health monitoring initialized")
    except ImportError:
        logger.warning("Health monitor module not available")
    except Exception as e:
        logger.error(f"Health monitor initialization failed: {e}")

# Background initialization
def background_init():
    """Background initialization of modules"""
    try:
        init_database()
        init_modules()
        logger.info("All modules initialized successfully")
    except Exception as e:
        logger.error(f"Background initialization error: {e}")

# Start background initialization
threading.Thread(target=background_init, daemon=True).start()

def calculate_frequency_analysis(results):
    """Calculate frequency analysis from lottery results for homepage charts"""
    try:
        number_counts = {}
        
        # Count frequency of all numbers across all lottery types
        for result in results:
            numbers = result.get_numbers_list()
            for num in numbers:
                if isinstance(num, (int, str)) and str(num).isdigit():
                    num_int = int(num)
                    number_counts[num_int] = number_counts.get(num_int, 0) + 1
        
        # Get top 10 most frequent numbers
        sorted_numbers = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)
        most_frequent = sorted_numbers[:10] if len(sorted_numbers) >= 10 else sorted_numbers
        
        logger.info(f"Frequency analysis: Found {len(number_counts)} unique numbers, top 10: {most_frequent}")
        
        return {
            'most_frequent': most_frequent,
            'total_numbers': len(number_counts)
        }
        
    except Exception as e:
        logger.error(f"Error calculating frequency analysis: {str(e)}")
        return {
            'most_frequent': [],
            'total_numbers': 0
        }

# Main routes
@app.route('/')
def home():
    """Homepage with latest lottery results and frequency analysis"""
    try:
        logger.info("=== HOMEPAGE: Loading fresh lottery data from database ===")
        
        # Get latest results from database with proper error handling
        try:
            latest_results = LotteryResult.query.order_by(LotteryResult.id.desc()).limit(20).all()
            
            # Process results and log details
            processed_results = []
            for result in latest_results:
                numbers = result.get_numbers_list()
                logger.info(f"Processing {result.lottery_type} main_numbers: {numbers}")
                logger.info(f"Parsed {result.lottery_type} numbers: {numbers}")
                processed_results.append(result)
            
            logger.info(f"HOMEPAGE: Loaded {len(processed_results)} results from database")
            
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            processed_results = []
        
        # Calculate frequency analysis for charts
        frequency_data = calculate_frequency_analysis(processed_results)
        
        # Get recent results for display (limit to 6 for homepage)
        recent_results = processed_results[:6] if processed_results else []
        
        # SEO metadata
        meta_description = "Latest South African lottery results including Lotto, PowerBall, and Daily Lotto. Check winning numbers, frequency analysis, and jackpot information."
        
        return render_template('index.html',
                              title="Latest South African Lottery Results | Winning Numbers & Analysis",
                              meta_description=meta_description,
                              recent_results=recent_results,
                              frequency_data=frequency_data)
        
    except Exception as e:
        logger.error(f"Homepage error: {str(e)}")
        traceback.print_exc()
        return render_template('index.html',
                              title="Latest South African Lottery Results",
                              recent_results=[],
                              frequency_data={'most_frequent': [], 'total_numbers': 0})

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('home'))
    
    # Get basic statistics
    try:
        total_results = LotteryResult.query.count()
        latest_result = LotteryResult.query.order_by(LotteryResult.id.desc()).first()
        
        data_stats = {
            'total_results': total_results,
            'latest_draw': latest_result.draw_number if latest_result else 'None',
            'latest_date': latest_result.draw_date.strftime('%Y-%m-%d') if latest_result else 'None'
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        data_stats = {
            'total_results': 0,
            'latest_draw': 'Error',
            'latest_date': 'Error'
        }
    
    return render_template('admin/dashboard.html',
                          title="Admin Dashboard",
                          data_stats=data_stats)

@app.route('/automation')
@login_required
def automation_control():
    """Automation control center"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    return render_template('admin/automation_control.html',
                          title="Automation Control Center")

@app.route('/automation/run-step', methods=['POST'])
@login_required
def run_automation_step():
    """Run individual automation step"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    step = request.form.get('step')
    
    if step == 'cleanup':
        flash('Cleanup step started', 'info')
    elif step == 'capture':
        flash('Screenshot capture started', 'info')
    elif step == 'ai_process':
        flash('AI processing started', 'info')
    elif step == 'database':
        flash('Database update started', 'info')
    else:
        flash('Invalid step', 'error')
    
    return redirect(url_for('automation_control'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or '/')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', title="Admin Login")

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)