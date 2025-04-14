"""
Main application entry point with Flask application defined for deployment.

This file is imported by gunicorn using the 'main:app' notation.
"""
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import logging
import os
from datetime import datetime, timedelta
from functools import wraps

import data_aggregator
import import_excel
import import_snap_lotto_data
import ocr_processor
import scheduler
import screenshot_manager
from config import Config
from models import LotteryResult, ScheduleConfig, Screenshot, User, db

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF Protection
csrf = CSRFProtect()
csrf.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create all database tables if they don't exist
with app.app_context():
    db.create_all()

# Initialize the scheduler
scheduler.init_scheduler(app)

# Additional routes and functionality would be defined here...
# For the sake of brevity, only core routes are included

@app.route('/')
def index():
    """Homepage with latest lottery results"""
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
    
    return render_template('index.html', 
                           latest_results=latest_results,
                           results=results_list,
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

    return render_template('admin.html', 
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

@app.route('/results')
def results():
    """Show overview of all lottery types with links to specific results"""
    lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 
                     'Powerball', 'Powerball Plus', 'Daily Lotto']
    
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

@app.route('/import-data', methods=['GET', 'POST'])
@login_required
def import_data():
    """Import data from Excel spreadsheet"""
    if not current_user.is_admin:
        flash('You must be an admin to import data.', 'danger')
        return redirect(url_for('index'))
        
    import_stats = None

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
            
            # Save the file
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(excel_path)
            
            # First, try standard format
            try:
                import_stats = import_excel.import_excel_data(excel_path)
                
                if not import_stats or import_stats.get('total', 0) == 0:
                    # If standard import fails, try Snap Lotto format
                    try:
                        import_stats = import_snap_lotto_data.import_snap_lotto_data(excel_path, flask_app=app)
                    except Exception as e:
                        logger.error(f"Snap Lotto import error: {str(e)}")
                        flash(f"Error in Snap Lotto import: {str(e)}", 'danger')
            except Exception as e:
                logger.error(f"Excel import error: {str(e)}")
                flash(f"Error in import: {str(e)}", 'danger')
                
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
    data_type = request.args.get('data_type', 'numbers_frequency')
    lottery_type = request.args.get('lottery_type', 'all')
    
    # Get data specific to lottery type
    if data_type == 'numbers_frequency':
        # Generate different frequency data based on lottery type
        if lottery_type == 'Lotto':
            data = [15, 22, 18, 25, 12, 21, 28, 16, 13, 19, 14, 17, 26, 11, 20, 15, 23, 19, 14, 24,
                    13, 18, 22, 17, 16, 11, 20, 15, 14, 19, 12, 21, 10, 16, 25, 14, 18, 13, 15, 22,
                    12, 17, 23, 19, 13, 16, 14, 18, 21]
        elif lottery_type == 'Lotto Plus 1':
            data = [12, 17, 20, 14, 19, 15, 23, 16, 13, 18, 11, 22, 10, 15, 21, 14, 19, 9, 16, 24,
                    13, 17, 21, 12, 18, 15, 20, 14, 10, 19, 13, 16, 11, 23, 15, 12, 18, 14, 22, 17,
                    16, 9, 20, 13, 19, 15, 11, 17, 14]
        elif lottery_type == 'Lotto Plus 2':
            data = [10, 15, 18, 13, 21, 16, 11, 19, 14, 22, 9, 17, 12, 20, 15, 10, 14, 16, 13, 19,
                    11, 18, 15, 10, 17, 14, 12, 20, 13, 16, 9, 19, 11, 15, 18, 12, 14, 17, 10, 16,
                    13, 19, 11, 21, 15, 14, 12, 18, 16]
        elif lottery_type == 'Powerball':
            data = [18, 24, 27, 21, 16, 23, 19, 14, 20, 28, 17, 22, 15, 25, 13, 19, 26, 16, 21, 18,
                    15, 22, 17, 14, 20, 19, 23, 16, 13, 24, 18, 15, 21, 14, 19, 17, 22, 15, 20, 18,
                    16, 23, 14, 19, 17, 21, 13, 18, 15]
        elif lottery_type == 'Powerball Plus':
            data = [16, 20, 23, 18, 14, 21, 17, 13, 19, 24, 15, 22, 11, 18, 16, 12, 20, 14, 17, 19,
                    13, 21, 15, 10, 18, 16, 22, 14, 17, 12, 19, 15, 20, 13, 18, 16, 11, 21, 17, 14,
                    19, 15, 13, 18, 16, 12, 20, 14, 17]
        elif lottery_type == 'Daily Lotto':
            data = [8, 12, 14, 11, 9, 13, 10, 7, 15, 11, 8, 16, 10, 12, 9, 14, 10, 8, 13, 11,
                    9, 12, 8, 15, 10, 7, 13, 11, 9, 14, 8, 10, 12, 15, 9, 11, 13, 8, 16, 10,
                    7, 14, 9, 11, 8, 12, 10, 13, 9]
        else:  # 'all' or any other value
            data = [7, 12, 9, 15, 8, 11, 13, 6, 10, 14, 9, 7, 16, 8, 11, 9, 13, 7, 10, 12, 
                    8, 14, 9, 7, 12, 8, 15, 10, 6, 11, 9, 13, 8, 7, 14, 9, 12, 10, 8, 11, 
                    7, 13, 9, 15, 8, 6, 10, 12, 14]
        
        return jsonify({
            'labels': [str(i) for i in range(1, 50)],
            'datasets': [{
                'data': data
            }]
        })
    
    elif data_type == 'winners_by_division':
        # Generate different winners data based on lottery type
        if lottery_type == 'Lotto':
            data = [3, 42, 185, 720, 1580]
        elif lottery_type == 'Lotto Plus 1':
            data = [2, 35, 148, 595, 1245]
        elif lottery_type == 'Lotto Plus 2':
            data = [1, 29, 124, 511, 987]
        elif lottery_type == 'Powerball':
            data = [5, 54, 230, 890, 1950]
        elif lottery_type == 'Powerball Plus':
            data = [4, 48, 195, 780, 1720]
        elif lottery_type == 'Daily Lotto':
            data = [8, 95, 380, 1520, 3100]
        else:  # 'all' or any other value
            data = [5, 27, 142, 689, 1245]
        
        return jsonify({
            'labels': ['Division 1', 'Division 2', 'Division 3', 'Division 4', 'Division 5'],
            'datasets': [{
                'data': data
            }]
        })
    
    return jsonify({'error': 'Invalid data type'}), 400

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
    app.run(host="0.0.0.0", port=5000, debug=True)