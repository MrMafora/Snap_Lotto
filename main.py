"""
Main application entry point with Flask application defined for deployment.

This file is imported by gunicorn using the 'main:app' notation.
"""
import logging
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, send_from_directory, session, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

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
    latest_results = data_aggregator.get_latest_results()
    return render_template('index.html', 
                           latest_results=latest_results,
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
    results = data_aggregator.get_all_results_by_lottery_type(lottery_type)
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
    
    if data_type == 'numbers_frequency':
        # Placeholder data
        return jsonify({
            'labels': [str(i) for i in range(1, 50)],
            'datasets': [{
                'data': [7, 12, 9, 15, 8, 11, 13, 6, 10, 14, 9, 7, 16, 8, 11, 9, 13, 7, 10, 12, 
                         8, 14, 9, 7, 12, 8, 15, 10, 6, 11, 9, 13, 8, 7, 14, 9, 12, 10, 8, 11, 
                         7, 13, 9, 15, 8, 6, 10, 12, 14]
            }]
        })
    
    elif data_type == 'winners_by_division':
        # Placeholder data
        return jsonify({
            'labels': ['Division 1', 'Division 2', 'Division 3', 'Division 4', 'Division 5'],
            'datasets': [{
                'data': [5, 27, 142, 689, 1245]
            }]
        })
    
    return jsonify({'error': 'Invalid data type'}), 400

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