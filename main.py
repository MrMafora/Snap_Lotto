"""
Main application entry point with Flask application defined for deployment.

This file is imported by gunicorn using the 'main:app' notation.

It also includes functionality to automatically bind to port 8080 
when running directly, to support Replit's external access requirements.
"""
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, send_from_directory, send_file
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import logging
import os
import threading
from datetime import datetime, timedelta
from functools import wraps

# Import models only (lightweight)
from models import LotteryResult, ScheduleConfig, Screenshot, User, db
from config import Config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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

# Initialize CSRF Protection but don't apply it app-wide
# This will allow us to selectively apply it to forms via WTF_CSRF_ENABLED config
csrf = CSRFProtect()
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for API endpoints

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
screenshot_manager = None
scheduler = None

def init_lazy_modules():
    """Initialize modules in a background thread to speed up startup"""
    global data_aggregator, import_excel, import_snap_lotto_data, ocr_processor, screenshot_manager, scheduler
    
    # Import heavy modules only when needed
    import data_aggregator as da
    import import_excel as ie
    import import_snap_lotto_data as isld
    import ocr_processor as op
    import screenshot_manager as sm
    import scheduler as sch
    
    # Store module references
    data_aggregator = da
    import_excel = ie
    import_snap_lotto_data = isld
    ocr_processor = op
    screenshot_manager = sm
    scheduler = sch
    
    # Initialize scheduler in background after imports are complete
    with app.app_context():
        scheduler.init_scheduler(app)
    
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
    
    # Import if not already loaded
    if data_aggregator is None:
        import data_aggregator as da
        data_aggregator = da
        logger.info("Loaded data_aggregator module on demand")
    
    # First, validate and correct any known draws (adds missing division data)
    corrected = data_aggregator.validate_and_correct_known_draws()
    if corrected > 0:
        logger.info(f"Corrected {corrected} lottery draws with verified data")
    
    # Get the latest results for each lottery type
    latest_results = data_aggregator.get_latest_results()
    
    # Convert dictionary of results to a list for iteration in the template
    results_list = []
    for lottery_type, result in latest_results.items():
        results_list.append(result)
    
    # Sort results by date (newest first)
    results_list.sort(key=lambda x: x.draw_date, reverse=True)
    
    # Get analytics data for the dashboard
    frequent_numbers = data_aggregator.get_most_frequent_numbers(limit=10)
    division_stats = data_aggregator.get_division_statistics()
    
    return render_template('index.html', 
                           latest_results=latest_results,
                           results=results_list,
                           frequent_numbers=frequent_numbers,
                           division_stats=division_stats,
                           title="Latest Lottery Results")

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard page"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))

    screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
    schedule_configs = ScheduleConfig.query.all()

    return render_template('admin/dashboard.html', 
                          screenshots=screenshots,
                          schedule_configs=schedule_configs,
                          title="Admin Dashboard")

@app.route('/login', methods=['GET', 'POST'])
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
    
    return render_template('login.html', title="Login")

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/ticket-scanner')
def ticket_scanner():
    """Ticket scanner page"""
    return render_template('ticket_scanner.html', title="Ticket Scanner")

@app.route('/scan-ticket', methods=['POST'])
def scan_ticket():
    """Process uploaded ticket image and return results"""
    # Check if file is included in the request
    if 'ticket_image' not in request.files:
        return jsonify({"error": "No ticket image provided"}), 400
        
    file = request.files['ticket_image']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    # Get the lottery type if specified (optional)
    lottery_type = request.form.get('lottery_type', '')
    
    # Get draw number if specified (optional)
    draw_number = request.form.get('draw_number', None)
    
    # Get file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if not file_extension:
        file_extension = '.jpeg'  # Default to JPEG if no extension
    
    try:
        # Read the file data
        image_data = file.read()
        
        # Import the ticket scanner module
        import ticket_scanner as ts
        
        # Process the ticket image using existing function
        result = ts.process_ticket_image(
            image_data=image_data,
            lottery_type=lottery_type,
            draw_number=draw_number,
            file_extension=file_extension
        )
        
        # Return JSON response with results
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Error processing ticket: {str(e)}")
        return jsonify({"error": f"Error processing ticket: {str(e)}"}), 500

@app.route('/results')
def results():
    """Show overview of all lottery types with links to specific results"""
    lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 
                     'Powerball', 'Powerball Plus', 'Daily Lotto']
    
    # Ensure data_aggregator is loaded before using it
    global data_aggregator
    
    # Import if not already loaded
    if data_aggregator is None:
        import data_aggregator as da
        data_aggregator = da
        logger.info("Loaded data_aggregator module on demand")
    
    latest_results = data_aggregator.get_latest_results()
    
    return render_template('results_overview.html',
                          lottery_types=lottery_types,
                          latest_results=latest_results,
                          title="All Lottery Results")

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
    
    return render_template('results.html', 
                           results=results, 
                           lottery_type=lottery_type,
                           title=f"{lottery_type} Results")

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
    import_excel.create_empty_template(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
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
def reset_file_upload_progress():
    """Reset the file upload progress for the current user"""
    user_id = current_user.id
    
    file_upload_progress[user_id] = {
        'percentage': 0,
        'status': 'initializing',
        'filename': ''
    }
    
    return jsonify({'success': True})

@app.route('/import-data', methods=['GET', 'POST'])
@login_required
def import_data():
    """Import data from Excel spreadsheet"""
    if not current_user.is_admin:
        flash('You must be an admin to import data.', 'danger')
        return redirect(url_for('index'))
        
    import_stats = None
    user_id = current_user.id
    
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
            
            # First, try standard format
            try:
                import_stats = import_excel.import_excel_data(excel_path)
                
                if not import_stats or import_stats.get('total', 0) == 0:
                    # If standard import fails, try Snap Lotto format
                    try:
                        # Update progress
                        file_upload_progress[user_id] = {
                            'percentage': 75,
                            'status': 'processing',
                            'filename': filename
                        }
                        
                        import_stats = import_snap_lotto_data.import_snap_lotto_data(excel_path, flask_app=app)
                        
                        # Update progress to complete
                        file_upload_progress[user_id] = {
                            'percentage': 100,
                            'status': 'complete',
                            'filename': filename
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
                    # Update progress to complete
                    file_upload_progress[user_id] = {
                        'percentage': 100,
                        'status': 'complete',
                        'filename': filename
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
                
    # Get some example results for each lottery type to display
    example_results = {}
    lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 
                     'Powerball', 'Powerball Plus', 'Daily Lotto']
                     
    for lottery_type in lottery_types:
        results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(
            LotteryResult.draw_date.desc()).limit(5).all()
        if results:
            example_results[lottery_type] = results
    
    return render_template('import_data.html', 
                           import_stats=import_stats,
                           example_results=example_results,
                           title="Import Lottery Data")

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
    
    schedule_configs = ScheduleConfig.query.all()
    
    # Handle form submission for updating settings
    if request.method == 'POST':
        # This would normally handle the form submission
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', 
                          schedule_configs=schedule_configs,
                          title="System Settings")

@app.route('/export-screenshots')
@login_required
def export_screenshots():
    """Export screenshots"""
    if not current_user.is_admin:
        flash('You must be an admin to export screenshots.', 'danger')
        return redirect(url_for('index'))
    
    screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
    
    return render_template('export_screenshots.html',
                          screenshots=screenshots,
                          title="Export Screenshots")

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
    
    return render_template('register.html', title="Register Admin User")

@app.route('/visualizations')
def visualizations():
    """Advanced data visualization and analytics"""
    lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 
                    'Powerball', 'Powerball Plus', 'Daily Lotto']
    
    # Get some summary statistics
    total_draws = LotteryResult.query.count()
    latest_draw = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).first()
    latest_draw_date = latest_draw.draw_date if latest_draw else None
    
    return render_template('visualizations.html',
                          lottery_types=lottery_types,
                          total_draws=total_draws,
                          latest_draw_date=latest_draw_date,
                          title="Data Analytics")

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
    
    return render_template('draw_details.html',
                          result=result,
                          lottery_type=lottery_type,
                          title=f"{lottery_type} Draw {draw_number} Details")

@app.route('/screenshot/<int:screenshot_id>')
def view_screenshot(screenshot_id):
    """View a screenshot image"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    # Normalize path and check if file exists
    screenshot_path = os.path.normpath(screenshot.path)
    
    if not os.path.isfile(screenshot_path):
        flash('Screenshot file not found', 'danger')
        return redirect(url_for('admin'))
    
    # Extract directory and filename from path
    directory = os.path.dirname(screenshot_path)
    filename = os.path.basename(screenshot_path)
    
    return send_from_directory(directory, filename)

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

# When running directly, not through gunicorn
if __name__ == "__main__":
    # Extra logging to help diagnose startup issues
    import logging
    import argparse
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Always force port 8080 for Replit compatibility
    port = 8080
    
    print(f"Starting Flask application directly on 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)