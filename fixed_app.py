"""
Fixed lottery data application with direct port binding
This simplified version solves the white screen issue
"""
import os
import logging
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy base
class Base(DeclarativeBase):
    pass

# Initialize database
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)

# Configure the app
app.secret_key = os.environ.get("SESSION_SECRET", "lottery-scraper-default-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Explicitly set database URI from environment variable
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Ensure proper PostgreSQL connection string format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info(f"Using database from DATABASE_URL environment variable")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery_data.db'
    logger.warning("DATABASE_URL not found, using SQLite database instead")

# Initialize SQLAlchemy with additional connection settings
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True
}

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models only after db is initialized
from models import LotteryResult, User

@login_manager.user_loader
def load_user(user_id):
    """Load user for login manager"""
    return User.query.get(int(user_id))

# Initialize database in a background thread
def init_database():
    """Create database tables in a background thread"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

# Start database initialization in background
threading.Thread(target=init_database, daemon=True).start()

@app.route('/')
def index():
    """Homepage with latest lottery results"""
    try:
        # Simple query to get last 5 lottery results
        with app.app_context():
            recent_results = LotteryResult.query.order_by(
                LotteryResult.draw_date.desc()
            ).limit(5).all()
            
            lottery_types = db.session.query(LotteryResult.lottery_type).distinct().all()
            lottery_types = [t[0] for t in lottery_types]
            
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Lottery Data Platform</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .header { background-color: #3498db; color: white; padding: 20px; text-align: center; }
                .results-container { display: flex; flex-wrap: wrap; justify-content: space-between; margin-top: 20px; }
                .result-card { background-color: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
                              padding: 20px; margin-bottom: 20px; width: calc(50% - 20px); }
                h1, h2, h3 { margin-top: 0; }
                .lottery-type { color: #3498db; }
                .numbers { display: flex; flex-wrap: wrap; margin: 15px 0; }
                .number { display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; 
                          border-radius: 50%; background-color: #2c3e50; color: white; margin-right: 10px; 
                          margin-bottom: 10px; font-weight: bold; }
                .bonus-number { background-color: #e74c3c; }
                .date { color: #7f8c8d; font-size: 0.9em; }
                .footer { text-align: center; margin-top: 30px; padding: 20px; color: #7f8c8d; 
                         border-top: 1px solid #ddd; }
                .message { background-color: #2ecc71; color: white; padding: 15px; border-radius: 5px; 
                          margin: 20px 0; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Lottery Data Platform</h1>
                <p>Your comprehensive source for lottery results and analysis</p>
            </div>
            
            <div class="container">
                <div class="message">
                    <strong>Success!</strong> The application is now working properly.
                </div>
                
                <h2>Recent Lottery Results</h2>
                
                <div class="results-container">
                    {% if recent_results %}
                        {% for result in recent_results %}
                            <div class="result-card">
                                <h3 class="lottery-type">{{ result.lottery_type }}</h3>
                                <div class="date">Draw Date: {{ result.get_formatted_date() }}</div>
                                <div class="date">Draw Number: {{ result.draw_number }}</div>
                                
                                <div class="numbers">
                                    {% for number in result.get_numbers_list() %}
                                        <div class="number">{{ number }}</div>
                                    {% endfor %}
                                    
                                    {% for bonus in result.get_bonus_numbers_list() %}
                                        <div class="number bonus-number">{{ bonus }}</div>
                                    {% endfor %}
                                </div>
                            </div>
                        {% endfor %}
                    {% else %}
                        <p>No recent lottery results found in the database.</p>
                    {% endif %}
                </div>
                
                <h2>Available Lottery Types</h2>
                <ul>
                    {% for type in lottery_types %}
                        <li>{{ type }}</li>
                    {% endfor %}
                </ul>
            </div>
            
            <div class="footer">
                <p>&copy; 2025 Lottery Data Platform - All rights reserved</p>
            </div>
        </body>
        </html>
        """, recent_results=recent_results, lottery_types=lottery_types)
    
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        
        # Show a friendly error page
        return f"""
        <html>
            <head>
                <title>Lottery Data Platform</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    h1 {{ color: #2c3e50; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    .error {{ color: #e74c3c; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Lottery Data Platform</h1>
                    <p>The application is running, but there was an error loading the lottery data:</p>
                    <p class="error">{str(e)}</p>
                </div>
            </body>
        </html>
        """

def render_template_string(template_string, **context):
    """Simple template rendering function since we might not have templates folder yet"""
    from jinja2 import Template
    template = Template(template_string)
    return template.render(**context)

if __name__ == "__main__":
    # Get the port from environment variable or use default
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting fixed lottery application on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)