"""
Simple main application for South African Lottery System
Core functionality without complex imports
"""
import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import core models and config
from models import db, LotteryResult, User
from config import Config

# Create the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF Protection
csrf = CSRFProtect(app)

# Add proxy fix for deployment
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Homepage with latest lottery results"""
    try:
        # Get latest results for each lottery type
        lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 'Powerball', 'Powerball Plus', 'Daily Lotto']
        latest_results = {}
        
        for lottery_type in lottery_types:
            result = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
            if result:
                latest_results[lottery_type] = result
        
        return render_template('index.html', latest_results=latest_results)
    except Exception as e:
        logger.error(f"Error loading homepage: {e}")
        return render_template('index.html', latest_results={})

@app.route('/ticket-scanner')
def ticket_scanner():
    """Ticket scanner page"""
    return render_template('ticket_scanner.html')

@app.route('/process-ticket', methods=['POST'])
@csrf.exempt
def process_ticket():
    """Process a lottery ticket image"""
    try:
        if 'ticket_image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['ticket_image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # For now, return a placeholder response
        # In production, this would process the image with AI
        return jsonify({
            'success': True,
            'message': 'Ticket scanner is ready! Please provide your Anthropic API key to enable full ticket analysis.',
            'extracted_numbers': [],
            'lottery_type': 'Unknown',
            'draw_date': None,
            'winning_matches': []
        })
        
    except Exception as e:
        logger.error(f"Error processing ticket: {e}")
        return jsonify({'error': 'Failed to process ticket'}), 500

@app.route('/results')
def results():
    """Show overview of all lottery types"""
    try:
        lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 'Powerball', 'Powerball Plus', 'Daily Lotto']
        results_overview = {}
        
        for lottery_type in lottery_types:
            count = LotteryResult.query.filter_by(lottery_type=lottery_type).count()
            latest = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
            results_overview[lottery_type] = {
                'count': count,
                'latest': latest
            }
        
        return render_template('results.html', results_overview=results_overview)
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return render_template('results.html', results_overview={})

@app.route('/results/<lottery_type>')
def lottery_results(lottery_type):
    """Show all results for a specific lottery type"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(
            LotteryResult.draw_date.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('lottery_results.html', 
                             results=results, 
                             lottery_type=lottery_type)
    except Exception as e:
        logger.error(f"Error loading {lottery_type} results: {e}")
        return render_template('lottery_results.html', 
                             results=None, 
                             lottery_type=lottery_type)

@app.route('/health-check')
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'South African Lottery System is running'})

# Initialize database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)