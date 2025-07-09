"""
Main application entry point for the South African Lottery Scanner
Advanced AI-powered lottery intelligence platform
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import json
import tempfile
import traceback
from sqlalchemy import and_, func, desc, asc
from sqlalchemy.orm import joinedload
from pathlib import Path
import uuid
from urllib.parse import quote, unquote

# Import configuration and models
from config import Config
from models import db, User, LotteryResult, ExtractionReview, HealthCheck, Alert, SystemLog
from security_utils import csrf, limiter, sanitize_input, validate_form_data, RateLimitExceeded

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize security
csrf.init_app(app)
limiter.init_app(app)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Database initialization
try:
    logger.info("Using database from DATABASE_URL environment variable")
    if 'ssl' in app.config['SQLALCHEMY_DATABASE_URI']:
        logger.info("PostgreSQL SSL mode enabled")
except Exception as e:
    logger.error(f"Database configuration error: {e}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Lazy loading for optional modules
def safe_import(module_name):
    """Safely import optional modules"""
    try:
        return __import__(module_name)
    except ImportError as e:
        logger.warning(f"Optional module {module_name} not available: {e}")
        return None

# Create database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

# Database type mapping for different lottery types
LOTTERY_TYPE_MAPPING = {
    'Lottery': ['LOTTO'],
    'Lottery Plus 1': ['LOTTO PLUS 1'],
    'Lottery Plus 2': ['LOTTO PLUS 2'],
    'Powerball': ['POWERBALL'],
    'Powerball Plus': ['POWERBALL PLUS'],
    'Daily Lottery': ['DAILY LOTTO']
}

# Display name mapping (reverse of above)
DISPLAY_NAME_MAPPING = {
    'LOTTO': 'Lottery',
    'LOTTO PLUS 1': 'Lottery Plus 1',
    'LOTTO PLUS 2': 'Lottery Plus 2',
    'POWERBALL': 'Powerball',
    'POWERBALL PLUS': 'Powerball Plus',
    'DAILY LOTTO': 'Daily Lottery'
}

class DrawResult:
    """Wrapper class for lottery results with additional methods"""
    def __init__(self, result):
        self.result = result
        self.lottery_type = result.lottery_type
        self.draw_number = result.draw_number
        self.draw_date = result.draw_date
        self.numbers = result.numbers
        self.bonus_numbers = result.bonus_numbers
        self.divisions = result.divisions
        self.rollover_amount = result.rollover_amount
        self.next_jackpot = result.next_jackpot
        self.total_pool_size = result.total_pool_size
        self.total_sales = result.total_sales
        self.draw_machine = result.draw_machine
        self.next_draw_date = result.next_draw_date
        
    def get_numbers_list(self):
        """Get main numbers as a list"""
        if isinstance(self.numbers, str):
            try:
                return json.loads(self.numbers)
            except:
                return []
        return self.numbers or []
    
    def get_bonus_numbers_list(self):
        """Get bonus numbers as a list"""
        if isinstance(self.bonus_numbers, str):
            try:
                return json.loads(self.bonus_numbers)
            except:
                return []
        return self.bonus_numbers or []
    
    def get_parsed_divisions(self):
        """Get parsed divisions data"""
        if not self.divisions or self.divisions == '[]':
            return []
        try:
            if isinstance(self.divisions, str):
                return json.loads(self.divisions)
            return self.divisions
        except:
            return []

@app.route('/')
def index():
    """Homepage with latest lottery results"""
    try:
        logger.info("=== HOMEPAGE: Loading fresh lottery data from database ===")
        
        # Use direct psycopg2 connection to bypass SQLAlchemy type issues
        import psycopg2
        import os
        
        connection_string = os.environ.get('DATABASE_URL')
        latest_results = []
        
        try:
            with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT lottery_type, draw_number, draw_date, numbers, bonus_numbers, divisions, 
                               rollover_amount, next_jackpot, total_pool_size, total_sales, draw_machine, next_draw_date
                        FROM lottery_result 
                        WHERE lottery_type IN ('LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO')
                        ORDER BY draw_date DESC 
                        LIMIT 50
                    """)
                    
                    for row in cur.fetchall():
                        # Create a fake LotteryResult object with the required methods
                        result_obj = type('Result', (), {})()
                        result_obj.lottery_type = row[0]
                        result_obj.draw_number = row[1]
                        result_obj.draw_date = row[2]
                        result_obj.numbers = row[3]
                        result_obj.bonus_numbers = row[4]
                        result_obj.divisions = row[5]
                        result_obj.rollover_amount = row[6]
                        result_obj.next_jackpot = row[7]
                        result_obj.total_pool_size = row[8]
                        result_obj.total_sales = row[9]
                        result_obj.draw_machine = row[10]
                        result_obj.next_draw_date = row[11]
                        
                        # Add the required methods
                        def get_numbers_list():
                            if isinstance(result_obj.numbers, str):
                                try:
                                    return json.loads(result_obj.numbers)
                                except:
                                    return []
                            return result_obj.numbers or []
                        
                        def get_bonus_numbers_list():
                            if isinstance(result_obj.bonus_numbers, str):
                                try:
                                    return json.loads(result_obj.bonus_numbers)
                                except:
                                    return []
                            return result_obj.bonus_numbers or []
                        
                        def get_parsed_divisions():
                            if not result_obj.divisions or result_obj.divisions == '[]':
                                return []
                            try:
                                if isinstance(result_obj.divisions, str):
                                    return json.loads(result_obj.divisions)
                                return result_obj.divisions
                            except:
                                return []
                        
                        result_obj.get_numbers_list = get_numbers_list
                        result_obj.get_bonus_numbers_list = get_bonus_numbers_list
                        result_obj.get_parsed_divisions = get_parsed_divisions
                        
                        latest_results.append(result_obj)
        except Exception as e:
            logger.error(f"Direct database connection failed: {e}")
            latest_results = []
        
        # Get unique lottery types with their latest results
        seen_types = set()
        unique_results = []
        for result in latest_results:
            if result.lottery_type not in seen_types:
                seen_types.add(result.lottery_type)
                unique_results.append(result)
        
        logger.info(f"HOMEPAGE: Loaded {len(unique_results)} results from database")
        
        # Get frequency analysis for homepage charts
        all_numbers = []
        for result in unique_results:
            if result.numbers:
                try:
                    if isinstance(result.numbers, str):
                        numbers = json.loads(result.numbers)
                    else:
                        numbers = result.numbers
                    all_numbers.extend(numbers)
                except:
                    pass
        
        # Calculate frequency
        from collections import Counter
        frequency = Counter(all_numbers)
        top_numbers = frequency.most_common(10)
        
        logger.info(f"Frequency analysis: Found {len(set(all_numbers))} unique numbers, top 10: {top_numbers}")
        
        return render_template('index.html', 
                             results=unique_results,
                             top_numbers=top_numbers,
                             total_numbers=len(set(all_numbers)))
    
    except Exception as e:
        logger.error(f"Homepage error: {e}")
        logger.error(traceback.format_exc())
        return render_template('index.html', results=[], top_numbers=[], total_numbers=0)

@app.route('/results')
@app.route('/results/<lottery_type>')
def results(lottery_type=None):
    """Display lottery results"""
    try:
        if lottery_type:
            # Map display name to database types
            db_types = LOTTERY_TYPE_MAPPING.get(lottery_type, [lottery_type])
            
            logger.info(f"Looking for lottery type '{lottery_type}' mapped to DB types '{db_types}'")
            
            # Use direct psycopg2 connection to bypass SQLAlchemy type issues
            import psycopg2
            import os
            
            connection_string = os.environ.get('DATABASE_URL')
            results = []
            
            try:
                with psycopg2.connect(connection_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT lottery_type, draw_number, draw_date, numbers, bonus_numbers, divisions, 
                                   rollover_amount, next_jackpot, total_pool_size, total_sales, draw_machine, next_draw_date
                            FROM lottery_result 
                            WHERE lottery_type = ANY(%s)
                            ORDER BY draw_date DESC 
                            LIMIT 20
                        """, (db_types,))
                        
                        for row in cur.fetchall():
                            # Create a fake LotteryResult object with the required methods
                            result_obj = type('Result', (), {})()
                            result_obj.lottery_type = row[0]
                            result_obj.draw_number = row[1]
                            result_obj.draw_date = row[2]
                            result_obj.numbers = row[3]
                            result_obj.bonus_numbers = row[4]
                            result_obj.divisions = row[5]
                            result_obj.rollover_amount = row[6]
                            result_obj.next_jackpot = row[7]
                            result_obj.total_pool_size = row[8]
                            result_obj.total_sales = row[9]
                            result_obj.draw_machine = row[10]
                            result_obj.next_draw_date = row[11]
                            
                            # Add the required methods
                            def get_numbers_list():
                                if isinstance(result_obj.numbers, str):
                                    try:
                                        return json.loads(result_obj.numbers)
                                    except:
                                        return []
                                return result_obj.numbers or []
                            
                            def get_bonus_numbers_list():
                                if isinstance(result_obj.bonus_numbers, str):
                                    try:
                                        return json.loads(result_obj.bonus_numbers)
                                    except:
                                        return []
                                return result_obj.bonus_numbers or []
                            
                            def get_parsed_divisions():
                                if not result_obj.divisions or result_obj.divisions == '[]':
                                    return []
                                try:
                                    if isinstance(result_obj.divisions, str):
                                        return json.loads(result_obj.divisions)
                                    return result_obj.divisions
                                except:
                                    return []
                            
                            result_obj.get_numbers_list = get_numbers_list
                            result_obj.get_bonus_numbers_list = get_bonus_numbers_list
                            result_obj.get_parsed_divisions = get_parsed_divisions
                            
                            results.append(result_obj)
            except Exception as e:
                logger.error(f"Direct database connection failed: {e}")
                results = []
            
            logger.info(f"Found {len(results)} results")
            
            return render_template('results.html', 
                                 results=results, 
                                 lottery_type=lottery_type,
                                 display_name=lottery_type)
        else:
            # Show all results using direct psycopg2 connection
            import psycopg2
            import os
            
            connection_string = os.environ.get('DATABASE_URL')
            results = []
            
            try:
                with psycopg2.connect(connection_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT lottery_type, draw_number, draw_date, numbers, bonus_numbers, divisions, 
                                   rollover_amount, next_jackpot, total_pool_size, total_sales, draw_machine, next_draw_date
                            FROM lottery_result 
                            ORDER BY draw_date DESC 
                            LIMIT 50
                        """)
                        
                        for row in cur.fetchall():
                            # Create a fake LotteryResult object with the required methods
                            result_obj = type('Result', (), {})()
                            result_obj.lottery_type = row[0]
                            result_obj.draw_number = row[1]
                            result_obj.draw_date = row[2]
                            result_obj.numbers = row[3]
                            result_obj.bonus_numbers = row[4]
                            result_obj.divisions = row[5]
                            result_obj.rollover_amount = row[6]
                            result_obj.next_jackpot = row[7]
                            result_obj.total_pool_size = row[8]
                            result_obj.total_sales = row[9]
                            result_obj.draw_machine = row[10]
                            result_obj.next_draw_date = row[11]
                            
                            # Add the required methods
                            def get_numbers_list():
                                if isinstance(result_obj.numbers, str):
                                    try:
                                        return json.loads(result_obj.numbers)
                                    except:
                                        return []
                                return result_obj.numbers or []
                            
                            def get_bonus_numbers_list():
                                if isinstance(result_obj.bonus_numbers, str):
                                    try:
                                        return json.loads(result_obj.bonus_numbers)
                                    except:
                                        return []
                                return result_obj.bonus_numbers or []
                            
                            def get_parsed_divisions():
                                if not result_obj.divisions or result_obj.divisions == '[]':
                                    return []
                                try:
                                    if isinstance(result_obj.divisions, str):
                                        return json.loads(result_obj.divisions)
                                    return result_obj.divisions
                                except:
                                    return []
                            
                            result_obj.get_numbers_list = get_numbers_list
                            result_obj.get_bonus_numbers_list = get_bonus_numbers_list
                            result_obj.get_parsed_divisions = get_parsed_divisions
                            
                            results.append(result_obj)
            except Exception as e:
                logger.error(f"Direct database connection failed: {e}")
                results = []
            
            return render_template('results.html', results=results)
            
    except Exception as e:
        logger.error(f"Results page error: {e}")
        logger.error(traceback.format_exc())
        return render_template('results.html', results=[], lottery_type=lottery_type)

@app.route('/results/<lottery_type>/<int:draw_number>')
def draw_details(lottery_type, draw_number):
    """Display detailed draw results"""
    try:
        # Handle URL encoding
        lottery_type = unquote(lottery_type)
        
        logger.info(f"Created result object: lottery_type={lottery_type}, draw_number={draw_number}, draw_date={result.draw_date if 'result' in locals() else 'N/A'}")
        
        # Get the specific draw
        result = db.session.query(LotteryResult).filter(
            LotteryResult.lottery_type == lottery_type,
            LotteryResult.draw_number == draw_number
        ).first()
        
        if not result:
            flash(f"Draw {draw_number} not found for {lottery_type}", 'error')
            return redirect(url_for('results', lottery_type=lottery_type))
        
        # Create wrapper with additional methods
        draw_result = DrawResult(result)
        
        # Get display name for breadcrumb
        display_name = DISPLAY_NAME_MAPPING.get(lottery_type, lottery_type)
        
        return render_template('draw_details.html', 
                             result=draw_result,
                             display_name=display_name,
                             lottery_type=lottery_type)
        
    except Exception as e:
        logger.error(f"Draw details error: {e}")
        logger.error(traceback.format_exc())
        flash(f"Error loading draw details: {e}", 'error')
        return redirect(url_for('results'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

@app.errorhandler(RateLimitExceeded)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429

# Initialize optional modules
try:
    from lottery_analysis import bp as lottery_analysis_bp
    app.register_blueprint(lottery_analysis_bp)
    logger.info("Lottery analysis routes registered")
except ImportError:
    logger.warning("Lottery analysis module not available")

# Initialize monitoring and health systems
try:
    from health_monitor import init_health_monitor
    from monitoring_dashboard import init_monitoring_dashboard
    from cache_manager import init_cache_manager
    
    init_health_monitor(app, db)
    init_monitoring_dashboard(app, db)
    init_cache_manager(app)
    
    logger.info("Phase 3 monitoring system initialized")
except ImportError as e:
    logger.warning(f"Monitoring system not available: {e}")

# Initialize Phase 4 advanced features
try:
    from internationalization import init_i18n
    from api_integration import init_api_integration
    from predictive_analytics import init_predictive_analytics
    
    init_i18n(app)
    init_api_integration(app)
    init_predictive_analytics(app, db)
    
    logger.info("Phase 4 advanced features initialized")
except ImportError as e:
    logger.warning(f"Advanced features not available: {e}")

logger.info("All modules lazy-loaded successfully")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)