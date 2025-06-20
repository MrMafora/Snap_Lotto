"""
Clean main application with proper error handling and no legacy conflicts.
"""
import logging
import os
import threading
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

# Import models and config
from models import LotteryResult, User, db
from config import Config

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SESSION_SECRET", "lottery-scraper-default-secret")

# Database setup
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info("Using PostgreSQL database")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'
    logger.warning("Using SQLite fallback")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 30
}

if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS']["connect_args"] = {"sslmode": "require"}

# Initialize database
db.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# Initialize database
def init_db():
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database initialized")
            
            # Create admin user if needed
            if not User.query.filter_by(username='admin').first():
                admin_user = User()
                admin_user.username = 'admin'
                admin_user.email = 'admin@localhost.com'
                admin_user.is_admin = True
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Admin user created: admin/admin123")
        except Exception as e:
            logger.error(f"Database init error: {e}")

# Routes
@app.route('/')
def home():
    from cache_manager import get_optimized_latest_results
    try:
        # Use optimized cached query for better performance
        results = get_optimized_latest_results(limit=6)
        
        # Calculate frequency data efficiently
        number_counts = {}
        for result in results:
            numbers = result.get_numbers_list()
            for num in numbers:
                if isinstance(num, (int, str)) and str(num).isdigit():
                    num_int = int(num)
                    number_counts[num_int] = number_counts.get(num_int, 0) + 1
        
        most_frequent = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        frequency_data = {'most_frequent': most_frequent, 'total_numbers': len(number_counts)}
        
        return render_template('index.html',
                              title="Latest South African Lottery Results",
                              recent_results=results,
                              frequency_data=frequency_data)
    except Exception as e:
        logger.error(f"Homepage error: {e}")
        return render_template('index.html',
                              title="Latest South African Lottery Results",
                              recent_results=[],
                              frequency_data={'most_frequent': [], 'total_numbers': 0})

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    from cache_manager import get_optimized_lottery_stats
    try:
        data_stats = get_optimized_lottery_stats()
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        data_stats = {'total_results': 0, 'latest_draw': 'Error', 'latest_date': 'Error'}
    
    return render_template('admin/dashboard.html', title="Admin Dashboard", data_stats=data_stats)

@app.route('/automation')
@login_required
def automation_control():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    return render_template('admin/automation_control.html', title="Automation Control")

@app.route('/automation/run-step', methods=['POST'])
@login_required
def run_automation_step():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    step = request.form.get('step')
    
    try:
        if step == 'cleanup':
            import step1_cleanup
            step1_cleanup.run_cleanup()
            flash('Cleanup completed', 'success')
        elif step == 'capture':
            import step2_capture
            step2_capture.run_screenshot_capture()
            flash('Screenshot capture completed', 'success')
        elif step == 'ai_process':
            import step3_ai_process
            step3_ai_process.run_ai_process()
            flash('AI processing completed', 'success')
        elif step == 'database':
            import step4_database
            step4_database.run_database_update()
            flash('Database update completed', 'success')
        else:
            flash('Invalid step', 'error')
    except Exception as e:
        logger.error(f"Step {step} error: {e}")
        flash(f'Step failed: {str(e)}', 'error')
    
    return redirect(url_for('automation_control'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful', 'success')
            return redirect(request.args.get('next') or '/')
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html', title="Admin Login")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Logged out', 'info')
    return redirect('/')

@app.route('/results')
def results():
    """Results page with all lottery results"""
    try:
        results = LotteryResult.query.order_by(LotteryResult.id.desc()).limit(50).all()
        return render_template('results.html', title="Lottery Results", results=results)
    except Exception as e:
        logger.error(f"Results page error: {e}")
        return render_template('results.html', title="Lottery Results", results=[])

@app.route('/ticket-scanner')
@app.route('/scanner')
def ticket_scanner():
    """Ticket scanner page"""
    return render_template('scanner.html', title="Lottery Ticket Scanner")

@app.route('/frequency-analysis')
def frequency_analysis():
    """Frequency analysis page"""
    return render_template('frequency.html', title="Frequency Analysis")

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html', title="About")

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html', title="Contact")

@app.route('/visualizations')
def visualizations():
    """Data visualizations page"""
    return render_template('visualizations.html', title="Data Visualizations")

@app.route('/statistics')
def statistics():
    """Statistics page"""
    return render_template('statistics.html', title="Statistics")

@app.route('/predictions')
def predictions():
    """Predictions page"""
    return render_template('predictions.html', title="Predictions")

@app.route('/history')
def history():
    """Historical results page"""
    try:
        results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).limit(100).all()
        return render_template('history.html', title="Historical Results", results=results)
    except Exception as e:
        logger.error(f"History page error: {e}")
        return render_template('history.html', title="Historical Results", results=[])

@app.route('/scheduler-status')
@login_required
def scheduler_status():
    """Scheduler status page"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    status_info = {
        'status': 'Running',
        'next_run': 'Daily at 1:00 AM',
        'last_run': 'Not scheduled yet',
        'enabled': True
    }
    return render_template('admin/scheduler_status.html', 
                          title="Scheduler Status", 
                          status=status_info)

@app.route('/system-health')
@login_required
def system_health():
    """System health monitoring page"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    health_info = {
        'database': 'Connected',
        'server': 'Running',
        'memory': 'Normal',
        'disk': 'Normal'
    }
    return render_template('admin/health.html', 
                          title="System Health", 
                          health=health_info)

@app.route('/import-data')
@login_required
def import_data():
    """Data import page"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    return render_template('admin/import.html', title="Import Data")

@app.route('/import-history')
@login_required
def import_history():
    """Import history page"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    return render_template('admin/import_history.html', title="Import History")

@app.route('/settings')
@login_required
def settings():
    """Application settings page"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    return render_template('settings.html', title="Settings")

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Admin user registration page"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if username and email and password:
            new_user = User()
            new_user.username = username
            new_user.email = email
            new_user.set_password(password)
            new_user.is_admin = True
            db.session.add(new_user)
            db.session.commit()
            flash(f'Admin user {username} created successfully', 'success')
            return redirect(url_for('admin'))
        else:
            flash('All fields are required', 'danger')
    
    return render_template('register.html', title="Add Admin User")

@app.route('/api-tracking')
@login_required
def api_tracking_view():
    """API usage tracking page"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    tracking_data = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'average_response_time': 0
    }
    return render_template('admin/api_tracking.html', title="API Tracking", data=tracking_data)

# API routes for frequency analysis
@app.route('/api/lottery-analysis/frequency')
def frequency_api():
    try:
        days = request.args.get('days', 365, type=int)
        lottery_type = request.args.get('lottery_type')
        
        query = LotteryResult.query
        if lottery_type:
            query = query.filter_by(lottery_type=lottery_type)
        
        results = query.order_by(LotteryResult.id.desc()).limit(100).all()
        
        number_counts = {}
        for result in results:
            numbers = result.get_numbers_list()
            for num in numbers:
                if isinstance(num, (int, str)) and str(num).isdigit():
                    num_int = int(num)
                    number_counts[num_int] = number_counts.get(num_int, 0) + 1
        
        most_frequent = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return jsonify({
            'success': True,
            'lottery_types': ['All Lottery Types'],
            'frequency_data': most_frequent,
            'total_numbers': len(number_counts)
        })
    
    except Exception as e:
        logger.error(f"Frequency API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Initialize in background
threading.Thread(target=init_db, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)