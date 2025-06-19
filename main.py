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
login_manager.login_view = 'login'

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
    try:
        # Get recent lottery results
        results = LotteryResult.query.order_by(LotteryResult.id.desc()).limit(6).all()
        
        # Calculate frequency data
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
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    try:
        total_results = LotteryResult.query.count()
        latest_result = LotteryResult.query.order_by(LotteryResult.id.desc()).first()
        
        data_stats = {
            'total_results': total_results,
            'latest_draw': latest_result.draw_number if latest_result else 'None',
            'latest_date': latest_result.draw_date.strftime('%Y-%m-%d') if latest_result else 'None'
        }
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
            step3_ai_process.run_ai_processing()
            flash('AI processing completed', 'success')
        elif step == 'database':
            import step4_database
            step4_database.run_database_save()
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