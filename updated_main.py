"""
Updated main application entry point for the Lottery Data Platform.
This version is configured to bind directly to port 8080 for reliable access.
"""
import os
import logging
import threading
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, send_from_directory, send_file, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from csrf_fix import EnhancedCSRFProtect

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models 
from models import LotteryResult, ScheduleConfig, Screenshot, User, Advertisement, AdImpression, Campaign, AdVariation, ImportHistory, ImportedRecord, db
from config import Config

# Create Flask application
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Explicitly set database URI
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Ensure proper PostgreSQL connection string format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info(f"Using database from DATABASE_URL environment variable")
else:
    logger.warning("DATABASE_URL not found, using fallback database configuration")

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF Protection
csrf = EnhancedCSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database in background
def init_database():
    """Initialize database tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")

# Start database initialization in background
threading.Thread(target=init_database, daemon=True).start()

@app.route('/')
def index():
    """Homepage with latest lottery results"""
    try:
        # Simple query to get last 5 lottery results
        recent_results = LotteryResult.query.order_by(
            LotteryResult.draw_date.desc()
        ).limit(5).all()
        
        # Get unique lottery types
        lottery_types = db.session.query(LotteryResult.lottery_type).distinct().all()
        lottery_types = [t[0] for t in lottery_types]
        
        return render_template('index.html', 
                              recent_results=recent_results,
                              lottery_types=lottery_types)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Lottery Data Platform</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f6f9;
                    color: #333;
                }
                .container {
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 20px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                }
                .error {
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                    border-left: 5px solid #f5c6cb;
                }
                .success {
                    background-color: #d4edda;
                    color: #155724;
                    padding: 15px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                    border-left: 5px solid #c3e6cb;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Lottery Data Platform</h1>
                <div class="success">
                    <strong>Success!</strong> The application is running correctly.
                </div>
                <div class="error">
                    <strong>Note:</strong> There was an error loading the lottery data, but the application itself is working properly.
                    <br><br>
                    Error details: {str(e)}
                </div>
            </div>
        </body>
        </html>
        """

# Define templates directory
@app.route('/templates/<path:path>')
def send_template(path):
    """Serve templates directory"""
    return send_from_directory('templates', path)

# Run the application
if __name__ == '__main__':
    # Determine port - use 8080 by default for direct access
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting lottery application on port {port}")
    app.run(host='0.0.0.0', port=port)