"""
Routes for the Snap Lotto application
"""
import os
import json
import logging
import shutil
from functools import wraps
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from flask_wtf import FlaskForm, CSRFProtect
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField, BooleanField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

# Import models and utilities
from main import db   # Import db from main.py instead of models
from models import Screenshot, LotteryResult, ScheduleConfig, User
from data_aggregator import aggregate_data, validate_and_correct_known_draws
from scheduler import run_lottery_task
from ticket_scanner import process_ticket_image
from import_snap_lotto_data import import_snap_lotto_data

def register_routes(app):
    """Register all application routes"""
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for flask-login"""
        return User.query.get(int(user_id))
    
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
        
        def validate_username(self, username):
            """Validate username is not already taken"""
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is already taken. Please choose a different one.')
                
        def validate_email(self, email):
            """Validate email is not already registered"""
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email is already registered. Please use a different one.')
    
    def admin_required(f):
        """Decorator for routes that require admin privileges"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Admin login route"""
        if current_user.is_authenticated:
            return redirect(url_for('admin_dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
            else:
                flash('Login unsuccessful. Please check username and password', 'danger')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    def logout():
        """Admin logout route"""
        logout_user()
        return redirect(url_for('index'))
    
    @app.route('/register', methods=['GET', 'POST'])
    @admin_required
    def register():
        """Admin registration route (only accessible by existing admins)"""
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = User.generate_password_hash(form.password.data)
            user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('admin_dashboard'))
        return render_template('register.html', title='Register', form=form)
    
    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """Admin dashboard showing links to admin-only features"""
        screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).limit(5).all()
        schedule_configs = ScheduleConfig.query.all()
        return render_template('admin_dashboard.html', screenshots=screenshots, schedule_configs=schedule_configs)
    
    @app.route('/')
    def index():
        """Home page showing lottery results and ticket scanning feature"""
        from data_aggregator import get_latest_results
        latest_results = get_latest_results()
        return render_template('index.html', latest_results=latest_results)
    
    @app.route('/results')
    def results():
        """Page showing all lottery results"""
        page = request.args.get('page', 1, type=int)
        per_page = 10
        lottery_type = request.args.get('lottery_type', None)
        
        class Pagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
            
            @property
            def prev_num(self):
                """Previous page number"""
                return self.page - 1 if self.page > 1 else None
            
            @property
            def next_num(self):
                """Next page number"""
                return self.page + 1 if self.page * self.per_page < self.total else None
                
            def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                """Iterate over page numbers."""
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                       (num > self.page - left_current - 1 and \
                        num < self.page + right_current) or \
                       num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
                
            @property
            def pages(self):
                """Total number of pages"""
                return (self.total + self.per_page - 1) // self.per_page
        
        # Query for lottery results
        query = LotteryResult.query
        if lottery_type:
            query = query.filter_by(lottery_type=lottery_type)
        
        query = query.order_by(LotteryResult.draw_date.desc())
        total = query.count()
        
        # Get paginated results
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        pagination = Pagination(items, page, per_page, total)
        
        # Get all lottery types for the filter
        all_lottery_types = db.session.query(LotteryResult.lottery_type).distinct().all()
        all_lottery_types = [lt[0] for lt in all_lottery_types]
        
        return render_template('results.html', results=pagination, 
                              lottery_type=lottery_type,
                              all_lottery_types=all_lottery_types)
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({"status": "ok"})
    
    @app.route('/ticket-scanner')
    def ticket_scanner():
        """Page for scanning lottery tickets and checking if they won"""
        class EmptyForm(FlaskForm):
            pass
        
        form = EmptyForm()
        return render_template('ticket_scanner_new.html', form=form)
    
    # The rest of the routes can be added as needed
    
    # Add visualization and admin routes
    
    @app.route('/visualizations')
    def visualizations():
        """Data visualization dashboard for lottery results"""
        return render_template('visualizations.html')
    
    @app.route('/api/visualization-data')
    def visualization_data():
        """API endpoint to fetch data for visualizations"""
        lottery_type = request.args.get('lottery_type', 'Lotto')
        results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date).all()
        
        data = {
            'labels': [result.draw_date.strftime('%Y-%m-%d') for result in results],
            'numbers': [],
            'frequency': {}
        }
        
        # Initialize frequency counter
        for i in range(1, 53):  # Assuming max ball is 52
            data['frequency'][str(i)] = 0
            
        # Track numbers and frequencies
        for result in results:
            numbers = result.get_numbers_list()
            for num in numbers:
                data['frequency'][str(num)] += 1
        
        # Convert to sorted list for chart
        data['frequency'] = [{'number': int(k), 'count': v} for k, v in data['frequency'].items() if v > 0]
        data['frequency'].sort(key=lambda x: x['number'])
        
        return jsonify(data)
    
    @app.route('/settings', methods=['GET', 'POST'])
    @admin_required
    def settings():
        """Page for configuring screenshot schedules (admin only)"""
        schedules = ScheduleConfig.query.all()
        return render_template('settings.html', schedules=schedules)
    
    @app.route('/toggle-schedule/<int:id>', methods=['POST'])
    @admin_required
    def toggle_schedule(id):
        """Toggle a schedule on or off (admin only)"""
        schedule = ScheduleConfig.query.get_or_404(id)
        schedule.active = not schedule.active
        db.session.commit()
        flash(f"Schedule for {schedule.lottery_type} {'activated' if schedule.active else 'deactivated'}", 'success')
        return redirect(url_for('settings'))
    
    @app.route('/delete-schedule/<int:id>', methods=['POST'])
    @admin_required
    def delete_schedule(id):
        """Delete a schedule (admin only)"""
        schedule = ScheduleConfig.query.get_or_404(id)
        db.session.delete(schedule)
        db.session.commit()
        flash(f"Schedule for {schedule.lottery_type} deleted", 'success')
        return redirect(url_for('settings'))
    
    @app.route('/run-now/<int:id>', methods=['POST'])
    @admin_required
    def run_now(id):
        """Manually run a scheduled task immediately in a background thread (admin only)"""
        import threading
        schedule = ScheduleConfig.query.get_or_404(id)
        flash(f"Running task for {schedule.lottery_type}. This may take a few minutes.", 'info')
        
        thread = threading.Thread(target=run_lottery_task, args=(schedule.id,))
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('settings'))
    
    @app.route('/api/get-screenshots')
    def get_screenshots():
        """API endpoint to fetch recent screenshots"""
        screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).limit(10).all()
        result = []
        for ss in screenshots:
            result.append({
                'id': ss.id,
                'url': ss.url,
                'lottery_type': ss.lottery_type,
                'timestamp': ss.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'path': ss.path,
                'processed': ss.processed
            })
        return jsonify(result)
    
    @app.route('/api/get-results/<lottery_type>')
    def get_results(lottery_type):
        """API endpoint to fetch results for a specific lottery type"""
        results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).limit(10).all()
        result = []
        for r in results:
            result.append(r.to_dict())
        return jsonify(result)
    
    @app.route('/import-data', methods=['GET', 'POST'])
    @admin_required
    def import_data():
        """Page for importing lottery data from spreadsheets (admin only)"""
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part', 'danger')
                return redirect(request.url)
                
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
                
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploads', filename)
                os.makedirs('uploads', exist_ok=True)
                file.save(file_path)
                
                try:
                    results = import_snap_lotto_data(file_path, app)
                    flash(f'Successfully imported {len(results)} lottery results', 'success')
                except Exception as e:
                    flash(f'Error during import: {str(e)}', 'danger')
                finally:
                    # Clean up upload
                    os.remove(file_path)
                
                return redirect(url_for('results'))
                
        return render_template('import_data.html')
    
    @app.route('/cleanup-screenshots', methods=['POST'])
    @admin_required
    def cleanup_screenshots():
        """Admin endpoint to manually clean up old screenshots (admin only)"""
        try:
            # Keep only the latest 100 screenshots
            screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).offset(100).all()
            count = 0
            
            for ss in screenshots:
                if os.path.exists(ss.path):
                    os.remove(ss.path)
                db.session.delete(ss)
                count += 1
                
            db.session.commit()
            flash(f'Successfully cleaned up {count} old screenshots', 'success')
        except Exception as e:
            flash(f'Error during cleanup: {str(e)}', 'danger')
            
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/draw/<lottery_type>/<draw_number>')
    def draw_details(lottery_type, draw_number):
        """Page for viewing detailed prize payout information for a specific draw"""
        draw = LotteryResult.query.filter_by(lottery_type=lottery_type, draw_number=draw_number).first_or_404()
        return render_template('draw_details.html', draw=draw)
    
    @app.route('/api/get-raw-ocr/<lottery_type>')
    def get_raw_ocr(lottery_type):
        """API endpoint to fetch raw OCR data for a specific lottery type"""
        # This could be expanded to fetch real OCR data if needed
        return jsonify({"status": "Simulated OCR data for " + lottery_type})
    
    @app.route('/api/scan-ticket', methods=['POST'])
    def scan_ticket():
        """API endpoint to process a lottery ticket image and check if it's a winner"""
        if 'ticket_image' not in request.files:
            return jsonify({'status': 'error', 'message': 'No image file provided'})
            
        file = request.files['ticket_image']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'})
            
        if file:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            try:
                # Process the ticket image using our ticket_scanner module
                scan_results = process_ticket_image(file_path)
                
                # Clean up the upload
                os.remove(file_path)
                
                return jsonify({
                    'status': 'success', 
                    'data': scan_results
                })
            except Exception as e:
                # Clean up on error
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({
                    'status': 'error',
                    'message': f'Error processing ticket: {str(e)}'
                })
    
    # Add route for deployed test page for reference
    @app.route('/deployment-test')
    def deployment_test():
        """Deployment test page"""
        return render_template('deployment_test.html')