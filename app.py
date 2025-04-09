"""
Application configuration and setup.
"""
import os
import json
import logging
import shutil
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, BooleanField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import db, Screenshot, LotteryResult, ScheduleConfig, User
from data_aggregator import aggregate_data, validate_and_correct_known_draws
from scheduler import run_lottery_task
from ticket_scanner import process_ticket_image
from import_snap_lotto_data import import_snap_lotto_data

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "lottery-scraper-default-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///lottery_data.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'info'

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create all database tables
with app.app_context():
    db.create_all()

# Import components after database is initialized
from scheduler import init_scheduler, schedule_task, remove_task
from screenshot_manager import capture_screenshot
from data_aggregator import aggregate_data, validate_and_correct_known_draws

# Initialize scheduler
scheduler = init_scheduler(app)

# Schedule any active tasks
with app.app_context():
    # Run validation to correct any known draw issues
    corrected_count = validate_and_correct_known_draws()
    if corrected_count > 0:
        logger.info(f"Corrected {corrected_count} draws with known good data")
    
    # Set up initial schedules if none exist
    if ScheduleConfig.query.count() == 0:
        # Add history pages (for drawing numbers/history)
        default_urls = [
            {'url': 'https://www.nationallottery.co.za/lotto-history', 'lottery_type': 'Lotto'},
            {'url': 'https://www.nationallottery.co.za/lotto-plus-1-history', 'lottery_type': 'Lotto Plus 1'},
            {'url': 'https://www.nationallottery.co.za/lotto-plus-2-history', 'lottery_type': 'Lotto Plus 2'},
            {'url': 'https://www.nationallottery.co.za/powerball-history', 'lottery_type': 'Powerball'},
            {'url': 'https://www.nationallottery.co.za/powerball-plus-history', 'lottery_type': 'Powerball Plus'},
            {'url': 'https://www.nationallottery.co.za/daily-lotto-history', 'lottery_type': 'Daily Lotto'}
        ]
        
        # Add results pages (for divisions, winners, and winnings)
        results_urls = [
            {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto Results'},
            {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1 Results'},
            {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2 Results'},
            {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball Results'},
            {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus Results'},
            {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto Results'}
        ]
        
        # Combine all URLs
        all_urls = default_urls + results_urls
        
        for i, config in enumerate(all_urls):
            # Stagger the scheduled times to avoid overwhelming the system
            hour = 1  # Run at 1 AM
            minute = i * 5  # 5 minutes apart
            
            schedule = ScheduleConfig(
                url=config['url'],
                lottery_type=config['lottery_type'],
                frequency='daily',
                hour=hour,
                minute=minute,
                active=True
            )
            db.session.add(schedule)
        
        db.session.commit()
        logger.info("Added default lottery schedule configurations")
    
    # Schedule active tasks
    for config in ScheduleConfig.query.filter_by(active=True).all():
        schedule_task(scheduler, config)

# Define authentication forms
class LoginForm(FlaskForm):
    """Login form for admin authentication"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    """Registration form for admin accounts"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')
    
    # Custom validators
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose another one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please use another one or reset your password.')

# Admin access decorator
def admin_required(f):
    """Decorator for routes that require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You don't have permission to access this page. Please log in as an administrator.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login route"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('admin_dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Admin logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    """Admin registration route (only accessible by existing admins)"""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('register.html', form=form)

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard showing links to admin-only features"""
    return render_template('admin/dashboard.html')

# Routes
# Export route functions for use by main.py
@app.route('/')
def index():
    """Home page showing lottery results and ticket scanning feature"""
    latest_results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).limit(10).all()
    return render_template('index.html', results=latest_results)

@app.route('/results')
def results():
    """Page showing all lottery results"""
    # Run validation to ensure known correct data is used
    try:
        corrected = validate_and_correct_known_draws()
        if corrected > 0:
            logger.info(f"Corrected {corrected} draws with known correct data")
    except Exception as e:
        logger.error(f"Error validating known draws: {str(e)}")
    
    lottery_type = request.args.get('lottery_type', None)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Import the normalization functions
    from data_aggregator import normalize_lottery_type
    
    # Create a query that avoids showing duplicate entries
    query = db.session.query(LotteryResult)
    
    # Filter by lottery type if specified
    if lottery_type:
        # Remove "Results" suffix if present for consistent filtering
        normalized_type = normalize_lottery_type(lottery_type)
        query = query.filter(
            # Match either exact type or the same type with "Results" suffix
            db.or_(
                LotteryResult.lottery_type == normalized_type,
                LotteryResult.lottery_type == f"{normalized_type} Results"
            )
        )
    
    # Get all results to remove duplicates properly
    all_results = query.order_by(LotteryResult.draw_date.desc()).all()
    
    # Process results to remove duplicates
    unique_results = []
    processed_draws = set()
    
    for result in all_results:
        # Normalize draw number to handle both "2530" and "LOTTO DRAW 2530" formats
        from data_aggregator import normalize_draw_number
        draw_key = normalize_draw_number(result.draw_number)
        normalized_type = normalize_lottery_type(result.lottery_type)
        
        # Create a unique key for this draw
        unique_key = f"{normalized_type}_{draw_key}"
        
        # Skip if we've already processed this draw
        if unique_key in processed_draws:
            continue
        
        # Mark this draw as processed
        processed_draws.add(unique_key)
        
        # Add to unique results
        unique_results.append(result)
    
    # Implement manual pagination since we're doing in-memory filtering
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paged_results = unique_results[start_idx:end_idx]
    
    # Create a pagination class similar to Flask-SQLAlchemy's but with added iter_pages method
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page  # Ceiling division
            self.has_next = page < self.pages
            self.has_prev = page > 1
            
        @property
        def prev_num(self):
            return self.page - 1 if self.has_prev else None
            
        @property
        def next_num(self):
            return self.page + 1 if self.has_next else None
            
        def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
            """Iterate over page numbers."""
            last = 0
            for num in range(1, self.pages + 1):
                if (num <= left_edge or
                    (self.page - left_current - 1 < num < self.page + right_current) or
                    num > self.pages - right_edge):
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
    
    # Create our pagination object
    total = len(unique_results)
    pagination = Pagination(
        items=paged_results,
        page=page,
        per_page=per_page,
        total=total
    )
    
    return render_template('results.html', results=pagination, lottery_type=lottery_type)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Page for configuring screenshot schedules (admin only)"""
    if request.method == 'POST':
        url = request.form.get('url')
        lottery_type = request.form.get('lottery_type')
        frequency = request.form.get('frequency', 'daily')
        hour = request.form.get('hour', 0, type=int)
        minute = request.form.get('minute', 0, type=int)
        
        if not url or not lottery_type:
            flash('URL and lottery type are required', 'danger')
            return redirect(url_for('settings'))
        
        # Create or update schedule
        config = ScheduleConfig.query.filter_by(url=url).first()
        if not config:
            config = ScheduleConfig(url=url, lottery_type=lottery_type, 
                                  frequency=frequency, hour=hour, minute=minute, active=True)
            db.session.add(config)
        else:
            config.lottery_type = lottery_type
            config.frequency = frequency
            config.hour = hour
            config.minute = minute
            config.active = True
        
        db.session.commit()
        
        # Add to scheduler
        schedule_task(scheduler, config)
        
        flash('Schedule updated successfully', 'success')
        return redirect(url_for('settings'))
    
    schedules = ScheduleConfig.query.all()
    return render_template('settings.html', schedules=schedules)

@app.route('/toggle_schedule/<int:id>')
@login_required
@admin_required
def toggle_schedule(id):
    """Toggle a schedule on or off (admin only)"""
    config = ScheduleConfig.query.get_or_404(id)
    config.active = not config.active
    db.session.commit()
    
    if config.active:
        schedule_task(scheduler, config)
        flash(f'Schedule for {config.lottery_type} activated', 'success')
    else:
        remove_task(scheduler, config.id)
        flash(f'Schedule for {config.lottery_type} deactivated', 'warning')
        
    return redirect(url_for('settings'))

@app.route('/delete_schedule/<int:id>')
@login_required
@admin_required
def delete_schedule(id):
    """Delete a schedule (admin only)"""
    config = ScheduleConfig.query.get_or_404(id)
    remove_task(scheduler, config.id)
    db.session.delete(config)
    db.session.commit()
    flash(f'Schedule for {config.lottery_type} deleted', 'warning')
    return redirect(url_for('settings'))

@app.route('/api/run_now/<int:id>')
@login_required
@admin_required
def run_now(id):
    """Manually run a scheduled task immediately in a background thread (admin only)"""
    config = ScheduleConfig.query.get_or_404(id)
    
    # Simply call the task function directly and let it handle threading
    logger.info(f"Manually running task for {config.url}")
    run_lottery_task(config.url, config.lottery_type)
    
    # Return immediately
    return jsonify({
        'status': 'success', 
        'message': f'Data sync started for {config.lottery_type}. This may take 30-60 seconds to complete.'
    })

@app.route('/api/screenshots')
def get_screenshots():
    """API endpoint to fetch recent screenshots"""
    screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).limit(20).all()
    return jsonify([{
        'id': s.id,
        'url': s.url,
        'lottery_type': s.lottery_type,
        'timestamp': s.timestamp.isoformat(),
        'path': s.path
    } for s in screenshots])

@app.route('/api/results/<lottery_type>')
def get_results(lottery_type):
    """API endpoint to fetch results for a specific lottery type"""
    limit = request.args.get('limit', 10, type=int)
    results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).limit(limit).all()
    return jsonify([r.to_dict() for r in results])

@app.route('/visualizations')
def visualizations():
    """Data visualization dashboard for lottery results"""
    # Get all lottery types for filter options
    lottery_types = db.session.query(LotteryResult.lottery_type).distinct().all()
    lottery_types = [lt[0] for lt in lottery_types]  # Convert from tuples to strings
    
    # Get latest results for initial display
    latest_results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).limit(20).all()
    
    return render_template('visualizations.html', 
                          lottery_types=lottery_types,
                          latest_results=latest_results)

@app.route('/import-data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_data():
    """Page for importing lottery data from spreadsheets (admin only)"""
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # Check if no file was selected
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        # Check if the file is an Excel file
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Only Excel files (.xlsx, .xls) are allowed', 'danger')
            return redirect(request.url)
            
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(app.root_path, 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            
        # Save the file securely
        filename = secure_filename(file.filename)
        file_path = os.path.join(uploads_dir, filename)
        file.save(file_path)
        
        # Get the purge option
        purge_option = request.form.get('purge', 'no')
        should_purge = purge_option == 'yes'
        
        # Import the data
        if should_purge:
            from purge_data import purge_data
            purge_data()
            flash('Existing data purged successfully', 'warning')
            
        # Process the Excel file
        success = import_snap_lotto_data(file_path, flask_app=app)
        
        # Clean up - remove the uploaded file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing uploaded file: {str(e)}")
            
        if success:
            flash('Spreadsheet data imported successfully', 'success')
        else:
            flash('Error importing spreadsheet data. Check the logs for details.', 'danger')
            
        return redirect(url_for('index'))
        
    return render_template('import_data.html')

@app.route('/api/visualization-data')
def visualization_data():
    """API endpoint to fetch data for visualizations"""
    lottery_type = request.args.get('lottery_type', None)
    data_type = request.args.get('data_type', 'numbers_frequency')
    
    if lottery_type:
        query = LotteryResult.query.filter_by(lottery_type=lottery_type)
    else:
        query = LotteryResult.query
    
    results = query.order_by(LotteryResult.draw_date.desc()).limit(100).all()
    
    # Check if we have any results to work with
    if not results:
        return jsonify({
            'error': 'No data available',
            'message': 'No lottery results found for the selected filters.'
        })
    
    if data_type == 'numbers_frequency':
        # Calculate frequency of each number
        frequencies = {}
        total_draws = len(results)
        
        # Initialize all possible numbers based on lottery type
        max_number = 49  # Default for regular lotto
        if lottery_type and 'daily' in lottery_type.lower():
            max_number = 36  # Daily Lotto uses 1-36
        
        # Initialize all possible numbers with zero frequency
        for i in range(1, max_number + 1):
            frequencies[i] = 0
            
        # Count actual frequencies
        for result in results:
            numbers = result.get_numbers_list()
            for num in numbers:
                if num in frequencies:
                    frequencies[num] += 1
        
        # Convert to sorted list of dictionaries for easier manipulation in JavaScript
        sorted_frequencies = []
        for num, freq in sorted(frequencies.items(), key=lambda x: int(x[0])):
            sorted_frequencies.append({
                'number': str(num),
                'frequency': freq
            })
        
        # Format for Chart.js
        chart_data = {
            'labels': [item['number'] for item in sorted_frequencies],
            'datasets': [{
                'label': f'Number Frequency for {lottery_type if lottery_type else "All Types"}',
                'data': [item['frequency'] for item in sorted_frequencies],
                'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            }],
            'frequencies': sorted_frequencies,  # Add sorted frequency data for better insights
            'totalDraws': total_draws
        }
        
        return jsonify(chart_data)
    
    elif data_type == 'winners_by_division':
        # Get winners by division
        division_winners = {}
        
        for result in results:
            divisions = result.get_divisions()
            if divisions:
                for div, data in divisions.items():
                    if div not in division_winners:
                        division_winners[div] = 0
                    
                    # Add winners from this draw
                    try:
                        winners = int(data.get('winners', 0))
                        division_winners[div] += winners
                    except (ValueError, TypeError):
                        # Skip if winners not a valid number
                        pass
        
        # Sort divisions by division number
        sorted_divisions = sorted(division_winners.items(), 
                                key=lambda x: int(x[0].split(' ')[1]) if len(x[0].split(' ')) > 1 and x[0].split(' ')[1].isdigit() else 999)
        
        chart_data = {
            'labels': [div[0] for div in sorted_divisions],
            'datasets': [{
                'label': f'Winners by Division for {lottery_type if lottery_type else "All Types"}',
                'data': [div[1] for div in sorted_divisions],
                'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1
            }]
        }
        
        return jsonify(chart_data)
    
    elif data_type == 'prize_amounts':
        # Get average prize amounts by division
        division_prizes = {}
        division_counts = {}
        
        # Extract only actual prize values (no defaults or placeholders)
        for result in results:
            divisions = result.get_divisions()
            if divisions:
                for div, data in divisions.items():
                    # Get prize value from the data
                    try:
                        prize_str = data.get('prize', '0')
                        # Clean up the string and convert to float
                        prize_str = prize_str.replace('R', '').replace(',', '').strip()
                        
                        # Only process actual prize values (not zeros or placeholders)
                        if prize_str and prize_str != '0':
                            prize = float(prize_str)
                            
                            # Add to our running totals
                            if div not in division_prizes:
                                division_prizes[div] = prize
                                division_counts[div] = 1
                            else:
                                division_prizes[div] += prize
                                division_counts[div] += 1
                    except (ValueError, TypeError):
                        # If conversion fails, skip this entry
                        pass
                        
        # If no real prize data available, return a special message
        if not division_prizes:
            return jsonify({
                'error': 'No real prize data available',
                'message': 'No actual prize amounts are available for this lottery type'
            })
        
        # Calculate averages
        for div in division_prizes:
            if division_counts[div] > 0:
                division_prizes[div] = division_prizes[div] / division_counts[div]
        
        # Sort divisions by division number
        sorted_divisions = sorted(division_prizes.items(), 
                                key=lambda x: int(x[0].split(' ')[1]) if len(x[0].split(' ')) > 1 and x[0].split(' ')[1].isdigit() else 999)
        
        chart_data = {
            'labels': [div[0] for div in sorted_divisions],
            'datasets': [{
                'label': f'Average Prize Amount (R) for {lottery_type if lottery_type else "All Types"}',
                'data': [div[1] for div in sorted_divisions],
                'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            }]
        }
        
        return jsonify(chart_data)
    
    elif data_type == 'draw_dates':
        # Group results by draw date
        date_counts = {}
        for result in results:
            date_str = result.draw_date.strftime('%Y-%m-%d')
            if date_str in date_counts:
                date_counts[date_str] += 1
            else:
                date_counts[date_str] = 1
        
        # Sort by date
        sorted_dates = sorted(date_counts.items())
        
        chart_data = {
            'labels': [date[0] for date in sorted_dates],
            'datasets': [{
                'label': f'Number of Draws for {lottery_type if lottery_type else "All Types"}',
                'data': [date[1] for date in sorted_dates],
                'backgroundColor': 'rgba(153, 102, 255, 0.6)',
                'borderColor': 'rgba(153, 102, 255, 1)',
                'fill': False,
                'tension': 0.1
            }]
        }
        
        return jsonify(chart_data)
    
    return jsonify({'error': 'Invalid data type'})

@app.route('/admin/cleanup-screenshots', methods=['GET', 'POST'])
@login_required
@admin_required
def cleanup_screenshots():
    """Admin endpoint to manually clean up old screenshots (admin only)"""
    if request.method == 'POST':
        from screenshot_manager import cleanup_old_screenshots
        try:
            cleanup_old_screenshots()
            flash('Screenshot cleanup completed successfully', 'success')
        except Exception as e:
            logger.error(f"Error during screenshot cleanup: {str(e)}")
            flash(f'Error during cleanup: {str(e)}', 'danger')
        
        return redirect(url_for('settings'))
    
    return render_template('cleanup.html')

@app.route('/draw-details/<lottery_type>/<draw_number>')
def draw_details(lottery_type, draw_number):
    """Page for viewing detailed prize payout information for a specific draw"""
    
    # Import normalize_draw_number
    from data_aggregator import normalize_draw_number
    
    # Normalize draw number for lookup 
    normalized_draw = normalize_draw_number(draw_number)
    
    # Find the lottery result for this draw number
    result = LotteryResult.query.filter_by(
        lottery_type=lottery_type,
        draw_number=normalized_draw
    ).first()
    
    if not result:
        # Try with broader search if exact match not found
        results = LotteryResult.query.filter(
            LotteryResult.lottery_type == lottery_type,
            LotteryResult.draw_number.like(f"%{normalized_draw}%")
        ).all()
        
        if results:
            # Use first match if any found
            result = results[0]
    
    if not result:
        flash(f"No data found for {lottery_type} Draw {draw_number}", "warning")
        return redirect(url_for('results', lottery_type=lottery_type))
    
    # Get the divisions data
    divisions = result.get_divisions()
    
    # Get the draw date formatted nicely
    draw_date = result.draw_date.strftime('%A, %d %B %Y')
    
    return render_template(
        'draw_details.html', 
        result=result, 
        divisions=divisions, 
        draw_date=draw_date,
        lottery_type=lottery_type
    )

@app.route('/api/raw-ocr/<lottery_type>')
def get_raw_ocr(lottery_type):
    """API endpoint to fetch raw OCR data for a specific lottery type"""
    from ocr_processor import process_screenshot
    
    # Find the most recent screenshot record for this lottery type
    screenshot = Screenshot.query.filter_by(
        lottery_type=lottery_type
    ).order_by(Screenshot.timestamp.desc()).first()
    
    if not screenshot:
        return jsonify({'error': 'No screenshot found for this lottery type'})
    
    # Process the screenshot with OCR
    try:
        raw_data = process_screenshot(screenshot.path, lottery_type)
        
        # Extract OCR provider information
        ocr_provider = raw_data.get('ocr_provider', 'unknown')
        ocr_model = raw_data.get('ocr_model', 'unknown')
        chat_model = raw_data.get('chat_model', None)
        
        # Build enhanced response
        response = {
            'screenshot_info': {
                'id': screenshot.id,
                'path': screenshot.path,
                'timestamp': screenshot.timestamp.isoformat(),
                'processed': screenshot.processed
            },
            'ocr_info': {
                'provider': ocr_provider,
                'model': ocr_model,
                'timestamp': raw_data.get('ocr_timestamp')
            },
            'ocr_data': raw_data
        }
        
        # Add model version info if available
        if chat_model:
            response['ocr_info']['model_version'] = chat_model
            
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing screenshot with OCR: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/ticket-scanner')
def ticket_scanner():
    """Page for scanning lottery tickets and checking if they won"""
    return render_template('ticket_scanner_new.html')

@app.route('/scan-ticket', methods=['POST'])
@csrf.exempt  # Exempt this route from CSRF protection for fetch API
def scan_ticket():
    """API endpoint to process a lottery ticket image and check if it's a winner"""
    app.logger.info("Scan ticket endpoint called")
    
    # CSRF protection is disabled for this endpoint
    # This is needed because we're using fetch API without CSRF token
    if 'ticket_image' not in request.files:
        app.logger.error("No ticket image in request files")
        return jsonify({'error': 'No ticket image provided'})
        
    file = request.files['ticket_image']
    if file.filename == '':
        app.logger.error("Empty filename in ticket image")
        return jsonify({'error': 'No ticket image selected'})
        
    app.logger.info(f"Processing ticket image: {file.filename}")
        
    # Lottery type is now optional - the OCR will detect it if not provided
    lottery_type = request.form.get('lottery_type', 'unknown')
    app.logger.info(f"Lottery type: {lottery_type}")
        
    draw_number = request.form.get('draw_number', None)
    if draw_number and draw_number.strip() == '':
        draw_number = None
    app.logger.info(f"Draw number: {draw_number}")
        
    # Read the image data
    try:
        image_data = file.read()
        app.logger.info(f"Image data read successfully: {len(image_data)} bytes")
        
        # Process the ticket image
        app.logger.info("Calling process_ticket_image function")
        result = process_ticket_image(image_data, lottery_type, draw_number)
        
        app.logger.info(f"Ticket processing result: {json.dumps(result, default=str)}")
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error processing ticket image: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f"Failed to process ticket: {str(e)}"})