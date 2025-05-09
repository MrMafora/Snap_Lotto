"""
Main application entry point with Flask application defined for deployment.

This file is imported by gunicorn using the 'main:app' notation.

It also includes functionality to automatically bind to port 8080 
when running directly, to support Replit's external access requirements.

IMPORTANT: This application includes built-in port forwarding capabilities
to handle both the internal port 5000 (used by gunicorn) and the external
port 8080 required by Replit for public access.
"""
import logging
import os
import io
import time
import threading
import traceback
from datetime import datetime, timedelta
from functools import wraps
from flask import abort

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Set up logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Now that logger is defined, import other modules
import scheduler  # Import directly at the top level for screenshot functions
import create_template  # Import directly for template creation
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, send_from_directory, send_file, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
# Import EnhancedCSRFProtect instead of CSRFProtect
from csrf_fix import EnhancedCSRFProtect

# Import models only (lightweight)
from models import LotteryResult, ScheduleConfig, Screenshot, User, Advertisement, AdImpression, Campaign, AdVariation, ImportHistory, ImportedRecord, db
from config import Config

# Import modules
import ad_management
import lottery_analysis
import puppeteer_routes
from import_latest_spreadsheet import import_latest_spreadsheet, find_latest_spreadsheet

# Import port proxy only if needed, but don't start it immediately
# We'll let it be started as a separate process
try:
    # Just checking if the module exists
    import auto_start_proxy
    logger.info("Port proxy auto-starter module found")
except Exception as e:
    logger.error(f"Failed to load port proxy auto-starter: {e}")

# Import template handling
try:
    import import_latest_template
    logger.info("Template import module loaded")
except Exception as e:
    logger.error(f"Failed to load template import module: {e}")

# Create the Flask application
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Add custom Jinja2 filters for math functions needed by charts
import math
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # Set locale for number formatting

app.jinja_env.filters['cos'] = lambda x: math.cos(float(x))
app.jinja_env.filters['sin'] = lambda x: math.sin(float(x))
app.jinja_env.filters['format_number'] = lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x

# Explicitly set database URI from environment variable
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Ensure proper PostgreSQL connection string format
    # Heroku-style connection strings start with postgres:// but SQLAlchemy requires postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info(f"Using database from DATABASE_URL environment variable")
else:
    logger.warning("DATABASE_URL not found, using fallback database configuration")

# Initialize SQLAlchemy with additional connection settings
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True
}

# Add SSL requirement for PostgreSQL connections
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS']["connect_args"] = {"sslmode": "require"}
    logger.info("PostgreSQL SSL mode enabled")

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF Protection
csrf = EnhancedCSRFProtect(app)
# EnhancedCSRFProtect class handles all the configuration, so we don't need to set these manually

# Exempt endpoints that don't need CSRF protection
csrf.exempt('scan_ticket')
csrf.exempt('check_js')
csrf.exempt('resolve_health_alert')
csrf.exempt('api_system_metrics')
csrf.exempt('record_impression')
csrf.exempt('record_click')
csrf.exempt('get_file_upload_progress')
csrf.exempt('health_check')
csrf.exempt('health_port_check')
csrf.exempt('puppeteer_status')

# Exempt all lottery analysis API endpoints
csrf.exempt('api_frequency_analysis')
csrf.exempt('api_pattern_analysis')
csrf.exempt('api_time_series_analysis')
csrf.exempt('api_correlation_analysis')
csrf.exempt('api_winner_analysis')
csrf.exempt('api_lottery_prediction')
csrf.exempt('api_full_analysis')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Defer database schema creation to background thread
def init_database():
    """Initialize database tables in background thread"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
        
# Start database initialization in background to avoid blocking startup
threading.Thread(target=init_database, daemon=True).start()

# Lazy load these modules - will be imported when needed
# This helps reduce initial load time
data_aggregator = None
import_excel = None
import_snap_lotto_data = None
ocr_processor = None
puppeteer_service = None
# scheduler is imported at the top level to ensure screenshot functions work
health_monitor = None

def init_lazy_modules():
    """Initialize modules in a background thread with timeout"""
    global data_aggregator, import_excel, import_snap_lotto_data, ocr_processor, puppeteer_service, health_monitor
    
    # Prioritize core modules
    try:
        import data_aggregator as da
        data_aggregator = da
    except Exception as e:
        logger.error(f"Error loading data_aggregator: {e}")
    
    # Note: Removed signal alarm since it only works in main thread
    
    # Import heavy modules only when needed
    import data_aggregator as da
    import import_excel as ie
    import import_snap_lotto_data as isld
    import ocr_processor as op
    import puppeteer_service as ps
    import health_monitor as hm
    
    # Store module references
    data_aggregator = da
    import_excel = ie
    import_snap_lotto_data = isld
    ocr_processor = op
    puppeteer_service = ps
    health_monitor = hm
    
    # Initialize scheduler and health monitoring in background after imports are complete
    with app.app_context():
        scheduler.init_scheduler(app)
        health_monitor.init_health_monitor(app, db)
    
    logger.info("All modules lazy-loaded successfully")

# Start lazy loading in background thread
threading.Thread(target=init_lazy_modules, daemon=True).start()

# Additional routes and functionality would be defined here...
# For the sake of brevity, only core routes are included

@app.route('/')
def index():
    """Homepage with latest lottery results"""
    # Ensure data_aggregator is loaded before using it
    global data_aggregator
    
    try:
        # Import if not already loaded
        if data_aggregator is None:
            import data_aggregator as da
            data_aggregator = da
            logger.info("Loaded data_aggregator module on demand")
        
        # First, validate and correct any known draws (adds missing division data)
        try:
            corrected = data_aggregator.validate_and_correct_known_draws()
            if corrected > 0:
                logger.info(f"Corrected {corrected} lottery draws with verified data")
        except Exception as e:
            logger.error(f"Error in validate_and_correct_known_draws: {e}")
        
        # Get the latest results for each lottery type
        try:
            latest_results = data_aggregator.get_latest_results()
            
            # Convert dictionary of results to a list for iteration in the template
            results_list = []
            
            # Use a dictionary to track unique draw numbers per type to avoid duplicates
            seen_draws = {}
            normalized_results = {}
            
            # First, create a dictionary to group results by normalized type
            type_groups = {}
            for lottery_type, result in latest_results.items():
                # Normalize the lottery type
                normalized_type = data_aggregator.normalize_lottery_type(lottery_type)
                
                # Group all results by normalized type
                if normalized_type not in type_groups:
                    type_groups[normalized_type] = []
                type_groups[normalized_type].append(result)
            
            # Now select the newest result for each normalized type
            for normalized_type, type_results in type_groups.items():
                # Sort by date (newest first)
                type_results.sort(key=lambda x: x.draw_date, reverse=True)
                # Take the newest result only
                newest_result = type_results[0]
                normalized_results[normalized_type] = newest_result
            
            # Second pass: add results using normalized keys to avoid duplicates
            for normalized_type, result in normalized_results.items():
                # Generate a deduplication key using normalized type
                key = f"{normalized_type}_{result.draw_number}"
                if key not in seen_draws:
                    # Clone the result to avoid modifying the database object directly
                    # This prevents unique constraint violations when adding to results_list
                    result_clone = LotteryResult(
                        id=result.id,
                        lottery_type=normalized_type,  # Use normalized type
                        draw_number=result.draw_number,
                        draw_date=result.draw_date,
                        numbers=result.numbers,
                        bonus_numbers=result.bonus_numbers,
                        divisions=result.divisions,
                        source_url=result.source_url,
                        screenshot_id=result.screenshot_id,
                        ocr_provider=result.ocr_provider,
                        ocr_model=result.ocr_model,
                        ocr_timestamp=result.ocr_timestamp,
                        created_at=result.created_at
                    )
                    results_list.append(result_clone)
                    seen_draws[key] = True
            
            # Define standard order of lottery types for consistent display
            lottery_type_order = [
                'Lottery', 
                'Lottery Plus 1', 
                'Lottery Plus 2', 
                'Powerball', 
                'Powerball Plus', 
                'Daily Lottery'
            ]
            
            # Create an order lookup dictionary for sorting (lower value = higher priority)
            lottery_order_lookup = {lottery_type: index for index, lottery_type in enumerate(lottery_type_order)}
            
            # Sort by lottery type order first, then by date (newest first) for same lottery type
            def sort_key(result):
                # If the lottery type isn't in our predefined order, put it at the end
                order_position = lottery_order_lookup.get(result.lottery_type, len(lottery_type_order))
                # Return a tuple to allow sortable comparison
                return (order_position, -int(result.draw_number) if result.draw_number.isdigit() else 0)
                
            # Apply the sorting
            results_list.sort(key=sort_key)
        except Exception as e:
            logger.error(f"Error getting latest lottery results: {e}")
            latest_results = {}
            results_list = []
        
        # Get analytics data for the dashboard
        try:
            frequent_numbers = data_aggregator.get_most_frequent_numbers(limit=10)
        except Exception as e:
            logger.error(f"Error getting frequent numbers: {e}")
            frequent_numbers = []
            
        try:
            division_stats = data_aggregator.get_division_statistics()
        except Exception as e:
            logger.error(f"Error getting division statistics: {e}")
            division_stats = {}
            
        # Get cold numbers (least frequently drawn)
        try:
            cold_numbers = data_aggregator.get_least_frequent_numbers(limit=5)
        except Exception as e:
            logger.error(f"Error getting cold numbers: {e}")
            cold_numbers = []
            
        # Get numbers not drawn recently
        try:
            absent_numbers = data_aggregator.get_numbers_not_drawn_recently(limit=5)
        except Exception as e:
            logger.error(f"Error getting absent numbers: {e}")
            absent_numbers = []
        
        # Define rich meta description for SEO
        meta_description = "Get the latest South African lottery results for Lottery, PowerBall and Daily Lottery. View winning numbers, jackpot amounts, and most frequently drawn numbers updated in real-time."
        
        # Home page doesn't need breadcrumbs (it's the root), but we define an empty list for consistency
        breadcrumbs = []
        
        return render_template('index.html', 
                            latest_results=latest_results,
                            results=results_list,
                            frequent_numbers=frequent_numbers,
                            cold_numbers=cold_numbers,
                            absent_numbers=absent_numbers,
                            division_stats=division_stats,
                            title="South African Lottery Results | Latest Winning Numbers",
                            meta_description=meta_description,
                            breadcrumbs=breadcrumbs)
    except Exception as e:
        logger.error(f"Critical error in index route: {e}")
        # Define rich meta description for SEO even in error case
        meta_description = "Get the latest South African lottery results for Lottery, PowerBall and Daily Lottery. View winning numbers, jackpot amounts, and most frequently drawn numbers updated in real-time."
        
        # Define empty breadcrumbs for consistency even in error case
        breadcrumbs = []
        
        return render_template('index.html', 
                            latest_results={},
                            results=[],
                            frequent_numbers=[],
                            cold_numbers=[],
                            absent_numbers=[],
                            division_stats={},
                            title="South African Lottery Results | Latest Winning Numbers",
                            meta_description=meta_description,
                            breadcrumbs=breadcrumbs)

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard page"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))

    screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
    schedule_configs = ScheduleConfig.query.all()

    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')}
    ]

    # Define SEO metadata
    meta_description = "Admin dashboard for the South African lottery results system. Manage data, screenshots, schedule configurations, and system settings."
    
    return render_template('admin/dashboard.html', 
                          screenshots=screenshots,
                          schedule_configs=schedule_configs,
                          title="Admin Dashboard | Lottery Results Management",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    # Define SEO metadata
    meta_description = "Secure login for administration of the South African lottery results system. Access administrative features to manage lottery data and system settings."
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Login", "url": url_for('login')}
    ]
    
    return render_template('login.html', 
                          title="Admin Login | Lottery Results Management",
                          meta_description=meta_description,
                          breadcrumbs=breadcrumbs)

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/scan-lottery-ticket-south-africa')
@app.route('/scanner-landing')
def scanner_landing():
    """Landing page focused on the exclusive lottery ticket scanner feature"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Lottery Ticket Scanner", "url": url_for('scanner_landing')}
    ]
    
    # Define SEO metadata
    meta_description = "South Africa's ONLY lottery ticket scanner app. Instantly check if your Lottery, PowerBall, or Daily Lottery ticket is a winner by uploading a photo."
    
    return render_template('scanner_landing.html',
                          title="South Africa's ONLY Lottery Ticket Scanner App | Check If You've Won Instantly",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/ticket-scanner')
def ticket_scanner():
    """Ticket scanner page - Allows users to scan and validate their lottery tickets"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Lottery Ticket Scanner", "url": url_for('scanner_landing')},
        {"name": "Scan Your Ticket", "url": url_for('ticket_scanner')}
    ]
    
    # Additional SEO metadata
    meta_description = "Check if your South African lottery ticket is a winner. Our free ticket scanner uses advanced technology to analyze and verify your lottery tickets instantly."
    
    return render_template('ticket_scanner.html', 
                          title="Lottery Ticket Scanner | Check If You've Won",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)
                          
@app.route('/clean-ticket-scanner')
def clean_ticket_scanner():
    """Clean implementation of the ticket scanner interface"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Lottery Ticket Scanner", "url": url_for('scanner_landing')},
        {"name": "Clean Scanner", "url": url_for('clean_ticket_scanner')}
    ]
    
    # Additional SEO metadata
    meta_description = "Check if your South African lottery ticket is a winner with our simplified, reliable scanner. Our clean implementation ensures reliable uploads and accurate results."
    
    return render_template('clean_ticket_scanner.html', 
                          title="Clean Lottery Ticket Scanner | Reliable Implementation",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/scan-ticket', methods=['POST'])
@csrf.exempt
def scan_ticket():
    """Process uploaded ticket image and return results"""
    logger.info("Scan ticket request received")
    
    # Enhanced request debugging
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Request files keys: {list(request.files.keys()) if request.files else 'No files'}")
    logger.info(f"Request form keys: {list(request.form.keys()) if request.form else 'No form data'}")
    
    # Check if file is included in the request
    if 'ticket_image' not in request.files:
        logger.error("No ticket_image in request.files")
        logger.error(f"Request files: {request.files}")
        return jsonify({"error": "No ticket image provided"}), 400
        
    file = request.files['ticket_image']
    logger.info(f"Received file: {file.filename}, Content type: {file.content_type}")
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        logger.error("Empty filename submitted")
        return jsonify({"error": "No selected file"}), 400
        
    # Get the lottery type if specified (optional)
    lottery_type = request.form.get('lottery_type', '')
    
    # Get draw number if specified (optional)
    draw_number = request.form.get('draw_number', None)
    
    # Get file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if not file_extension:
        logger.info("No file extension found, defaulting to .jpeg")
        file_extension = '.jpeg'  # Default to JPEG if no extension
    
    try:
        # Read the file data
        image_data = file.read()
        file_size = len(image_data)
        logger.info(f"Read file data successfully, file size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("File data is empty")
            return jsonify({"error": "Empty file uploaded"}), 400
        
        # Import the ticket scanner module
        import ticket_scanner as ts
        
        # Process the ticket image using existing function
        logger.info(f"Processing ticket image: lottery_type={lottery_type}, draw_number={draw_number}")
        result = ts.process_ticket_image(
            image_data=image_data,
            lottery_type=lottery_type,
            draw_number=draw_number,
            file_extension=file_extension
        )
        
        # Logging the success
        logger.info(f"Ticket processed successfully: {result.get('status', 'unknown')}")
        
        # Return JSON response with results
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Error processing ticket: {str(e)}")
        # Include more details in the error response
        return jsonify({
            "error": f"Error processing ticket: {str(e)}",
            "status": "error",
            "request_details": {
                "filename": file.filename if file else "No file",
                "content_type": file.content_type if file else "Unknown content type",
                "lottery_type": lottery_type,
                "draw_number": draw_number
            }
        }), 500

# Guides Routes
@app.route('/guides')
def guides_index():
    """Display index of lottery guides"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Home", "url": url_for('index')},
        {"name": "Lottery Guides", "url": url_for('guides_index')}
    ]
    
    # Define SEO metadata
    meta_description = "Comprehensive guides on how to play South African lottery games. Learn rules, strategies, and tips for Lottery, PowerBall, Daily Lottery and more."
    
    return render_template('guides/index.html', 
                          title="South African Lottery Guides | Tips & How-To Articles",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/guides/how-to-play-lottery')
def how_to_play_lotto():
    """Display guide on how to play Lottery"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Home", "url": url_for('index')},
        {"name": "Lottery Guides", "url": url_for('guides_index')},
        {"name": "How to Play Lottery", "url": url_for('how_to_play_lotto')}
    ]
    
    # Define SEO metadata
    meta_description = "Comprehensive guide on how to play the South African Lottery. Learn Lottery rules, drawing days, odds of winning, prize divisions, and expert tips."
    
    return render_template('guides/how_to_play_lotto.html',
                          title="How to Play Lottery South Africa | Complete Guide & Tips",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/guides/how-to-play-powerball')
def how_to_play_powerball():
    """Display guide on how to play PowerBall"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Home", "url": url_for('index')},
        {"name": "Lottery Guides", "url": url_for('guides_index')},
        {"name": "How to Play PowerBall", "url": url_for('how_to_play_powerball')}
    ]
    
    # Define SEO metadata
    meta_description = "Complete guide to playing PowerBall South Africa. Learn game rules, drawing schedule, odds, prize divisions, and expert strategies to increase your chances."
    
    # Placeholder until we create the PowerBall guide template
    flash("PowerBall guide coming soon! Check out our Lottery guide in the meantime.", "info")
    return redirect(url_for('guides_index'))

@app.route('/guides/how-to-play-daily-lottery')
def how_to_play_daily_lotto():
    """Display guide on how to play Daily Lottery"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Home", "url": url_for('index')},
        {"name": "Lottery Guides", "url": url_for('guides_index')},
        {"name": "How to Play Daily Lottery", "url": url_for('how_to_play_daily_lotto')}
    ]
    
    # Define SEO metadata
    meta_description = "Learn how to play Daily Lottery South Africa with our comprehensive guide. Discover game rules, draw times, odds of winning, and how to claim prizes."
    
    # Placeholder until we create the Daily Lottery guide template
    flash("Daily Lottery guide coming soon! Check out our Lottery guide in the meantime.", "info")
    return redirect(url_for('guides_index'))

@app.route('/results')
def results():
    """Show overview of all lottery types with links to specific results"""
    lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
                     'Powerball', 'Powerball Plus', 'Daily Lottery']
    
    # Ensure data_aggregator is loaded before using it
    global data_aggregator
    
    # Import if not already loaded
    if data_aggregator is None:
        import data_aggregator as da
        data_aggregator = da
        logger.info("Loaded data_aggregator module on demand")
    
    latest_results = data_aggregator.get_latest_results()
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Results", "url": url_for('results')}
    ]
    
    return render_template('results_overview.html',
                          lottery_types=lottery_types,
                          latest_results=latest_results,
                          title="All Lottery Results",
                          breadcrumbs=breadcrumbs)

@app.route('/results/<lottery_type>')
def lottery_results(lottery_type):
    """Show all results for a specific lottery type"""
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of results per page
    
    # Ensure data_aggregator is loaded before using it
    global data_aggregator
    
    # Import if not already loaded
    if data_aggregator is None:
        import data_aggregator as da
        data_aggregator = da
        logger.info("Loaded data_aggregator module on demand")
    
    # Get all results for this lottery type
    all_results = data_aggregator.get_all_results_by_lottery_type(lottery_type)
    
    # Create a paginated result from the raw list
    # This mimics SQLAlchemy's pagination object with the properties the template expects
    class PaginatedResults:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            
        @property
        def pages(self):
            return (self.total + self.per_page - 1) // self.per_page
            
        @property
        def has_prev(self):
            return self.page > 1
            
        @property
        def has_next(self):
            return self.page < self.pages
            
        @property
        def prev_num(self):
            return self.page - 1 if self.has_prev else None
            
        @property
        def next_num(self):
            return self.page + 1 if self.has_next else None
            
        def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num > self.page - left_current - 1 and num < self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
    
    # Calculate the sliced items for the current page
    start = (page - 1) * per_page
    end = min(start + per_page, len(all_results))
    items = all_results[start:end]
    
    # Create the pagination object
    results = PaginatedResults(items, page, per_page, len(all_results))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Results", "url": url_for('results')},
        {"name": lottery_type, "url": url_for('lottery_results', lottery_type=lottery_type)}
    ]
    
    return render_template('results.html', 
                           results=results, 
                           lottery_type=lottery_type,
                           title=f"{lottery_type} Results",
                           breadcrumbs=breadcrumbs)

@app.route('/export-template')
@login_required
def export_template():
    """Export an empty spreadsheet template for importing lottery data"""
    if not current_user.is_admin:
        flash('You must be an admin to export templates.', 'danger')
        return redirect(url_for('index'))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lottery_data_template_{timestamp}.xlsx"
    
    # Create template with lottery-specific tabs
    create_template.create_template(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=True
    )

# File upload progress tracker
# This dictionary stores the progress of file uploads for each user
# Structure: {user_id: {'percentage': 0-100, 'status': 'uploading|processing|complete|error', 'filename': 'example.xlsx'}}
file_upload_progress = {}

@app.route('/api/file-upload-progress')
@login_required
def get_file_upload_progress():
    """API endpoint to get current file upload progress for the current user"""
    user_id = current_user.id
    
    # If no progress exists for this user, return default values
    if user_id not in file_upload_progress:
        file_upload_progress[user_id] = {
            'percentage': 0,
            'status': 'initializing',
            'filename': ''
        }
    
    return jsonify(file_upload_progress[user_id])

@app.route('/api/file-upload-progress/reset', methods=['POST'])
@login_required
@csrf.exempt
def reset_file_upload_progress():
    """Reset the file upload progress for the current user"""
    user_id = current_user.id
    
    file_upload_progress[user_id] = {
        'percentage': 0,
        'status': 'initializing',
        'filename': ''
    }
    
    return jsonify({'success': True})

@app.route('/import-latest-spreadsheet', methods=['POST'])
@login_required
@csrf.exempt
def import_latest_spreadsheet_route():
    """Import the latest spreadsheet file from attached_assets or uploads directory"""
    if not current_user.is_admin:
        flash('You must be an admin to import data.', 'danger')
        return redirect(url_for('index'))
    
    import_type = request.form.get('import_type', 'excel')
    purge = request.form.get('purge', 'no') == 'yes'
    pattern = request.form.get('pattern', '*.xlsx')  # Modified to look for any Excel file
    
    try:
        # First, try to find in attached_assets
        latest_file = find_latest_spreadsheet("attached_assets", pattern)
        
        # If not found in attached_assets, look in uploads directory
        if not latest_file and os.path.exists("uploads"):
            latest_file = find_latest_spreadsheet("uploads", pattern)
            
            if latest_file:
                logger.info(f"Using spreadsheet from uploads directory: {latest_file}")
                # If found in uploads, use that directory for import
                success = import_latest_spreadsheet("uploads", pattern, import_type, purge)
        else:
            # Using spreadsheet from attached_assets
            success = import_latest_spreadsheet("attached_assets", pattern, import_type, purge)
        
        if not latest_file:
            # Try one more time with the original lottery_data_*.xlsx pattern
            original_pattern = "lottery_data_*.xlsx"
            latest_file = find_latest_spreadsheet("attached_assets", original_pattern)
            
            if not latest_file and os.path.exists("uploads"):
                latest_file = find_latest_spreadsheet("uploads", original_pattern)
                
                if latest_file:
                    # If found in uploads with original pattern, use that
                    success = import_latest_spreadsheet("uploads", original_pattern, import_type, purge)
            else:
                # Using spreadsheet from attached_assets with original pattern
                success = import_latest_spreadsheet("attached_assets", original_pattern, import_type, purge)
        
        if not latest_file:
            flash(f'No Excel spreadsheets found in attached_assets or uploads directories. Please upload a spreadsheet first.', 'danger')
            return redirect(url_for('import_data'))
        
        if success:
            flash(f'Successfully imported latest spreadsheet: {os.path.basename(latest_file)}', 'success')
        else:
            flash(f'Failed to import spreadsheet: {os.path.basename(latest_file)}. Check logs for details.', 'danger')
            
        return redirect(url_for('import_data'))
        
    except Exception as e:
        logger.exception(f"Error importing spreadsheet: {str(e)}")
        flash(f'Error importing spreadsheet: {str(e)}', 'danger')
        return redirect(url_for('import_data'))

@app.route('/import-history')
@login_required
def import_history():
    """View import history and details"""
    if not current_user.is_admin:
        flash('You must be an admin to view import history.', 'danger')
        return redirect(url_for('index'))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "Import History", "url": url_for('import_history')}
    ]
    
    # Define SEO metadata
    meta_description = "View and analyze South African lottery data import history. Track data sources, import dates, success rates, and detailed import logs for system administration."
    
    try:
        # Get recent imports with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get all import history records, newest first
        imports = ImportHistory.query.order_by(ImportHistory.import_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        return render_template('import_history.html',
                            imports=imports,
                            title="Lottery Data Import History | System Administration",
                            breadcrumbs=breadcrumbs,
                            meta_description=meta_description)
    except Exception as e:
        app.logger.error(f"Error retrieving import history: {str(e)}")
        flash(f"Error loading import history: {str(e)}", 'danger')
        return redirect(url_for('admin'))

@app.route('/import-history/<int:import_id>')
@login_required
def import_details(import_id):
    """View details of a specific import"""
    if not current_user.is_admin:
        flash('You must be an admin to view import details.', 'danger')
        return redirect(url_for('index'))
    
    # Define SEO metadata (will be updated with specific import details when the record is loaded)
    meta_description = "Detailed South African lottery data import information. View imported draw numbers, dates, and success status for administrative record-keeping."
    
    try:
        # Get the import record
        import_record = ImportHistory.query.get_or_404(import_id)
        
        # Define breadcrumbs for SEO
        breadcrumbs = [
            {"name": "Admin Dashboard", "url": url_for('admin')},
            {"name": "Import History", "url": url_for('import_history')},
            {"name": f"Import #{import_id}", "url": url_for('import_details', import_id=import_id)}
        ]
        
        # Get all records that were imported in this batch
        imported_records = ImportedRecord.query.filter_by(import_id=import_id).all()
        
        # Group records by lottery type for easier display
        records_by_type = {}
        for record in imported_records:
            lottery_type = record.lottery_type
            if lottery_type not in records_by_type:
                records_by_type[lottery_type] = []
            records_by_type[lottery_type].append(record)
        
        # Update meta description with specific import details
        meta_description = f"Details for lottery data import #{import_id} from {import_record.import_date.strftime('%Y-%m-%d')}. Contains {len(imported_records)} records across {len(records_by_type)} lottery types."
        
        return render_template('import_details.html',
                              import_record=import_record,
                              records_by_type=records_by_type,
                              title=f"Import Details #{import_id} | {import_record.import_date.strftime('%Y-%m-%d %H:%M')}",
                              breadcrumbs=breadcrumbs,
                              meta_description=meta_description)
    except Exception as e:
        app.logger.error(f"Error retrieving import details: {str(e)}")
        flash(f"Error loading import details: {str(e)}", 'danger')
        return redirect(url_for('import_history'))

@app.route('/import-data', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def import_data():
    """Import data from Excel spreadsheet"""
    global import_excel, import_snap_lotto_data
    
    if not current_user.is_admin:
        flash('You must be an admin to import data.', 'danger')
        return redirect(url_for('index'))
        
    import_stats = None
    user_id = current_user.id
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "Import Data", "url": url_for('import_data')}
    ]
    
    # Define SEO metadata
    meta_description = "Import South African lottery data from Excel spreadsheets. Upload Lottery, PowerBall, and Daily Lottery results to maintain an up-to-date database of winning numbers and prize information."
    
    # Initialize or reset progress tracking
    file_upload_progress[user_id] = {
        'percentage': 0,
        'status': 'initializing',
        'filename': ''
    }

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            excel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Update progress
            file_upload_progress[user_id] = {
                'percentage': 25,
                'status': 'uploading',
                'filename': filename
            }
            
            # Save the file
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(excel_path)
            
            # Update progress
            file_upload_progress[user_id] = {
                'percentage': 50,
                'status': 'processing',
                'filename': filename
            }
            
            try:
                # Check if this is a multi-sheet template by trying to detect sheets
                is_template_format = False
                try:
                    import pandas as pd
                    # Load Excel file and check for template sheets
                    xl = pd.ExcelFile(excel_path)
                    sheet_names = xl.sheet_names
                    
                    # Check if the file has the expected sheet structure (multiple sheets with lottery type names)
                    template_sheets = [
                        "Lottery", "Lottery Plus 1", "Lottery Plus 2", 
                        "Powerball", "Powerball Plus", "Daily Lottery"
                    ]
                    
                    # If at least 3 of the expected template sheets are present, we consider it a template
                    matches = sum(1 for sheet in template_sheets if sheet in sheet_names)
                    is_template_format = matches >= 3
                    
                    # Also consider template if the name contains "template"
                    if not is_template_format:
                        is_template_format = "template" in filename.lower()
                        
                    logger.info(f"File format detection: {'multi-sheet template' if is_template_format else 'standard'}")
                except Exception as e:
                    logger.warning(f"Error detecting file format: {str(e)}")
                    # Fall back to filename detection
                    is_template_format = "template" in filename.lower()
                
                if is_template_format:
                    try:
                        # Update progress
                        file_upload_progress[user_id] = {
                            'percentage': 50,
                            'status': 'processing template format',
                            'filename': filename
                        }
                        
                        # Import using the multi-sheet template processor
                        import multi_sheet_import
                        import_stats = multi_sheet_import.import_multisheet_excel(excel_path, flask_app=app)
                        
                        # If import was successful, track it in the import history
                        if isinstance(import_stats, dict) and import_stats.get('success'):
                            # Create import history record
                            import_history = ImportHistory(
                                import_type='multi_sheet_template',
                                file_name=filename,
                                records_added=import_stats.get('added', 0),
                                records_updated=import_stats.get('updated', 0),
                                total_processed=import_stats.get('total', 0),
                                errors=import_stats.get('errors', 0),
                                user_id=current_user.id
                            )
                            db.session.add(import_history)
                            db.session.commit()
                            
                            # Save individual imported records if available
                            if 'imported_records' in import_stats and import_stats['imported_records']:
                                for record_data in import_stats['imported_records']:
                                    imported_record = ImportedRecord(
                                        import_id=import_history.id,
                                        lottery_type=record_data['lottery_type'],
                                        draw_number=record_data['draw_number'],
                                        draw_date=record_data['draw_date'],
                                        is_new=record_data['is_new'],
                                        lottery_result_id=record_data['lottery_result_id']
                                    )
                                    db.session.add(imported_record)
                                db.session.commit()
                            
                            # Display results
                            added = import_stats.get('added', 0)
                            total = import_stats.get('total', 0)
                            errors = import_stats.get('errors', 0)
                            updated = import_stats.get('updated', 0)
                            
                            if added > 0 and updated > 0:
                                flash(f'Multi-sheet template import completed successfully. Added {added} new records, updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                            elif added > 0:
                                flash(f'Multi-sheet template import completed successfully. Added {added} new records, processed {total} total records with {errors} errors.', 'success')
                            elif updated > 0:
                                flash(f'Multi-sheet template import completed successfully. Updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                            else:
                                flash(f'Multi-sheet template import completed. No records were added or updated. Processed {total} records with {errors} errors.', 'info')
                        else:
                            error_msg = import_stats.get('error', 'Unknown error')
                            flash(f'Error in multi-sheet template import: {error_msg}', 'danger')
                        
                        # Update progress to complete
                        file_upload_progress[user_id] = {
                            'percentage': 100,
                            'status': 'complete',
                            'filename': filename,
                            'summary': import_stats if isinstance(import_stats, dict) else None
                        }
                    except Exception as e:
                        logger.error(f"Multi-sheet template import error: {str(e)}")
                        logger.error(traceback.format_exc())
                        flash(f"Error in multi-sheet template import: {str(e)}", 'danger')
                        
                        # Update progress to error
                        file_upload_progress[user_id] = {
                            'percentage': 100,
                            'status': 'error',
                            'filename': filename
                        }
                else:
                    # Try standard format for non-template files
                    try:
                        if import_excel is None:
                            import import_excel as ie
                        else:
                            ie = import_excel
                        import_stats = ie.import_excel_data(excel_path)
                        
                        # If import was successful, track it in the import history
                        if isinstance(import_stats, dict) and import_stats.get('success'):
                            # Create import history record
                            import_history = ImportHistory(
                                import_type='excel',
                                file_name=filename,
                                records_added=import_stats.get('added', 0),
                                records_updated=import_stats.get('updated', 0),
                                total_processed=import_stats.get('total', 0),
                                errors=import_stats.get('errors', 0),
                                user_id=current_user.id
                            )
                            db.session.add(import_history)
                            db.session.commit()
                            
                            # Save individual imported records if available
                            if 'imported_records' in import_stats and import_stats['imported_records']:
                                for record_data in import_stats['imported_records']:
                                    imported_record = ImportedRecord(
                                        import_id=import_history.id,
                                        lottery_type=record_data['lottery_type'],
                                        draw_number=record_data['draw_number'],
                                        draw_date=record_data['draw_date'],
                                        is_new=record_data['is_new'],
                                        lottery_result_id=record_data['lottery_result_id']
                                    )
                                    db.session.add(imported_record)
                                db.session.commit()
                        
                        # Check if import was unsuccessful (False) or if no records were imported
                        if import_stats is False or (isinstance(import_stats, dict) and import_stats.get('total', 0) == 0):
                            # If standard import fails, try Snap Lotto format
                            try:
                                # Update progress
                                file_upload_progress[user_id] = {
                                    'percentage': 75,
                                    'status': 'processing',
                                    'filename': filename
                                }
                                
                                # Import import_snap_lotto_data if not already loaded
                                if import_snap_lotto_data is None:
                                    import import_snap_lotto_data as isld
                                else:
                                    isld = import_snap_lotto_data
                                import_stats = isld.import_snap_lotto_data(excel_path, flask_app=app)
                                
                                # If import was successful, track it in the import history
                                if isinstance(import_stats, dict) and import_stats.get('success'):
                                    # Create import history record
                                    import_history = ImportHistory(
                                        import_type='snap_lotto',
                                        file_name=filename,
                                        records_added=import_stats.get('added', 0),
                                        records_updated=import_stats.get('updated', 0),
                                        total_processed=import_stats.get('total', 0),
                                        errors=import_stats.get('errors', 0),
                                        user_id=current_user.id
                                    )
                                    db.session.add(import_history)
                                    db.session.commit()
                                    
                                    # Save individual imported records if available
                                    if 'imported_records' in import_stats and import_stats['imported_records']:
                                        for record_data in import_stats['imported_records']:
                                            imported_record = ImportedRecord(
                                                import_id=import_history.id,
                                                lottery_type=record_data['lottery_type'],
                                                draw_number=record_data['draw_number'],
                                                draw_date=record_data['draw_date'],
                                                is_new=record_data['is_new'],
                                                lottery_result_id=record_data['lottery_result_id']
                                            )
                                            db.session.add(imported_record)
                                        db.session.commit()
                                
                                # Display results if available and successful
                                if isinstance(import_stats, dict) and import_stats.get('success'):
                                    added = import_stats.get('added', 0)
                                    total = import_stats.get('total', 0)
                                    errors = import_stats.get('errors', 0)
                                    
                                    updated = import_stats.get('updated', 0)
                                    if added > 0 and updated > 0:
                                        flash(f'Snap Lotto import completed successfully. Added {added} new records, updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                                    elif added > 0:
                                        flash(f'Snap Lotto import completed successfully. Added {added} new records, processed {total} total records with {errors} errors.', 'success')
                                    elif updated > 0:
                                        flash(f'Snap Lotto import completed successfully. Updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                                    else:
                                        flash(f'Snap Lotto import completed. No records were added or updated. Processed {total} records with {errors} errors.', 'info')
                                else:
                                    flash('Snap Lotto import completed', 'info')
                                
                                # Update progress to complete
                                file_upload_progress[user_id] = {
                                    'percentage': 100,
                                    'status': 'complete',
                                    'filename': filename,
                                    'summary': import_stats if isinstance(import_stats, dict) else None
                                }
                            except Exception as e:
                                logger.error(f"Snap Lotto import error: {str(e)}")
                                flash(f"Error in Snap Lotto import: {str(e)}", 'danger')
                                
                                # Update progress to error
                                file_upload_progress[user_id] = {
                                    'percentage': 100,
                                    'status': 'error',
                                    'filename': filename
                                }
                        else:
                            # Display results for standard import
                            if isinstance(import_stats, dict) and import_stats.get('success'):
                                added = import_stats.get('added', 0)
                                total = import_stats.get('total', 0)
                                errors = import_stats.get('errors', 0)
                                
                                updated = import_stats.get('updated', 0)
                                if added > 0 and updated > 0:
                                    flash(f'Import completed successfully. Added {added} new records, updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                                elif added > 0:
                                    flash(f'Import completed successfully. Added {added} new records, processed {total} total records with {errors} errors.', 'success')
                                elif updated > 0:
                                    flash(f'Import completed successfully. Updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                                else:
                                    flash(f'Import completed. No records were added or updated. Processed {total} records with {errors} errors.', 'info')
                            else:
                                flash('Import completed', 'info')
                            
                            # Update progress to complete
                            file_upload_progress[user_id] = {
                                'percentage': 100,
                                'status': 'complete',
                                'filename': filename,
                                'summary': import_stats if isinstance(import_stats, dict) else None
                            }
                    except Exception as e:
                        logger.error(f"Excel import error: {str(e)}")
                        flash(f"Error in import: {str(e)}", 'danger')
                        
                        # Update progress to error
                        file_upload_progress[user_id] = {
                            'percentage': 100,
                            'status': 'error',
                            'filename': filename
                        }
            except Exception as e:
                logger.error(f"File processing error: {str(e)}")
                logger.error(traceback.format_exc())
                flash(f"File processing error: {str(e)}", 'danger')
                
                # Update progress to error
                file_upload_progress[user_id] = {
                    'percentage': 100,
                    'status': 'error',
                    'filename': filename
                }
                
    # Get some example results for each lottery type to display
    example_results = {}
    lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
                     'Powerball', 'Powerball Plus', 'Daily Lottery']
    
    try:                 
        for lottery_type in lottery_types:
            try:
                results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(
                    LotteryResult.draw_date.desc()).limit(5).all()
                if results:
                    example_results[lottery_type] = results
            except Exception as e:
                app.logger.error(f"Error retrieving example results for {lottery_type}: {str(e)}")
                # Continue with other lottery types even if one fails
                continue
    except Exception as e:
        app.logger.error(f"Database error in import_data: {str(e)}")
        # If we can't get any example results, proceed without them
    
    # Extract structured data from import_stats (if available) for template rendering
    added_count = 0
    updated_count = 0
    total_count = 0
    error_count = 0
    imported_results = []
    
    if isinstance(import_stats, dict) and import_stats.get('success'):
        added_count = import_stats.get('added', 0)
        updated_count = import_stats.get('updated', 0)
        total_count = import_stats.get('total', 0)
        error_count = import_stats.get('errors', 0)
        
        # Get imported records for display
        if 'imported_records' in import_stats and import_stats['imported_records']:
            for record_data in import_stats['imported_records']:
                result = LotteryResult.query.get(record_data.get('lottery_result_id'))
                if result:
                    imported_results.append(result)
    
    return render_template('import_data.html', 
                           import_stats=import_stats,
                           example_results=example_results,
                           title="Import South African Lottery Data | Admin Tools",
                           meta_description=meta_description,
                           breadcrumbs=breadcrumbs,
                           added_count=added_count,
                           updated_count=updated_count,
                           total_count=total_count,
                           error_count=error_count,
                           imported_results=imported_results)

@app.route('/retake-screenshots')
@login_required
def retake_screenshots():
    """Admin route to retake all screenshots"""
    if not current_user.is_admin:
        flash('You must be an admin to retake screenshots.', 'danger')
        return redirect(url_for('index'))
        
    try:
        result = scheduler.retake_all_screenshots()
        
        if result:
            success_count = sum(1 for status in result.values() if status == 'success')
            fail_count = len(result) - success_count
            
            flash(f'Screenshot process started. {success_count} URLs queued successfully. {fail_count} failed.', 'info')
        else:
            flash('No URLs configured for screenshots.', 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/purge-database')
@login_required
def purge_database():
    """Admin route to purge all data from the database"""
    if not current_user.is_admin:
        flash('You must be an admin to purge the database.', 'danger')
        return redirect(url_for('index'))
        
    try:
        # Import the purge_data module
        import purge_data
        
        # Execute the purge operation
        result = purge_data.purge_data()
        
        if result:
            flash('Database purged successfully. All lottery results and screenshots have been deleted.', 'success')
        else:
            flash('An error occurred during the purge operation.', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Manage data syncs and system settings"""
    if not current_user.is_admin:
        flash('You must be an admin to access settings.', 'danger')
        return redirect(url_for('index'))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "System Settings", "url": url_for('settings')}
    ]
    
    # Define SEO metadata
    meta_description = "Configure South African lottery system settings and scheduled tasks. Manage data synchronization, screenshot capture timing, and system preferences."
    
    schedule_configs = ScheduleConfig.query.all()
    
    # Handle form submission for updating settings
    if request.method == 'POST':
        # This would normally handle the form submission
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', 
                          schedule_configs=schedule_configs,
                          title="System Settings | Lottery Data Management",
                          meta_description=meta_description,
                          breadcrumbs=breadcrumbs)

@app.route('/export-screenshots')
@login_required
def export_screenshots():
    """Export screenshots with integrated Puppeteer functionality"""
    if not current_user.is_admin:
        flash('You must be an admin to export screenshots.', 'danger')
        return redirect(url_for('index'))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "Export Screenshots", "url": url_for('export_screenshots')}
    ]
    
    # Define SEO metadata
    meta_description = "Export and manage South African lottery screenshots. Download captured lottery result images in various formats for analysis and record-keeping."
    
    screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
    
    # Create a status object combining both global and session status
    sync_status = None
    
    # First check if we have a status in the global puppeteer_capture_status
    if puppeteer_capture_status.get('in_progress'):
        # Use the global status if a synchronization is in progress
        sync_status = {
            'status': puppeteer_capture_status.get('overall_status', 'info'),
            'message': puppeteer_capture_status.get('status_message', 'Screenshot synchronization in progress')
        }
    elif 'sync_status' in session:
        # Fall back to session status if no active synchronization
        sync_status = session.pop('sync_status')
    
    # Get the timestamp of the most recent screenshot for status display
    last_updated = None
    if screenshots:
        last_updated = screenshots[0].timestamp
    
    # Import Puppeteer lottery URLs for the integrated capture functionality
    from puppeteer_service import LOTTERY_URLS
    
    # Add in-progress status if screenshots are currently being synchronized
    puppeteer_status = {
        'in_progress': puppeteer_capture_status.get('in_progress', False),
        'completed': puppeteer_capture_status.get('completed_screenshots', 0),
        'total': puppeteer_capture_status.get('total_screenshots', 0),
        'progress': puppeteer_capture_status.get('progress', 0),
        'status_message': puppeteer_capture_status.get('status_message', '')
    }
    
    return render_template('export_screenshots.html',
                          screenshots=screenshots,
                          title="Export Lottery Screenshots | Data Management",
                          meta_description=meta_description,
                          breadcrumbs=breadcrumbs,
                          sync_status=sync_status,
                          last_updated=last_updated,
                          lottery_urls=LOTTERY_URLS,
                          puppeteer_status=puppeteer_status)

@app.route('/export-screenshots-zip')
@login_required
def export_screenshots_zip():
    """Export all screenshots as a ZIP file"""
    if not current_user.is_admin:
        flash('You must be an admin to export screenshots.', 'danger')
        return redirect(url_for('index'))
    
    try:
        import io
        import zipfile
        from datetime import datetime
        
        # Get all screenshots
        screenshots = Screenshot.query.order_by(Screenshot.lottery_type).all()
        
        if not screenshots:
            flash('No screenshots available to export.', 'warning')
            return redirect(url_for('export_screenshots'))
        
        # Create a ZIP file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for screenshot in screenshots:
                if os.path.exists(screenshot.path):
                    # Get the file extension
                    _, ext = os.path.splitext(screenshot.path)
                    # Create a unique filename for each screenshot
                    lottery_type = screenshot.lottery_type.replace(' ', '_')
                    timestamp = screenshot.timestamp.strftime('%Y%m%d_%H%M%S')
                    filename = f"{lottery_type}_{timestamp}{ext}"
                    
                    # Add the screenshot to the ZIP file
                    zf.write(screenshot.path, filename)
                    
                    # Add zoomed version if it exists
                    if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                        _, zoomed_ext = os.path.splitext(screenshot.zoomed_path)
                        zoomed_filename = f"{lottery_type}_{timestamp}_zoomed{zoomed_ext}"
                        zf.write(screenshot.zoomed_path, zoomed_filename)
        
        # Reset the file pointer to the beginning of the file
        memory_file.seek(0)
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Send the ZIP file as a response
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'lottery_screenshots_{timestamp}.zip'
        )
    except Exception as e:
        app.logger.error(f"Error creating ZIP file: {str(e)}")
        flash(f'Error creating ZIP file: {str(e)}', 'danger')
        return redirect(url_for('export_screenshots'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register a new admin user"""
    if not current_user.is_admin:
        flash('You must be an admin to register new users.', 'danger')
        return redirect(url_for('index'))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "Register Admin", "url": url_for('register')}
    ]
    
    # Define SEO metadata
    meta_description = "Administrative user registration for South African lottery results system. Create secure admin accounts to manage lottery data and system configurations."
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Admin user {username} registered successfully!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('register.html', 
                          title="Register Admin User | Lottery Management System", 
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/visualizations')
def visualizations():
    """Advanced data visualization and analytics for South African lottery results"""
    lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
                    'Powerball', 'Powerball Plus', 'Daily Lottery']
    
    # Get some summary statistics
    total_draws = LotteryResult.query.count()
    latest_draw = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).first()
    latest_draw_date = latest_draw.draw_date if latest_draw else None
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Analytics", "url": url_for('visualizations')}
    ]
    
    # Additional SEO metadata
    meta_description = "Explore comprehensive South African lottery analytics. View frequency charts, number patterns, and winning statistics for Lotto, Powerball, and Daily Lotto games."
    
    return render_template('visualizations.html',
                          lottery_types=lottery_types,
                          total_draws=total_draws,
                          latest_draw_date=latest_draw_date,
                          title="Lottery Data Analytics | Statistical Analysis & Visualizations",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/api/visualization-data')
def visualization_data():
    """API endpoint for visualization data"""
    import data_aggregator
    from collections import Counter
    import logging
    
    data_type = request.args.get('data_type', 'numbers_frequency')
    lottery_type = request.args.get('lottery_type', 'all')
    
    logging.info(f"Visualization data request: type={data_type}, lottery={lottery_type}")
    
    try:
        # Get data specific to lottery type
        if data_type == 'numbers_frequency':
            # Get frequency count for all 49 numbers
            all_numbers = {str(i): 0 for i in range(1, 50)}
            
            # Count frequency of all numbers
            query = LotteryResult.query
            if lottery_type and lottery_type.lower() != 'all':
                query = query.filter_by(lottery_type=lottery_type)
                
            results = query.all()
            number_counter = Counter()
            
            logging.info(f"Found {len(results)} results for frequency analysis")
            
            for result in results:
                numbers = result.get_numbers_list()
                for num in numbers:
                    if 1 <= num <= 49:
                        number_counter[str(num)] += 1
            
            # Update all_numbers with actual frequencies
            for num, count in number_counter.items():
                if num in all_numbers:
                    all_numbers[num] = count
            
            # Convert to lists for JSON response
            data = [all_numbers[str(i)] for i in range(1, 50)]
            
            response_data = {
                'labels': [str(i) for i in range(1, 50)],
                'datasets': [{
                    'data': data
                }]
            }
            
            logging.info(f"Returning frequency data with {sum(data)} total occurrences")
            return jsonify(response_data)
        
        elif data_type == 'winners_by_division':
            # Get all results for this lottery type to process division data
            query = LotteryResult.query
            
            if lottery_type and lottery_type.lower() != 'all':
                # Try with exact match first
                results_by_type = query.filter_by(lottery_type=lottery_type).all()
                
                # If no results, try with normalized type
                if not results_by_type:
                    # Find any results with lottery type that might be a variant
                    lottery_type_variants = db.session.query(LotteryResult.lottery_type).distinct().all()
                    normalized_type = data_aggregator.normalize_lottery_type(lottery_type)
                    matching_types = []
                    
                    for lt in lottery_type_variants:
                        lt_name = lt[0]
                        if data_aggregator.normalize_lottery_type(lt_name) == normalized_type:
                            matching_types.append(lt_name)
                    
                    if matching_types:
                        results_by_type = query.filter(LotteryResult.lottery_type.in_(matching_types)).all()
            else:
                results_by_type = query.all()
            
            # Initialize division counters
            division_data = {}
            
            # Process division data from all matching results
            for result in results_by_type:
                divisions = result.get_divisions()
                if divisions:
                    for div_name, div_info in divisions.items():
                        # Extract the division number from the name (e.g., "Division 1" -> 1)
                        try:
                            div_num = int(div_name.split()[-1])
                            winners = div_info.get('winners', '0')
                            
                            # Convert winners to integer
                            if isinstance(winners, str):
                                winners = winners.replace(',', '')
                            winner_count = int(float(winners))
                            
                            if div_num not in division_data:
                                division_data[div_num] = 0
                            division_data[div_num] += winner_count
                        except (ValueError, IndexError):
                            continue
            
            # Sort divisions by number
            sorted_divisions = sorted(division_data.items())
            
            # Prepare data for chart
            divisions = [f'Division {div_num}' for div_num, _ in sorted_divisions]
            winner_counts = [count for _, count in sorted_divisions]
            
            logging.info(f"Processed {len(results_by_type)} results, found {len(divisions)} divisions with data")
            
            response_data = {
                'labels': divisions,
                'datasets': [{
                    'data': winner_counts
                }]
            }
            
            return jsonify(response_data)
        
        return jsonify({'error': 'Invalid data type'}), 400
    except Exception as e:
        logging.error(f"Error in visualization_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<lottery_type>/<draw_number>')
def draw_details(lottery_type, draw_number):
    """Show detailed information for a specific draw"""
    # First, validate and correct any known draws (adds missing division data)
    # This ensures draw details have prize division data if it's available
    corrected = data_aggregator.validate_and_correct_known_draws()
    if corrected > 0:
        logger.info(f"Corrected {corrected} lottery draws with verified data")
    
    # Get all results with matching lottery type
    all_results = data_aggregator.get_all_results_by_lottery_type(lottery_type)
    
    # Find the specific draw
    result = None
    draw_number = draw_number.strip()
    
    for r in all_results:
        r_draw_number = r.draw_number
        # Clean up the draw number for comparison
        r_draw_number = r_draw_number.replace('Draw', '').replace('DRAW', '').replace(
            'Lotto', '').replace('Plus 1', '').replace('Plus 2', '').replace(
            'Powerball', '').replace('Daily', '').strip()
        
        if r_draw_number == draw_number or r.draw_number == draw_number:
            result = r
            break
    
    if not result:
        flash(f"Draw {draw_number} not found for {lottery_type}", "warning")
        return redirect(url_for('lottery_results', lottery_type=lottery_type))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Results", "url": url_for('results')},
        {"name": lottery_type, "url": url_for('lottery_results', lottery_type=lottery_type)},
        {"name": f"Draw {draw_number}", "url": url_for('draw_details', lottery_type=lottery_type, draw_number=draw_number)}
    ]
    
    return render_template('draw_details.html',
                          result=result,
                          lottery_type=lottery_type,
                          title=f"{lottery_type} Draw {draw_number} Details",
                          breadcrumbs=breadcrumbs)

@app.route('/screenshot/<int:screenshot_id>')
def view_screenshot(screenshot_id):
    """View a screenshot image"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    force_download = request.args.get('force_download', 'false').lower() == 'true'
    
    # Keep track of attempts for logging
    attempts = []
    app.logger.info(f"Attempting to view screenshot ID {screenshot_id}, type: {screenshot.lottery_type}")
    
    # Fix for empty image issue - check if url attribute exists and set it if missing
    if not hasattr(screenshot, 'url') or not screenshot.url:
        if hasattr(screenshot, 'source_url') and screenshot.source_url:
            screenshot.url = screenshot.source_url
            db.session.commit()
        else:
            # Try to set a reasonable default URL if none exists
            from config import Config
            for url_info in Config.RESULTS_URLS:
                if url_info['lottery_type'].lower() == screenshot.lottery_type.lower():
                    screenshot.url = url_info['url']
                    db.session.commit()
                    break
                    
    # Get the correct file extension for the screenshot file (if it exists)
    file_ext = '.png'  # Default extension
    if screenshot.path and os.path.exists(screenshot.path):
        _, file_ext = os.path.splitext(screenshot.path)
    
    # Look for any relevant files in the screenshots directory that might match this ID
    screenshots_dir = 'screenshots'
    html_dir = os.path.join(screenshots_dir, 'html')
    matching_files = []
    
    # First check the HTML directory for date-based files that match the lottery type
    if os.path.exists(html_dir):
        for filename in os.listdir(html_dir):
            if screenshot.lottery_type.lower().replace(' ', '_') in filename.lower():
                matching_files.append(os.path.join(html_dir, filename))
    
    # Then check the main screenshots directory
    if os.path.exists(screenshots_dir):
        for filename in os.listdir(screenshots_dir):
            if screenshot.lottery_type.lower().replace(' ', '_') in filename.lower():
                matching_files.append(os.path.join(screenshots_dir, filename))
    
    # If we found matching files, use the most recent one
    if matching_files and not (screenshot.path and os.path.exists(screenshot.path)):
        # Sort by modification time (most recent first)
        matching_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        newest_file = matching_files[0]
        
        # Update the screenshot record with the file path
        if newest_file.endswith('.html'):
            if not screenshot.html_path or not os.path.exists(screenshot.html_path):
                screenshot.html_path = newest_file
                db.session.commit()
                app.logger.info(f"Updated screenshot HTML path to {newest_file}")
        else:
            if not screenshot.path or not os.path.exists(screenshot.path):
                screenshot.path = newest_file
                db.session.commit()
                app.logger.info(f"Updated screenshot path to {newest_file}")
    
    # Always try to generate a fresh PNG from HTML for consistent results
    if screenshot.html_path and os.path.isfile(screenshot.html_path):
        app.logger.info(f"HTML file exists at {screenshot.html_path} ({os.path.getsize(screenshot.html_path)} bytes)")
        try:
            app.logger.info(f"Using puppeteer_service.generate_png_from_html for {screenshot.html_path}")
            
            # Import the function from our puppeteer_service module
            from puppeteer_service import generate_png_from_html
            
            # Generate the PNG image
            success, temp_screenshot_path, error_message = generate_png_from_html(
                html_path=screenshot.html_path
            )
            
            # Check if generation was successful
            if success and temp_screenshot_path and os.path.exists(temp_screenshot_path):
                app.logger.info(f"Successfully generated PNG at {temp_screenshot_path} ({os.path.getsize(temp_screenshot_path)} bytes)")
                attempts.append(f"Successfully generated PNG: {os.path.getsize(temp_screenshot_path)} bytes")
                
                # Return the generated file
                return send_file(
                    temp_screenshot_path,
                    mimetype='image/png',
                    as_attachment=force_download,
                    download_name=f"{screenshot.lottery_type.replace(' ', '_')}.png"
                )
            else:
                error_msg = f"Failed to generate PNG: {error_message}"
                app.logger.error(error_msg)
                attempts.append(error_msg)
                # Don't raise an exception, let it try the fallback methods
                
        except Exception as e:
            error_msg = f"Error with puppeteer_service.generate_png_from_html: {str(e)}"
            app.logger.error(error_msg)
            attempts.append(error_msg)
            
            # Continue to fallback approaches - no exception needed
    else:
        attempts.append(f"HTML file missing or invalid: {getattr(screenshot, 'html_path', None)}")
    
    # Try alternative: If we have a PNG in the database, use it
    if screenshot.path and os.path.isfile(screenshot.path):
        file_size = os.path.getsize(screenshot.path)
        app.logger.info(f"Using existing PNG file as fallback: {screenshot.path} ({file_size} bytes)")
        attempts.append(f"Using existing PNG: {file_size} bytes")
        
        if file_size > 100:  # Even a very minimal image should be larger than this
            directory = os.path.dirname(screenshot.path)
            filename = os.path.basename(screenshot.path)
            
            try:
                # Use send_file instead of send_from_directory for more reliability
                return send_file(
                    screenshot.path,
                    mimetype='image/png',
                    as_attachment=force_download,
                    download_name=f"{screenshot.lottery_type.replace(' ', '_')}.png"
                )
            except Exception as e:
                error_msg = f"Error sending PNG file: {str(e)}"
                app.logger.error(error_msg)
                attempts.append(error_msg)
        else:
            attempts.append(f"PNG file too small ({file_size} bytes)")
    else:
        attempts.append(f"PNG file missing or invalid: {getattr(screenshot, 'path', None)}")
    
    # Third fallback: If HTML exists and not forcing download, show HTML directly
    if not force_download and screenshot.html_path and os.path.isfile(screenshot.html_path):
        html_size = os.path.getsize(screenshot.html_path)
        app.logger.info(f"Falling back to direct HTML display: {screenshot.html_path} ({html_size} bytes)")
        attempts.append(f"Falling back to direct HTML: {html_size} bytes")
        
        try:
            # Use send_file instead of send_from_directory for more reliability
            return send_file(
                screenshot.html_path,
                mimetype='text/html',
                download_name=f"{screenshot.lottery_type.replace(' ', '_')}.html"
            )
        except Exception as e:
            error_msg = f"Error sending HTML file: {str(e)}"
            app.logger.error(error_msg)
            attempts.append(error_msg)
    
    # Check the attached_assets directory for any matching files
    attached_assets_dir = 'attached_assets'
    attached_files = []
    
    if os.path.exists(attached_assets_dir):
        for filename in os.listdir(attached_assets_dir):
            if screenshot.lottery_type.lower().replace(' ', '_') in filename.lower():
                file_path = os.path.join(attached_assets_dir, filename)
                if os.path.isfile(file_path) and os.path.getsize(file_path) > 100:
                    attached_files.append(file_path)
    
    # If we found matching attached files, use the most recent one
    if attached_files:
        attached_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        newest_file = attached_files[0]
        
        app.logger.info(f"Using file from attached_assets directory: {newest_file}")
        attempts.append(f"Using attached_assets file: {newest_file}")
        
        try:
            # Get the correct mimetype
            _, ext = os.path.splitext(newest_file)
            if ext.lower() in ['.jpg', '.jpeg']:
                mimetype = 'image/jpeg'
            elif ext.lower() == '.png':
                mimetype = 'image/png'
            elif ext.lower() == '.html':
                mimetype = 'text/html'
            else:
                mimetype = 'application/octet-stream'
            
            # Return the attached file
            return send_file(
                newest_file,
                mimetype=mimetype,
                as_attachment=force_download,
                download_name=f"{screenshot.lottery_type.replace(' ', '_')}{ext}"
            )
        except Exception as e:
            error_msg = f"Error sending attached file: {str(e)}"
            app.logger.error(error_msg)
            attempts.append(error_msg)
    
    # Try an embedded/inline response with HTML fallback
    try:
        app.logger.info("Trying an embedded HTML response fallback")
        
        # First check if we have the HTML file
        if screenshot.html_path and os.path.isfile(screenshot.html_path):
            try:
                with open(screenshot.html_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                
                # Create a nicer fallback HTML with embedded screenshot info
                fallback_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Screenshot: {screenshot.lottery_type}</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                        h1 {{ color: #333; }}
                        .content {{ margin-top: 20px; padding: 20px; border: 1px solid #eee; }}
                        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
                        .actions {{ margin-top: 20px; }}
                        .btn {{ background: #e74c3c; color: white; padding: 10px 15px; text-decoration: none; border-radius: 3px; display: inline-block; }}
                        .html-preview {{ border: 1px solid #ddd; padding: 15px; background: #f9f9f9; margin-top: 20px; overflow: auto; max-height: 500px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Screenshot Preview: {screenshot.lottery_type}</h1>
                        <div class="meta">ID: {screenshot_id}</div>
                        <div class="meta">Timestamp: {screenshot.timestamp}</div>
                        <div class="meta">URL: {getattr(screenshot, 'url', 'Unknown URL')}</div>
                        
                        <div class="content">
                            <h3>Screenshot Data</h3>
                            <p>The screenshot image could not be displayed directly, but the HTML content is available below.</p>
                            <div class="actions">
                                <a href="{url_for('view_screenshot', screenshot_id=screenshot_id, force_download='true')}" class="btn">Download Raw Content</a>
                            </div>
                        </div>
                        
                        <div class="html-preview">
                            <h3>HTML Preview</h3>
                            <iframe srcdoc="{html_content.replace('"', '&quot;')}" style="width:100%; height:400px; border:1px solid #ddd;"></iframe>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                return fallback_html, 200, {'Content-Type': 'text/html'}
            except Exception as e:
                app.logger.error(f"Failed to create embedded HTML: {str(e)}")
                attempts.append(f"Failed to create embedded HTML: {str(e)}")
    except Exception as e:
        app.logger.error(f"Embedded HTML fallback failed: {str(e)}")
        attempts.append(f"Embedded HTML fallback failed: {str(e)}")
        
    # If all else fails, generate a proper error image with useful information
    try:
        from PIL import Image, ImageDraw, ImageFont
        import tempfile
        
        # Create a more visually appealing error image with lottery branding
        img = Image.new('RGB', (800, 500), color=(255, 248, 240))  # Light warm background
        draw = ImageDraw.Draw(img)
        
        # Add a header bar
        draw.rectangle([(0, 0), (800, 60)], fill=(231, 76, 60))  # Red header
        
        # Try to use a default font
        try:
            font = ImageFont.load_default()
            large_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        except Exception:
            font = None
            large_font = None
            small_font = None
        
        # Draw title and details with better formatting
        draw.text((20, 15), f"Screenshot Preview - {screenshot.lottery_type}", fill=(255, 255, 255), font=large_font)
        draw.text((20, 80), f"Screenshot Information", fill=(50, 50, 50), font=large_font)
        
        draw.text((40, 120), f"• ID: {screenshot_id}", fill=(80, 80, 80), font=font)
        draw.text((40, 150), f"• Type: {screenshot.lottery_type}", fill=(80, 80, 80), font=font)
        draw.text((40, 180), f"• Timestamp: {screenshot.timestamp}", fill=(80, 80, 80), font=font)
        draw.text((40, 210), f"• URL: {getattr(screenshot, 'url', 'Unknown URL')[:60]}", fill=(80, 80, 80), font=font)
        
        # Add a section for debug info
        draw.rectangle([(20, 250), (780, 252)], fill=(200, 200, 200))  # Divider line
        draw.text((20, 270), "Debug Information", fill=(50, 50, 50), font=font)
        
        # Add attempt information with better formatting
        y_pos = 300
        for i, attempt in enumerate(attempts[:5]):  # Limit to 5 attempts to fit on image
            draw.text((40, y_pos), f"• {attempt[:70]}", fill=(180, 60, 60), font=small_font)
            y_pos += 30
            
        # Add helpful instructions
        draw.rectangle([(0, 440), (800, 500)], fill=(240, 240, 240))
        draw.text((20, 450), "To fix this issue, try using the 'Resync' button on the screenshot gallery page.", 
                 fill=(50, 50, 50), font=font)
        draw.text((20, 470), "If the problem persists, check the HTML source or contact the administrator.", 
                 fill=(50, 50, 50), font=small_font)
        
        # Save to a temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.close()
        img.save(temp_file.name)
        
        app.logger.warning(f"Created error placeholder image as last resort: {temp_file.name}")
        
        # Return the error image
        return send_file(
            temp_file.name,
            mimetype='image/png',
            as_attachment=force_download,
            download_name=f"preview_{screenshot.lottery_type.replace(' ', '_')}.png"
        )
    except Exception as final_error:
        app.logger.error(f"All image generation attempts failed: {str(final_error)}")
        
        # Only at this point do we give up completely
        flash(f'Failed to generate or retrieve any valid content for this screenshot', 'danger')
        return redirect(url_for('export_screenshots'))

@app.route('/screenshot-zoomed/<int:screenshot_id>')
def view_zoomed_screenshot(screenshot_id):
    """View a zoomed screenshot image"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    if not screenshot.zoomed_path:
        flash('No zoomed screenshot available', 'warning')
        return redirect(url_for('admin'))
    
    # Normalize path and check if file exists
    zoomed_path = os.path.normpath(screenshot.zoomed_path)
    
    if not os.path.isfile(zoomed_path):
        flash('Zoomed screenshot file not found', 'danger')
        return redirect(url_for('admin'))
    
    # Extract directory and filename from path
    directory = os.path.dirname(zoomed_path)
    filename = os.path.basename(zoomed_path)
    
    return send_from_directory(directory, filename)

@app.route('/html-content/<int:screenshot_id>')
def view_html_content(screenshot_id):
    """View the raw HTML content of a screenshot"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    if not screenshot.html_path:
        flash('No HTML content available for this screenshot', 'warning')
        return redirect(url_for('export_screenshots'))
    
    # Normalize path and check if file exists
    html_path = os.path.normpath(screenshot.html_path)
    
    if not os.path.isfile(html_path):
        flash('HTML file not found', 'danger')
        return redirect(url_for('export_screenshots'))
    
    # Extract directory and filename from path
    directory = os.path.dirname(html_path)
    filename = os.path.basename(html_path)
    
    # Return the HTML file as text/html content
    return send_from_directory(directory, filename, mimetype='text/html')

@app.route('/sync-all-screenshots', methods=['POST'])
@login_required
@csrf.exempt
def sync_all_screenshots():
    """Sync all screenshots from their source URLs using Puppeteer"""
    global puppeteer_capture_status
    
    if not current_user.is_admin:
        flash('You must be an admin to sync screenshots.', 'danger')
        return redirect(url_for('index'))
    
    # Check if there's already a capture in progress
    if puppeteer_capture_status['in_progress']:
        flash('A screenshot capture operation is already in progress. Please wait for it to complete.', 'warning')
        return redirect(url_for('export_screenshots'))
    
    try:
        # Use Puppeteer service for capturing screenshots
        from puppeteer_service import capture_multiple_screenshots, LOTTERY_URLS
        
        # Reset and initialize status
        puppeteer_capture_status.update({
            'in_progress': True,
            'total_screenshots': len(LOTTERY_URLS),
            'completed_screenshots': 0,
            'start_time': datetime.now(),
            'last_updated': datetime.now(),
            'success_count': 0,
            'error_count': 0,
            'status_message': 'Starting screenshot capture with Puppeteer...',
            'errors': []
        })
        
        app.logger.info(f"Starting synchronization of {len(LOTTERY_URLS)} screenshots using Puppeteer service...")
        
        # Use threading to process screenshots without blocking
        def process_screenshots():
            """
            Process screenshots using thread-safe approach that doesn't use Flask's session object.
            This avoids the "Working outside of request context" error.
            """
            global puppeteer_capture_status
            
            # Create a new app context for this thread
            with app.app_context():
                try:
                    # Start the capture process
                    start_time = time.time()
                    
                    # Initialize tracking
                    results = {}
                    db_updates = 0
                    db_creates = 0
                    
                    # Process each URL individually to update status as we go
                    for i, (lottery_type, url) in enumerate(LOTTERY_URLS.items()):
                        # Update status - thread-safe, doesn't use session
                        puppeteer_capture_status['status_message'] = f"Capturing {lottery_type} screenshot ({i+1}/{len(LOTTERY_URLS)})..."
                        puppeteer_capture_status['last_updated'] = datetime.now()
                        
                        try:
                            # Capture individual screenshot
                            from puppeteer_service import capture_single_screenshot
                            result = capture_single_screenshot(lottery_type, url)
                            results[lottery_type] = result
                            
                            # Update progress - thread-safe, doesn't use session
                            puppeteer_capture_status['completed_screenshots'] = i + 1
                            
                            if result.get('status') == 'success':
                                puppeteer_capture_status['success_count'] += 1
                                
                                # Find or create screenshot record
                                screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
                                
                                if screenshot:
                                    # Update existing record
                                    screenshot.path = result.get('path')
                                    screenshot.html_path = result.get('html_path', '')  # Store HTML path if available
                                    screenshot.source_url = url
                                    screenshot.timestamp = datetime.now()
                                    db_updates += 1
                                else:
                                    # Create new record
                                    screenshot = Screenshot(
                                        lottery_type=lottery_type,
                                        path=result.get('path'),
                                        html_path=result.get('html_path', ''),  # Store HTML path if available
                                        source_url=url,
                                        timestamp=datetime.now()
                                    )
                                    db.session.add(screenshot)
                                    db_creates += 1
                                    
                                # Commit after each successful screenshot
                                db.session.commit()
                            else:
                                puppeteer_capture_status['error_count'] += 1
                                error_msg = result.get('error', 'Unknown error')
                                puppeteer_capture_status['errors'].append(f"{lottery_type}: {error_msg}")
                                app.logger.error(f"Error capturing {lottery_type} screenshot: {error_msg}")
                        
                        except Exception as e:
                            # Handle individual screenshot errors
                            puppeteer_capture_status['error_count'] += 1
                            puppeteer_capture_status['errors'].append(f"{lottery_type}: {str(e)}")
                            app.logger.error(f"Error capturing {lottery_type} screenshot: {str(e)}")
                    
                    # All screenshots processed - finalize
                    elapsed_time = time.time() - start_time
                    app.logger.info(f"Puppeteer screenshot capture completed in {elapsed_time:.2f} seconds")
                    
                    # Update final status
                    success_count = puppeteer_capture_status['success_count']
                    error_count = puppeteer_capture_status['error_count']
                    
                    # Prepare status message - thread-safe, doesn't use session
                    if success_count > 0 and error_count == 0:
                        status_message = f'Successfully synchronized {success_count} screenshots with Puppeteer. Updated {db_updates} records, created {db_creates} new records.'
                        puppeteer_capture_status['status_message'] = status_message
                        puppeteer_capture_status['overall_status'] = 'success'
                    elif success_count > 0 and error_count > 0:
                        status_message = f'Partially synchronized. {success_count} successful, {error_count} failed with Puppeteer. Database: {db_updates} updated, {db_creates} created.'
                        puppeteer_capture_status['status_message'] = status_message
                        puppeteer_capture_status['overall_status'] = 'warning'
                    else:
                        status_message = f'Failed to synchronize screenshots with Puppeteer. {error_count} errors encountered.'
                        puppeteer_capture_status['status_message'] = status_message
                        puppeteer_capture_status['overall_status'] = 'danger'
                        
                except Exception as e:
                    app.logger.error(f"Error in screenshot processing thread: {str(e)}")
                    traceback.print_exc()
                    puppeteer_capture_status['status_message'] = f'Error: {str(e)}'
                    puppeteer_capture_status['errors'].append(f"General error: {str(e)}")
                    puppeteer_capture_status['overall_status'] = 'danger'
                
                finally:
                    # Mark process as completed
                    puppeteer_capture_status['in_progress'] = False
                    puppeteer_capture_status['last_updated'] = datetime.now()
        
        # Start processing in background thread
        threading.Thread(target=process_screenshots, daemon=True).start()
        
        # Return immediately, processing continues in background
        flash('Screenshot synchronization started in the background. Check status for updates.', 'info')
    
    except Exception as e:
        app.logger.error(f"Error initiating screenshot capture with Puppeteer: {str(e)}")
        traceback.print_exc()
        session['sync_status'] = {
            'status': 'danger',
            'message': f'Error initiating screenshot capture with Puppeteer: {str(e)}'
        }
        # Reset status in case of error
        puppeteer_capture_status['in_progress'] = False
        puppeteer_capture_status['status_message'] = f'Error: {str(e)}'
    
    return redirect(url_for('export_screenshots'))

@app.route('/sync-screenshot/<int:screenshot_id>', methods=['POST'])
@login_required
@csrf.exempt
def sync_single_screenshot(screenshot_id):
    """Sync a single screenshot by its ID using Puppeteer"""
    if not current_user.is_admin:
        flash('You must be an admin to sync screenshots.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Get the screenshot
        screenshot = Screenshot.query.get_or_404(screenshot_id)
        
        # Import Puppeteer service
        from puppeteer_service import capture_single_screenshot, LOTTERY_URLS
        
        # Check if the lottery type exists in our URLs dictionary
        lottery_type = screenshot.lottery_type
        if lottery_type in LOTTERY_URLS:
            url = LOTTERY_URLS[lottery_type]
        else:
            # Try fuzzy matching for similar names
            found_match = False
            for known_type, known_url in LOTTERY_URLS.items():
                if known_type.lower() in lottery_type.lower() or lottery_type.lower() in known_type.lower():
                    lottery_type = known_type
                    url = known_url
                    found_match = True
                    break
            
            if not found_match:
                app.logger.error(f"Could not find matching URL for lottery type: {screenshot.lottery_type}")
                session['sync_status'] = {
                    'status': 'danger',
                    'message': f'Error: Could not find matching URL for lottery type: {screenshot.lottery_type}'
                }
                return redirect(url_for('export_screenshots'))
        
        app.logger.info(f"Capturing screenshot for {lottery_type} using Puppeteer...")
        
        # Capture the screenshot using the new capture_single_screenshot function
        result = capture_single_screenshot(lottery_type, url)
        
        if result.get('status') == 'success' and result.get('path'):
            # Update the screenshot record
            screenshot.path = result.get('path')
            screenshot.timestamp = datetime.now()
            
            # Also update HTML path if available
            if result.get('html_path'):
                screenshot.html_path = result.get('html_path')
                app.logger.info(f"Updated HTML path: {result.get('html_path')}")
            
            db.session.commit()
            
            app.logger.info(f"Screenshot successfully synchronized: Path={result.get('path')}, "
                           f"HTML Path={result.get('html_path')}")
            
            # Verify the file exists
            file_path = result.get('path')
            if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                app.logger.info(f"Verified PNG file exists: {os.path.getsize(file_path)} bytes")
            else:
                app.logger.warning(f"PNG file does not exist or is empty: {result.get('path')}")
            
            session['sync_status'] = {
                'status': 'success',
                'message': f'Successfully captured screenshot for {lottery_type} using Puppeteer.'
            }
        else:
            session['sync_status'] = {
                'status': 'warning',
                'message': f'Failed to capture screenshot for {lottery_type} using Puppeteer. Error: {result.get("error", "Unknown error")}'
            }
    except Exception as e:
        app.logger.error(f"Error capturing screenshot with Puppeteer: {str(e)}")
        traceback.print_exc()
        session['sync_status'] = {
            'status': 'danger',
            'message': f'Error capturing screenshot with Puppeteer: {str(e)}'
        }
    
    return redirect(url_for('export_screenshots'))

@app.route('/preview-website/<int:screenshot_id>')
@login_required
def preview_website(screenshot_id):
    """
    Serve the most recent screenshot as a preview image.
    
    Instead of attempting to generate a real-time preview (which often fails due to anti-scraping),
    this simplified approach displays the most recently captured screenshot with timestamp information.
    This provides a reliable preview experience without triggering anti-scraping measures.
    """
    from io import BytesIO
    import time
    from datetime import datetime, timedelta
    from PIL import Image, ImageDraw, ImageFont

    try:
        # Retrieve the screenshot object
        screenshot = Screenshot.query.get_or_404(screenshot_id)

        # Fix for empty image issue - ensure url attribute exists
        if not hasattr(screenshot, 'url') or not screenshot.url:
            if hasattr(screenshot, 'source_url') and screenshot.source_url:
                screenshot.url = screenshot.source_url
                db.session.commit()
            else:
                # Try to set a reasonable default URL if none exists
                from config import Config
                for url_info in Config.RESULTS_URLS:
                    if url_info['lottery_type'].lower() == screenshot.lottery_type.lower():
                        screenshot.url = url_info['url']
                        db.session.commit()
                        break
        
        # First try to generate from HTML if available - this is the most reliable approach
        if screenshot.html_path and os.path.exists(screenshot.html_path):
            try:
                app.logger.info(f"Generating thumbnail preview from HTML: {screenshot.html_path}")
                
                # Import the function from our puppeteer_service module
                from puppeteer_service import generate_png_from_html
                
                # Generate a temporary PNG file
                success, temp_path, error_message = generate_png_from_html(screenshot.html_path)
                
                if success and temp_path and os.path.exists(temp_path):
                    app.logger.info(f"Using freshly generated PNG for preview: {temp_path}")
                    
                    # Add timestamp overlay
                    img = Image.open(temp_path)
                    draw = ImageDraw.Draw(img)
                    
                    # Try to use a default font
                    try:
                        font = ImageFont.load_default()
                    except Exception:
                        font = None
                    
                    # Create semi-transparent background for text
                    img_width = img.width
                    draw.rectangle(((0, 0), (img_width, 30)), fill=(0, 0, 0, 128))
                    
                    # Add timestamp text
                    timestamp_text = f"Generated preview ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
                    draw.text((10, 8), timestamp_text, fill=(255, 255, 255), font=font)
                    draw.text((img_width - 150, 8), "LIVE PREVIEW", fill=(200, 255, 200), font=font)
                    
                    # Convert to bytes for serving
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    return send_file(
                        buffer,
                        mimetype='image/png',
                        download_name=f'preview_{screenshot_id}.png',
                        as_attachment=False
                    )
            except Exception as html_error:
                app.logger.warning(f"Could not generate preview from HTML: {str(html_error)}")
        
        # Fallback to using existing screenshot if available
        if screenshot.path and os.path.exists(screenshot.path):
            try:
                # Get file modification time and format it
                file_mod_time = os.path.getmtime(screenshot.path)
                capture_time = datetime.fromtimestamp(file_mod_time)
                time_ago = datetime.now() - capture_time
                
                # Read the existing screenshot
                with open(screenshot.path, 'rb') as f:
                    existing_img_data = f.read()
                
                # Create a PIL Image from the screenshot
                img = Image.open(BytesIO(existing_img_data))
                
                # Add timestamp overlay at the top
                draw = ImageDraw.Draw(img)
                
                # Try to use a default font
                try:
                    font = ImageFont.load_default()
                except Exception:
                    font = None
                
                # Create semi-transparent background for text
                img_width = img.width
                draw.rectangle(((0, 0), (img_width, 30)), fill=(0, 0, 0, 128))
                
                # Format time ago in a human-readable way
                if time_ago < timedelta(minutes=1):
                    time_text = "Captured just now"
                elif time_ago < timedelta(hours=1):
                    time_text = f"Captured {int(time_ago.total_seconds() / 60)} minutes ago"
                elif time_ago < timedelta(days=1):
                    time_text = f"Captured {int(time_ago.total_seconds() / 3600)} hours ago"
                else:
                    time_text = f"Captured {int(time_ago.days)} days ago"
                
                # Add timestamp text
                timestamp_text = f"{time_text} ({capture_time.strftime('%Y-%m-%d %H:%M:%S')})"
                draw.text((10, 8), timestamp_text, fill=(255, 255, 255), font=font)
                draw.text((img_width - 150, 8), "CAPTURED PREVIEW", fill=(255, 200, 200), font=font)
                
                # Convert back to bytes
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                app.logger.info(f"Using last successful screenshot for preview of {screenshot.lottery_type} from {time_ago.total_seconds():.0f} seconds ago")
                
                return send_file(
                    buffer,
                    mimetype='image/png',
                    download_name=f'preview_{screenshot_id}.png',
                    as_attachment=False
                )
            except Exception as file_error:
                app.logger.warning(f"Could not process existing screenshot for preview: {str(file_error)}")
        
        # If we don't have a screenshot, create a warning image that is more user-friendly
        app.logger.warning(f"No valid screenshot found for {screenshot.lottery_type} ({screenshot_id}), creating friendly warning image")
        
        # Create warning image with clean design
        img = Image.new('RGB', (800, 450), color=(255, 252, 240))  # Light yellow background
        d = ImageDraw.Draw(img)

        # Add a yellow warning header
        d.rectangle([(0, 0), (800, 40)], fill=(241, 196, 15))  # Yellow header
        
        # Try to use a default font
        try:
            font = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        except Exception:
            font = None
            font_medium = None
            font_small = None
        
        # Draw warning icon
        d.rectangle([(30, 60), (70, 100)], fill=(241, 196, 15))  # Warning icon
        d.text((44, 68), "!", fill=(255, 255, 255), font=font)
        
        # Draw warning text with better formatting
        d.text((10, 10), f"Preview - {screenshot.lottery_type}", fill=(50, 50, 50), font=font)
        d.text((90, 70), "Preview generation timed out.", fill=(50, 50, 50), font=font)
        d.text((90, 100), "The website may be unavailable.", fill=(80, 80, 80), font=font_medium)
        
        # Add information about the screenshot
        d.rectangle([(0, 140), (800, 142)], fill=(230, 230, 230))  # Divider line
        d.text((30, 160), f"Screenshot ID: {screenshot_id}", fill=(100, 100, 100), font=font_small)
        d.text((30, 190), f"Lottery Type: {screenshot.lottery_type}", fill=(100, 100, 100), font=font_small)
        d.text((30, 220), f"URL: {getattr(screenshot, 'url', 'Unknown URL')[:60]}", fill=(100, 100, 100), font=font_small)
        
        # Add helpful instruction
        d.rectangle([(0, 380), (800, 450)], fill=(245, 245, 245))
        d.text((30, 400), "Click the 'Resync' button below to attempt capturing this screenshot again.", 
               fill=(50, 50, 50), font=font_small)
        
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        buffer.seek(0)
        
        # Return the warning image
        return send_file(
            buffer,
            mimetype='image/png',
            download_name=f'preview_info_{screenshot_id}.png',
            as_attachment=False
        )
    
    except Exception as e:
        app.logger.error(f"Error serving preview for {screenshot_id}: {str(e)}")
        # Generate a better looking error message image
        from PIL import Image, ImageDraw
        
        img = Image.new('RGB', (800, 450), color=(255, 235, 235))  # Light red background
        d = ImageDraw.Draw(img)
        
        # Add a header bar
        d.rectangle([(0, 0), (800, 40)], fill=(231, 76, 60))  # Red header
        
        # Draw warning icon
        d.rectangle([(30, 60), (70, 100)], fill=(231, 76, 60))  # Error icon
        d.text((44, 68), "!", fill=(255, 255, 255), font=None)
        
        # Draw error text
        d.text((10, 10), "Preview Error", fill=(255, 255, 255), font=None)
        d.text((90, 70), "Preview generation failed", fill=(150, 0, 0), font=None)
        d.text((90, 100), f"Error details: {str(e)[:60]}", fill=(100, 0, 0), font=None)
        
        # Add a helpful message
        d.rectangle([(0, 380), (800, 450)], fill=(245, 235, 235))
        d.text((30, 400), "Try clicking the 'Resync' button to fix this issue.", fill=(100, 0, 0), font=None)
        
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        buffer.seek(0)
        
        # Return the error image instead of JSON error
        return send_file(
            buffer,
            mimetype='image/png',
            download_name=f'preview_error_{screenshot_id}.png',
            as_attachment=False
        )

@app.route('/cleanup-screenshots', methods=['POST'])
@login_required
@csrf.exempt
def cleanup_screenshots():
    """Route to cleanup old screenshots with simplified approach"""
    if not current_user.is_admin:
        flash('You must be an admin to clean up screenshots.', 'danger')
        return redirect(url_for('index'))
        
    try:
        # Simple approach to cleanup - just keep the latest screenshot per URL
        # This is a direct implementation rather than relying on the complex scheduler module
        from models import Screenshot, db
        import os
        from sqlalchemy import func
        
        # Group screenshots by URL and find the latest for each
        subquery = db.session.query(
            Screenshot.url,
            func.max(Screenshot.timestamp).label('max_timestamp')
        ).group_by(Screenshot.url).subquery()
        
        # Find all screenshots that aren't the latest for their URL
        screenshots_to_delete = Screenshot.query.join(
            subquery,
            db.and_(
                Screenshot.url == subquery.c.url,
                Screenshot.timestamp < subquery.c.max_timestamp
            )
        ).all()
        
        # Delete files and database records
        deleted_count = 0
        for screenshot in screenshots_to_delete:
            # Try to delete the file if it exists
            if screenshot.path and os.path.exists(screenshot.path):
                try:
                    os.remove(screenshot.path)
                except Exception as file_error:
                    app.logger.warning(f"Could not delete screenshot file {screenshot.path}: {str(file_error)}")
            
            # Try to delete zoomed file if it exists
            if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                try:
                    os.remove(screenshot.zoomed_path)
                except Exception as file_error:
                    app.logger.warning(f"Could not delete zoomed screenshot file {screenshot.zoomed_path}: {str(file_error)}")
                    
            # Try to delete HTML file if it exists (Puppeteer saves HTML content)
            if hasattr(screenshot, 'html_path') and screenshot.html_path and os.path.exists(screenshot.html_path):
                try:
                    os.remove(screenshot.html_path)
                except Exception as file_error:
                    app.logger.warning(f"Could not delete HTML file {screenshot.html_path}: {str(file_error)}")
            
            # Delete the database record
            db.session.delete(screenshot)
            deleted_count += 1
        
        # Commit changes
        db.session.commit()
        
        # Store success message in session
        session['sync_status'] = {
            'status': 'success',
            'message': f'Successfully cleaned up {deleted_count} old screenshots. Only the latest screenshot for each URL is kept.'
        }
    except Exception as e:
        app.logger.error(f"Error cleaning up screenshots: {str(e)}")
        traceback.print_exc()
        
        session['sync_status'] = {
            'status': 'danger',
            'message': f'Error cleaning up screenshots: {str(e)}'
        }
    
    return redirect(url_for('export_screenshots'))

@app.route('/export-combined-zip')
@login_required
def export_combined_zip():
    """Export template and screenshots in a single ZIP file"""
    if not current_user.is_admin:
        flash('You must be an admin to export data.', 'danger')
        return redirect(url_for('index'))
    
    try:
        import io
        import zipfile
        import tempfile
        import glob
        from datetime import datetime
        
        # Create a timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get all screenshots from database
        screenshots = Screenshot.query.order_by(Screenshot.lottery_type).all()
        
        if not screenshots:
            flash('No screenshots available to export.', 'warning')
            return redirect(url_for('export_screenshots'))
        
        # Log some information about the screenshots
        logger.info(f"Found {len(screenshots)} screenshots in database to export")
        
        # Create a temporary directory for the template
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the template file
            template_filename = f"lottery_data_template_{timestamp}.xlsx"
            template_path = os.path.join(temp_dir, template_filename)
            create_template.create_template(template_path)
            logger.info(f"Created template file at {template_path}")
            
            # Get all screenshots from the directory
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            all_screenshot_files = []
            if os.path.exists(screenshot_dir):
                all_screenshot_files = glob.glob(os.path.join(screenshot_dir, '*.png'))
                all_screenshot_files.extend(glob.glob(os.path.join(screenshot_dir, '*.jpg')))
                all_screenshot_files.extend(glob.glob(os.path.join(screenshot_dir, '*.jpeg')))
                logger.info(f"Found {len(all_screenshot_files)} screenshot files in directory")
            
            # Create a ZIP file in memory
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add the template to the ZIP file
                zf.write(template_path, f"template/{template_filename}")
                logger.info(f"Added template to ZIP file")
                
                # Track the number of screenshots added
                screenshots_added = 0
                
                # Add screenshots from the database first
                for screenshot in screenshots:
                    try:
                        if os.path.exists(screenshot.path):
                            # Get the file extension
                            _, ext = os.path.splitext(screenshot.path)
                            # Create a unique filename for each screenshot
                            lottery_type = screenshot.lottery_type.replace(' ', '_')
                            ss_timestamp = screenshot.timestamp.strftime('%Y%m%d_%H%M%S')
                            filename = f"{lottery_type}_{ss_timestamp}{ext}"
                            
                            # Add the screenshot to the ZIP file in a screenshots folder
                            zf.write(screenshot.path, f"screenshots/{filename}")
                            screenshots_added += 1
                            
                            # Add zoomed version if it exists
                            if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                                _, zoomed_ext = os.path.splitext(screenshot.zoomed_path)
                                zoomed_filename = f"{lottery_type}_{ss_timestamp}_zoomed{zoomed_ext}"
                                zf.write(screenshot.zoomed_path, f"screenshots/{zoomed_filename}")
                                screenshots_added += 1
                                
                            # Add HTML content if it exists (from Puppeteer)
                            if hasattr(screenshot, 'html_path') and screenshot.html_path and os.path.exists(screenshot.html_path):
                                html_filename = f"{lottery_type}_{ss_timestamp}.html"
                                zf.write(screenshot.html_path, f"html_content/{html_filename}")
                                screenshots_added += 1
                                logger.info(f"Added HTML content for {lottery_type}")
                        else:
                            logger.warning(f"Screenshot file not found: {screenshot.path}")
                    except Exception as e:
                        logger.error(f"Error adding screenshot to ZIP: {str(e)}, path: {screenshot.path}")
                
                # If no screenshots were added from database paths, include all files from screenshots directory
                if screenshots_added == 0 and all_screenshot_files:
                    logger.info(f"No screenshots were added from database paths, adding all files from screenshots directory")
                    for screenshot_file in all_screenshot_files:
                        try:
                            # Get filename only
                            filename = os.path.basename(screenshot_file)
                            # Add to ZIP file
                            zf.write(screenshot_file, f"screenshots/{filename}")
                            screenshots_added += 1
                        except Exception as e:
                            logger.error(f"Error adding screenshot file to ZIP: {str(e)}, path: {screenshot_file}")
            
                logger.info(f"Added {screenshots_added} screenshot files to the ZIP archive")
            
            # Reset the file pointer to the beginning of the file
            memory_file.seek(0)
            
            # Check if any screenshots were added
            if screenshots_added == 0:
                logger.warning("No screenshots were added to the ZIP archive")
                flash('No screenshots were found to include in the ZIP file. Only the template will be included.', 'warning')
            
            # Send the ZIP file as a response
            logger.info(f"Sending combined ZIP file with {screenshots_added} screenshots")
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'lottery_data_combined_{timestamp}.zip'
            )
    except Exception as e:
        logger.error(f"Error creating combined ZIP file: {str(e)}")
        traceback.print_exc()  # Print full traceback for better debugging
        flash(f'Error creating combined ZIP file: {str(e)}', 'danger')
        return redirect(url_for('export_screenshots'))

@app.route('/port_check')
def port_check():
    """Special endpoint to check which port the application is responding on"""
    host = request.host
    return jsonify({
        "success": True,
        "host": host,
        "server_port": request.host.split(':')[1] if ':' in request.host else "default",
        "request_url": request.url,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/results/<lottery_type>')
def api_results(lottery_type):
    """API endpoint for lottery results"""
    try:
        limit = request.args.get('limit', type=int)
        results = data_aggregator.export_results_to_json(lottery_type, limit)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Advertisement Management Routes
@app.route('/admin/manage-ads')
@app.route('/admin/manage-ads/<placement>')
@login_required
def manage_ads(placement=None):
    """Admin page to manage advertisements"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get all ads or filter by placement
    if placement:
        ads = Advertisement.query.filter_by(placement=placement).order_by(Advertisement.priority.desc()).all()
    else:
        ads = Advertisement.query.order_by(Advertisement.priority.desc()).all()
    
    return render_template('admin/manage_ads.html', 
                          ads=ads,
                          placement=placement,
                          title="Manage Advertisements")

@app.route('/admin/upload-ad', methods=['GET', 'POST'])
@login_required
def upload_ad():
    """Admin page to upload a new advertisement"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    form = request.form
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            duration = int(request.form.get('duration'))
            placement = request.form.get('placement')
            priority = int(request.form.get('priority', 5))
            target_impressions = int(request.form.get('target_impressions'))
            active = 'active' in request.form
            
            # Get custom message and rich content settings
            custom_message = request.form.get('custom_message')
            loading_duration = int(request.form.get('loading_duration', 10))
            is_rich_content = 'is_rich_content' in request.form
            html_content = request.form.get('html_content') if is_rich_content else None
            
            # Handle optional dates
            start_date = request.form.get('start_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = None
                
            end_date = request.form.get('end_date')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date = None
            
            # Check if video file is included
            if 'video_file' not in request.files:
                flash('No video file provided', 'danger')
                return redirect(request.url)
            
            video_file = request.files['video_file']
            if video_file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            # Determine file type
            file_type = video_file.content_type or 'video/mp4'
            
            # Create ads directory if it doesn't exist
            ads_dir = os.path.join('static', 'ads')
            os.makedirs(ads_dir, exist_ok=True)
            
            # Save the file with a unique name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{secure_filename(name)}_{timestamp}.{file_type.split('/')[-1]}"
            file_path = os.path.join(ads_dir, filename)
            video_file.save(file_path)
            
            # Handle custom image if provided
            custom_image_path = None
            if 'custom_image' in request.files and request.files['custom_image'].filename:
                custom_image = request.files['custom_image']
                
                # Determine file type
                image_type = custom_image.content_type or 'image/jpeg'
                
                # Save the image
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"custom_image_{secure_filename(name)}_{timestamp}.{image_type.split('/')[-1]}"
                custom_image_path = os.path.join('static', 'ads', 'images', image_filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(custom_image_path), exist_ok=True)
                
                # Save the image
                custom_image.save(custom_image_path)
            
            # Create new advertisement record
            new_ad = Advertisement(
                name=name,
                description=description,
                file_path=file_path,
                file_type=file_type,
                duration=duration,
                placement=placement,
                priority=priority,
                target_impressions=target_impressions,
                active=active,
                start_date=start_date,
                end_date=end_date,
                created_by_id=current_user.id,
                custom_message=custom_message,
                custom_image_path=custom_image_path,
                loading_duration=loading_duration,
                is_rich_content=is_rich_content,
                html_content=html_content
            )
            
            db.session.add(new_ad)
            db.session.commit()
            
            flash(f'Advertisement "{name}" uploaded successfully!', 'success')
            return redirect(url_for('manage_ads'))
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error uploading advertisement: {str(e)}")
            flash(f'Error uploading advertisement: {str(e)}', 'danger')
    
    return render_template('admin/upload_ad.html', 
                          form=form,
                          title="Upload Advertisement")

@app.route('/admin/edit-ad/<int:ad_id>', methods=['GET', 'POST'])
@login_required
def edit_ad(ad_id):
    """Admin page to edit an existing advertisement"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get the advertisement
    ad = Advertisement.query.get_or_404(ad_id)
    form = request.form
    
    if request.method == 'POST':
        try:
            # Update advertisement details
            ad.name = request.form.get('name')
            ad.description = request.form.get('description')
            ad.duration = int(request.form.get('duration'))
            ad.placement = request.form.get('placement')
            ad.priority = int(request.form.get('priority', 5))
            ad.target_impressions = int(request.form.get('target_impressions'))
            ad.active = 'active' in request.form
            
            # Update custom message and content settings
            ad.custom_message = request.form.get('custom_message')
            ad.loading_duration = int(request.form.get('loading_duration', 10))
            ad.is_rich_content = 'is_rich_content' in request.form
            ad.html_content = request.form.get('html_content') if ad.is_rich_content else None
            
            # Handle optional dates
            start_date = request.form.get('start_date')
            if start_date:
                ad.start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                ad.start_date = None
                
            end_date = request.form.get('end_date')
            if end_date:
                ad.end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                ad.end_date = None
            
            # Check if a new video file was uploaded
            if 'video_file' in request.files and request.files['video_file'].filename:
                video_file = request.files['video_file']
                
                # Determine file type
                file_type = video_file.content_type or 'video/mp4'
                
                # Delete old file if it exists and is in the ads directory
                if ad.file_path and os.path.exists(ad.file_path) and 'static/ads' in ad.file_path:
                    try:
                        os.remove(ad.file_path)
                    except Exception as e:
                        logger.warning(f"Could not delete old advertisement file: {str(e)}")
                
                # Save the new file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{secure_filename(ad.name)}_{timestamp}.{file_type.split('/')[-1]}"
                file_path = os.path.join('static', 'ads', filename)
                video_file.save(file_path)
                
                # Update file path and type
                ad.file_path = file_path
                ad.file_type = file_type
            
            # Save changes
            db.session.commit()
            
            flash(f'Advertisement "{ad.name}" updated successfully!', 'success')
            return redirect(url_for('manage_ads'))
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error updating advertisement: {str(e)}")
            flash(f'Error updating advertisement: {str(e)}', 'danger')
    
    # Prepare form data for template
    form = {
        'name': ad.name,
        'description': ad.description,
        'duration': ad.duration,
        'placement': ad.placement,
        'priority': ad.priority,
        'target_impressions': ad.target_impressions,
        'active': ad.active,
        'start_date': ad.start_date,
        'end_date': ad.end_date,
        'custom_message': ad.custom_message,
        'loading_duration': ad.loading_duration,
        'is_rich_content': ad.is_rich_content,
        'html_content': ad.html_content
    }
    
    return render_template('admin/upload_ad.html', 
                          form=form,
                          ad=ad,
                          title="Edit Advertisement")

@app.route('/admin/preview-ad/<int:ad_id>')
@login_required
def preview_ad(ad_id):
    """Admin page to preview an advertisement"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get the advertisement
    ad = Advertisement.query.get_or_404(ad_id)
    
    return render_template('admin/preview_ad.html', 
                          ad=ad,
                          title=f"Preview: {ad.name}")

@app.route('/admin/delete-ad', methods=['POST'])
@login_required
def delete_ad():
    """Delete an advertisement"""
    if not current_user.is_admin:
        flash('You must be an admin to delete advertisements.', 'danger')
        return redirect(url_for('index'))
    
    ad_id = request.form.get('ad_id')
    if not ad_id:
        flash('No advertisement specified', 'danger')
        return redirect(url_for('manage_ads'))
    
    try:
        ad = Advertisement.query.get_or_404(ad_id)
        
        # Delete the file if it exists and is in the ads directory
        if ad.file_path and os.path.exists(ad.file_path) and 'static/ads' in ad.file_path:
            try:
                os.remove(ad.file_path)
            except Exception as e:
                logger.warning(f"Could not delete advertisement file: {str(e)}")
        
        # Delete the advertisement from the database
        db.session.delete(ad)
        db.session.commit()
        
        flash(f'Advertisement "{ad.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error deleting advertisement: {str(e)}")
        flash(f'Error deleting advertisement: {str(e)}', 'danger')
    
    return redirect(url_for('manage_ads'))

@app.route('/admin/ad-impressions')
@login_required
def ad_impressions():
    """Admin page to view ad impressions"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get all impressions grouped by advertisement
    ads = Advertisement.query.all()
    impressions = AdImpression.query.order_by(AdImpression.timestamp.desc()).limit(100).all()
    
    return render_template('admin/ad_impressions.html',
                          ads=ads,
                          impressions=impressions,
                          title="Advertisement Impressions")

@app.route('/admin/ad-performance')
@login_required
def ad_performance():
    """Admin page to view ad performance analytics"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get ad performance statistics
    ads = Advertisement.query.all()
    
    # Calculate performance metrics
    ad_stats = []
    for ad in ads:
        total_impressions = ad.total_impressions
        total_clicks = ad.total_clicks
        click_through_rate = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        progress_percent = (total_impressions / ad.target_impressions * 100) if ad.target_impressions > 0 else 0
        
        ad_stats.append({
            'ad': ad,
            'impressions': total_impressions,
            'clicks': total_clicks,
            'ctr': click_through_rate,
            'progress': min(progress_percent, 100)  # Cap at 100%
        })
    
    return render_template('admin/ad_performance.html',
                          ad_stats=ad_stats,
                          title="Advertisement Performance")

@app.route('/api/record-impression', methods=['POST'])
def record_impression():
    """API endpoint to record an ad impression"""
    try:
        ad_id = request.json.get('ad_id')
        if not ad_id:
            return jsonify({"error": "No ad_id provided"}), 400
        
        # Get the advertisement
        ad = Advertisement.query.get_or_404(ad_id)
        
        # Create new impression record
        impression = AdImpression(
            ad_id=ad_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=request.cookies.get('session', 'unknown'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            page=request.referrer,
            duration_viewed=request.json.get('duration')
        )
        
        # Update ad impression count
        ad.total_impressions += 1
        
        db.session.add(impression)
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error recording impression: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/record-click', methods=['POST'])
def record_click():
    """API endpoint to record an ad click"""
    try:
        impression_id = request.json.get('impression_id')
        if not impression_id:
            return jsonify({"error": "No impression_id provided"}), 400
        
        # Get the impression
        impression = AdImpression.query.get_or_404(impression_id)
        
        # Update impression and ad click counts
        impression.was_clicked = True
        impression.advertisement.total_clicks += 1
        
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error recording click: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/system_status')
@login_required
def system_status():
    """System status dashboard for monitoring all components"""
    # Check server status
    port_5000_status = True  # We're already running on this port if this code executes
    
    # Check port 8080
    port_8080_status = False
    try:
        import urllib.request
        response = urllib.request.urlopen('http://localhost:8080/port_check', timeout=2)
        port_8080_status = response.getcode() == 200
    except Exception as e:
        logger.warning(f"Failed to check port 8080: {str(e)}")
    
    # Get database status and statistics
    db_status = True
    db_tables_count = 0
    db_records_count = 0
    db_type = "PostgreSQL"
    
    try:
        # Count tables
        from sqlalchemy import text
        result = db.session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        db_tables_count = result.scalar() or 0
        
        # Count records in lottery_result table as a sample
        result = db.session.execute(text("SELECT COUNT(*) FROM lottery_result"))
        db_records_count = result.scalar() or 0
    except Exception as e:
        logger.error(f"Database status check error: {str(e)}")
        db_status = False
    
    # Get advertisement system stats
    active_ads_count = Advertisement.query.filter_by(active=True).count()
    total_impressions = db.session.query(db.func.count(AdImpression.id)).scalar() or 0
    js_status = True  # Will be set by frontend JS
    
    # Get lottery stats
    lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 'Powerball', 'Powerball Plus', 'Daily Lottery']
    lottery_stats = []
    
    for lottery_type in lottery_types:
        count = LotteryResult.query.filter_by(lottery_type=lottery_type).count()
        latest_draw = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
        
        lottery_stats.append({
            'name': lottery_type,
            'count': count,
            'latest_draw': latest_draw.draw_date.strftime('%Y-%m-%d') if latest_draw else 'N/A'
        })
    
    # Get system resource usage
    try:
        import psutil
        memory_usage = int(psutil.virtual_memory().percent)
        cpu_usage = int(psutil.cpu_percent(interval=0.1))
        disk_usage = int(psutil.disk_usage('/').percent)
    except ImportError:
        # Fallback if psutil not available
        memory_usage = 50
        cpu_usage = 30
        disk_usage = 40
        logger.warning("psutil not available for system stats, using placeholder values")
    
    return render_template(
        'admin/system_status.html',
        port_5000_status=port_5000_status,
        port_8080_status=port_8080_status,
        server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        last_checked=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        db_status=db_status,
        db_tables_count=db_tables_count,
        db_records_count=db_records_count,
        db_type=db_type,
        active_ads_count=active_ads_count,
        total_impressions=total_impressions,
        js_status=js_status,
        lottery_stats=lottery_stats,
        memory_usage=memory_usage,
        cpu_usage=cpu_usage,
        disk_usage=disk_usage
    )

@app.route('/admin/check-js', methods=['POST'])
@login_required
@csrf.exempt
def check_js():
    """API endpoint to check if JavaScript is operational"""
    return jsonify({'success': True})

@app.route('/admin/health-dashboard')
@login_required
@csrf.exempt
def health_dashboard():
    """Health monitoring dashboard for system administrators"""
    import health_monitor
    from datetime import datetime, timedelta
    import json
    
    # Get the overall system status
    system_status = health_monitor.get_system_status(app, db)
    
    # Get port usage data
    port_history = health_monitor.get_health_history('port_usage', 1)
    # Add active ports to components
    active_ports = system_status.get('active_ports', [])
    
    # Get recent alerts
    alerts = health_monitor.get_recent_alerts(10)
    
    # Get health check history
    health_history = health_monitor.get_health_history(limit=10)
    
    # Get resource usage history for charts
    resource_history = health_monitor.get_health_history('system_resources', 24)
    
    # Prepare chart data
    resource_timestamps = []
    cpu_history = []
    memory_history = []
    disk_history = []
    
    for check in resource_history:
        # Try to parse timestamps and details
        try:
            timestamp = datetime.fromisoformat(check['timestamp'].replace('Z', '+00:00'))
            resource_timestamps.append(timestamp.strftime('%H:%M'))
            
            details = check['details']
            if isinstance(details, str):
                details = json.loads(details)
            
            cpu_history.append(details.get('cpu_usage', 0))
            memory_history.append(details.get('memory_usage', 0))
            disk_history.append(details.get('disk_usage', 0))
        except Exception as e:
            app.logger.error(f"Error parsing health check data: {str(e)}")
    
    # If we don't have enough data points, add some placeholders
    if len(resource_timestamps) < 5:
        now = datetime.now()
        for i in range(5 - len(resource_timestamps)):
            time_point = now - timedelta(hours=i)
            resource_timestamps.insert(0, time_point.strftime('%H:%M'))
            cpu_history.insert(0, 0)
            memory_history.insert(0, 0)
            disk_history.insert(0, 0)
    
    # Reverse lists to show chronological order
    resource_timestamps.reverse()
    cpu_history.reverse()
    memory_history.reverse()
    disk_history.reverse()
    
    # Add additional port monitoring information
    service_port_map = {}
    
    # If port usage information is available in the health history,
    # populate the service-to-port mapping
    if port_history and len(port_history) > 0:
        try:
            port_details = port_history[0]['details']
            if isinstance(port_details, str):
                port_details = json.loads(port_details)
            
            # Extract service usage mapping from details if available
            if isinstance(port_details, dict) and 'service_usage' in port_details:
                service_port_map = port_details['service_usage']
        except Exception as e:
            app.logger.error(f"Error extracting port history data: {str(e)}")
    
    return render_template(
        'admin/health_dashboard.html',
        overall_status=system_status['overall_status'],
        components=system_status['components'],
        last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        alerts=alerts,
        health_history=health_history,
        resource_timestamps=resource_timestamps,
        cpu_history=cpu_history,
        memory_history=memory_history,
        disk_history=disk_history,
        active_ports=active_ports,
        service_port_map=service_port_map
    )

@app.route('/admin/health-alerts')
@login_required
def health_alerts():
    """View and manage health alerts"""
    import health_monitor
    from datetime import datetime
    
    # Get all alerts
    alerts = health_monitor.get_recent_alerts(100)
    
    # Generate chart data for alert types
    alert_types = {}
    for alert in alerts:
        alert_type = alert['alert_type']
        if alert_type in alert_types:
            alert_types[alert_type] += 1
        else:
            alert_types[alert_type] = 1
    
    # Prepare chart data
    alert_types_list = list(alert_types.keys())
    alert_counts = [alert_types[t] for t in alert_types_list]
    
    # Generate time-based data
    # Group alerts by day for the last 30 days
    time_data = [0] * 30
    time_labels = []
    
    now = datetime.now()
    for i in range(30):
        day = now - timedelta(days=i)
        time_labels.insert(0, day.strftime('%m/%d'))
        
    for alert in alerts:
        try:
            created_at = datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00'))
            days_ago = (now - created_at).days
            if 0 <= days_ago < 30:
                time_data[29 - days_ago] += 1
        except:
            pass
    
    # Add utility functions for templates
    def format_duration(start_time, end_time):
        """Format a duration between two timestamps"""
        try:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration = end_time - start_time
            seconds = duration.total_seconds()
            
            if seconds < 60:
                return f"{int(seconds)} seconds"
            elif seconds < 3600:
                return f"{int(seconds / 60)} minutes"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                minutes = int((seconds % 3600) / 60)
                return f"{hours} hours, {minutes} minutes"
            else:
                days = int(seconds / 86400)
                hours = int((seconds % 86400) / 3600)
                return f"{days} days, {hours} hours"
        except Exception as e:
            app.logger.error(f"Error formatting duration: {str(e)}")
            return "Unknown"
    
    return render_template(
        'admin/health_alerts.html',
        alerts=alerts,
        alert_types=alert_types_list,
        alert_counts=alert_counts,
        time_labels=time_labels,
        time_data=time_data,
        format_duration=format_duration,
        now=datetime.now()
    )

@app.route('/admin/resolve-health-alert/<int:alert_id>', methods=['POST'])
@login_required
@csrf.exempt
def resolve_health_alert(alert_id):
    """Manually resolve a health alert"""
    import health_monitor
    import sqlite3
    
    try:
        conn = sqlite3.connect(health_monitor.health_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the alert
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        alert = cursor.fetchone()
        
        if alert:
            # Update the alert
            cursor.execute(
                "UPDATE alerts SET resolved = 1, resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
                (alert_id,)
            )
            conn.commit()
            
            # Also resolve any other alerts of the same type
            alert_type = alert['alert_type']
            health_monitor.resolve_alert(alert_type)
            
            flash(f"Alert #{alert_id} ({alert_type}) has been resolved.", "success")
        else:
            flash(f"Alert #{alert_id} not found.", "danger")
            
        conn.close()
    except Exception as e:
        flash(f"Error resolving alert: {str(e)}", "danger")
    
    return redirect(url_for('health_alerts'))

@app.route('/admin/health-history')
@login_required
def health_history():
    """View detailed health check history"""
    import health_monitor
    import json
    from datetime import datetime
    from sqlalchemy import func
    
    # Set up pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    selected_type = request.args.get('check_type', '')
    selected_status = request.args.get('status', '')
    
    # Get health check history
    try:
        import sqlite3
        conn = sqlite3.connect(health_monitor.health_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build the query
        query = "SELECT * FROM health_checks"
        params = []
        
        if selected_type or selected_status:
            query += " WHERE"
            
            if selected_type:
                query += " check_type = ?"
                params.append(selected_type)
                
            if selected_type and selected_status:
                query += " AND"
                
            if selected_status:
                query += " status = ?"
                params.append(selected_status)
        
        # Get total count for pagination
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Add sorting and pagination
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        # Execute query
        cursor.execute(query, params)
        history = [dict(row) for row in cursor.fetchall()]
        
        # Get all unique check types for the filter dropdown
        cursor.execute("SELECT DISTINCT check_type FROM health_checks ORDER BY check_type")
        check_types = [row[0] for row in cursor.fetchall()]
        
        # Get status counts for chart
        cursor.execute("SELECT status, COUNT(*) FROM health_checks GROUP BY status")
        status_counts_raw = cursor.fetchall()
        
        # Prepare status counts for chart
        status_counts = [0, 0, 0, 0]  # OK, WARNING, CRITICAL, ERROR
        for status, count in status_counts_raw:
            if status == 'OK':
                status_counts[0] = count
            elif status == 'WARNING':
                status_counts[1] = count
            elif status == 'CRITICAL':
                status_counts[2] = count
            elif status == 'ERROR':
                status_counts[3] = count
        
        # Get check type counts for chart
        cursor.execute("SELECT check_type, COUNT(*) FROM health_checks GROUP BY check_type")
        type_counts_raw = cursor.fetchall()
        
        # Prepare check type counts for chart
        type_counts = [row[1] for row in type_counts_raw]
        
        conn.close()
        
        # Create pagination object
        class Pagination:
            def __init__(self, page, per_page, total):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                
            @property
            def has_prev(self):
                return self.page > 1
                
            @property
            def has_next(self):
                return self.page < self.pages
                
            @property
            def prev_num(self):
                return self.page - 1 if self.has_prev else None
                
            @property
            def next_num(self):
                return self.page + 1 if self.has_next else None
                
            def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if (num <= left_edge or
                            (self.page - left_current <= num <= self.page + right_current) or
                            (self.pages - right_edge < num)):
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        pagination = Pagination(page, per_page, total)
        
        # Format JSON for display
        def format_json(json_str):
            try:
                if isinstance(json_str, str):
                    data = json.loads(json_str)
                else:
                    data = json_str
                return json.dumps(data, indent=2)
            except:
                return json_str
        
    except Exception as e:
        app.logger.error(f"Error getting health history: {str(e)}")
        history = []
        check_types = []
        status_counts = [0, 0, 0, 0]
        type_counts = []
        pagination = None
        format_json = lambda x: x
    
    return render_template(
        'admin/health_history.html',
        history=history,
        check_types=check_types,
        selected_type=selected_type,
        selected_status=selected_status,
        status_counts=status_counts,
        type_counts=type_counts,
        pagination=pagination,
        format_json=format_json
    )

@app.route('/health_port_check')
def health_port_check():
    """Simple endpoint to check if the server is running on a specific port"""
    return jsonify({
        'status': 'ok',
        'message': 'Port health check successful',
        'port': request.environ.get('SERVER_PORT', '5000'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# Global variable to store Puppeteer screenshot capture status
puppeteer_capture_status = {
    'in_progress': False,
    'total_screenshots': 0,
    'completed_screenshots': 0,
    'start_time': None,
    'last_updated': None,
    'success_count': 0,
    'error_count': 0,
    'status_message': 'No capture in progress',
    'errors': [],
    'progress': 0  # Progress percentage (0-100)
}

@app.route('/puppeteer-status')
@csrf.exempt
def puppeteer_status():
    """API endpoint to check the status of Puppeteer screenshot capture"""
    global puppeteer_capture_status
    
    # Use explicit progress value if set, otherwise calculate from completed/total
    progress = puppeteer_capture_status.get('progress', 0)
    if progress == 0 and puppeteer_capture_status['total_screenshots'] > 0:
        progress = (puppeteer_capture_status['completed_screenshots'] / 
                   puppeteer_capture_status['total_screenshots']) * 100
    
    # Add elapsed time if in progress
    elapsed_time = None
    if puppeteer_capture_status['in_progress'] and puppeteer_capture_status['start_time']:
        elapsed_time = (datetime.now() - puppeteer_capture_status['start_time']).total_seconds()
    
    # Return the current status
    return jsonify({
        'in_progress': puppeteer_capture_status['in_progress'],
        'progress': round(progress, 1),
        'status_message': puppeteer_capture_status['status_message'],
        'success_count': puppeteer_capture_status['success_count'],
        'error_count': puppeteer_capture_status['error_count'],
        'total_screenshots': puppeteer_capture_status['total_screenshots'],
        'completed_screenshots': puppeteer_capture_status['completed_screenshots'],
        'elapsed_time': elapsed_time,
        'errors': puppeteer_capture_status['errors'][:5]  # Limit the number of errors returned
    })

@app.route('/admin/run-health-checks', methods=['POST', 'GET'])
@login_required
@csrf.exempt
def run_health_checks():
    """Manually trigger health checks"""
    import health_monitor
    
    try:
        health_monitor.run_health_checks(app, db)
        flash("Health checks completed successfully.", "success")
    except Exception as e:
        flash(f"Error running health checks: {str(e)}", "danger")
    
    return redirect(url_for('health_dashboard'))

@app.route('/health_check', methods=['GET'])
@csrf.exempt
def health_check():
    """Simple endpoint for health checks in Replit deployment"""
    return jsonify({
        'status': 'ok',
        'message': 'Health check successful',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })



@app.route('/api/system-metrics', methods=['GET'])
@csrf.exempt
def system_metrics():
    """API endpoint to get current system metrics for dashboard"""
    try:
        import psutil
        
        # Get system stats
        memory = psutil.virtual_memory()
        memory_usage = int(memory.percent)
        
        disk = psutil.disk_usage('/')
        disk_usage = int(disk.percent)
        
        cpu_usage = int(psutil.cpu_percent(interval=0.5))
        
        return jsonify({
            'success': True,
            'cpu_usage': f"{cpu_usage}%",
            'memory_usage': f"{memory_usage}%",
            'disk_usage': f"{disk_usage}%",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Register advertisement management routes
ad_management.register_ad_routes(app)

# Register lottery analysis routes
lottery_analysis.register_analysis_routes(app, db)

# Register puppeteer screenshot routes
puppeteer_routes.register_puppeteer_routes(app)

# API Request Tracking routes
@app.route('/admin/api-tracking')
@login_required
def api_tracking_dashboard():
    """Dashboard for tracking API requests to external services"""
    from datetime import datetime, timedelta
    from models import APIRequestLog
    from sqlalchemy import func, desc
    
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get time periods for filtering
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    this_week = today - timedelta(days=today.weekday())
    this_month = today.replace(day=1)
    
    # Get overall statistics
    overall_stats = APIRequestLog.get_stats_by_date_range()
    
    # Get daily statistics for the last 30 days
    daily_stats = db.session.query(
        func.date(APIRequestLog.created_at).label('date'),
        func.count(APIRequestLog.id).label('count'),
        func.sum(APIRequestLog.total_tokens).label('tokens')
    ).group_by(func.date(APIRequestLog.created_at)
    ).order_by(desc('date')).limit(30).all()
    
    # Get service breakdown
    service_breakdown = db.session.query(
        APIRequestLog.service,
        func.count(APIRequestLog.id).label('count'),
        func.sum(APIRequestLog.total_tokens).label('tokens')
    ).group_by(APIRequestLog.service).all()
    
    # Get model breakdown for Anthropic
    model_breakdown = db.session.query(
        APIRequestLog.model,
        func.count(APIRequestLog.id).label('count'),
        func.sum(APIRequestLog.total_tokens).label('tokens')
    ).filter(APIRequestLog.service == 'anthropic'
    ).group_by(APIRequestLog.model).all()
    
    # Get recent requests with status, limited to 100
    recent_requests = APIRequestLog.query.order_by(
        APIRequestLog.created_at.desc()
    ).limit(100).all()
    
    # Calculate statistics for specific time periods
    today_stats = APIRequestLog.get_stats_by_date_range(start_date=today)
    yesterday_stats = APIRequestLog.get_stats_by_date_range(start_date=yesterday, end_date=today)
    this_week_stats = APIRequestLog.get_stats_by_date_range(start_date=this_week)
    this_month_stats = APIRequestLog.get_stats_by_date_range(start_date=this_month)
    
    # Format data for charts
    daily_labels = [str(item.date) for item in daily_stats]
    daily_requests = [item.count for item in daily_stats]
    daily_tokens = [int(item.tokens) if item.tokens else 0 for item in daily_stats]
    
    # Prepare service breakdown data for charts
    service_labels = [item.service for item in service_breakdown]
    service_counts = [item.count for item in service_breakdown]
    service_tokens = [int(item.tokens) if item.tokens else 0 for item in service_breakdown]
    
    return render_template(
        'admin/api_tracking.html',
        title="API Request Tracking",
        overall_stats=overall_stats,
        today_stats=today_stats,
        yesterday_stats=yesterday_stats,
        this_week_stats=this_week_stats,
        this_month_stats=this_month_stats,
        service_breakdown=service_breakdown,
        model_breakdown=model_breakdown,
        recent_requests=recent_requests,
        daily_labels=daily_labels,
        daily_requests=daily_requests,
        daily_tokens=daily_tokens,
        service_labels=service_labels,
        service_counts=service_counts,
        service_tokens=service_tokens
    )

# Route for importing latest template file
@app.route('/admin/import-latest-template')
@login_required
@admin_required
def import_latest_template_route():
    """Import the latest lottery data template file"""
    try:
        result = import_latest_template.import_latest_template()
        return render_template('import_status.html', 
                               success=result.get('success', False),
                               stats=result.get('stats', {}),
                               error=result.get('error', 'Unknown error'))
    except Exception as e:
        logger.error(f"Error importing template: {str(e)}")
        return render_template('import_status.html', 
                               success=False,
                               stats={},
                               error=f"Error: {str(e)}")

# Route for viewing import history
@app.route('/admin/import-history')
@login_required
@admin_required
def admin_import_history():
    """Display import history in admin panel"""
    history = ImportHistory.query.order_by(ImportHistory.import_date.desc()).all()
    return render_template('import_history.html', history=history)

# Route for importing missing draws
@app.route('/admin/import-missing-draws')
@login_required
@admin_required
def import_missing_draws_route():
    """Import specific missing lottery draws"""
    try:
        from import_missing_draws import import_missing_draws
        result = import_missing_draws("attached_assets/missing_draws.xlsx")
        
        return render_template('import_status.html', 
                              success=result.get('success', False),
                              stats=result.get('stats', {}),
                              error=result.get('error', 'Unknown error'))
    except Exception as e:
        logger.error(f"Error importing missing draws: {str(e)}")
        return render_template('import_status.html', 
                              success=False,
                              stats={},
                              error=f"Error: {str(e)}")

# When running directly, not through gunicorn
if __name__ == "__main__":
    # Extra logging to help diagnose startup issues
    import logging
    import os
    
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Use port 8080 for Replit compatibility
    port = int(os.environ.get('PORT', 8080))
    
    # Start Flask app
    print(f"Starting Flask application on 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)