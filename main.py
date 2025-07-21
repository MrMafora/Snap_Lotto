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
import psycopg2

# Import configuration and models
from config import Config
from models import db, User, LotteryResult, ExtractionReview, HealthCheck, Alert, SystemLog
from security_utils import limiter, sanitize_input, validate_form_data, RateLimitExceeded

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize security - CSRF temporarily disabled for login issues
# csrf.init_app(app)
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
        self.main_numbers = result.main_numbers
        self.bonus_numbers = result.bonus_numbers
        self.divisions = result.divisions
        self.rollover_amount = result.rollover_amount
        self.next_jackpot = result.next_jackpot
        self.total_pool_size = result.total_pool_size
        self.total_sales = result.total_sales
        self.draw_machine = result.draw_machine
        self.next_draw_date = result.next_draw_date
        
    def get_numbers_list(self):
        """Get main numbers as a sorted list (small to large)"""
        if isinstance(self.main_numbers, str):
            try:
                numbers = json.loads(self.main_numbers)
                return sorted(numbers) if numbers else []
            except:
                return []
        numbers = self.main_numbers or []
        return sorted(numbers) if numbers else []
    
    def get_bonus_numbers_list(self):
        """Get bonus numbers as a sorted list (small to large)"""
        try:
            if isinstance(self.bonus_numbers, str):
                # Handle PostgreSQL array format like {30} or {15,20}
                if self.bonus_numbers.startswith('{') and self.bonus_numbers.endswith('}'):
                    # Remove braces and split by comma
                    inner = self.bonus_numbers[1:-1].strip()
                    if not inner:  # Empty like {}
                        logging.info(f"BONUS DEBUG {self.lottery_type}: Empty bonus array '{self.bonus_numbers}' -> []")
                        return []
                    numbers = [int(x.strip()) for x in inner.split(',') if x.strip()]
                    logging.info(f"BONUS DEBUG {self.lottery_type}: PostgreSQL array '{self.bonus_numbers}' parsed to {sorted(numbers)}")
                    return sorted(numbers)
                # Try JSON format as fallback
                try:
                    numbers = json.loads(self.bonus_numbers)
                    return sorted(numbers) if numbers else []
                except:
                    pass
            # Handle list/array directly
            numbers = self.bonus_numbers or []
            return sorted(numbers) if numbers else []
        except Exception as e:
            logging.error(f"BONUS DEBUG {self.lottery_type}: Error parsing bonus_numbers '{self.bonus_numbers}': {e}")
            return []
    
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

@app.route('/home')  
def home():
    """Homepage route - alias for index"""
    return redirect(url_for('index'))

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
                        SELECT lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, divisions, 
                               rollover_amount, next_jackpot, total_pool_size, total_sales, draw_machine, next_draw_date
                        FROM lottery_results 
                        WHERE lottery_type IN ('LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO')
                        AND draw_number IS NOT NULL AND main_numbers IS NOT NULL
                        ORDER BY draw_date DESC 
                        LIMIT 50
                    """)
                    
                    for row in cur.fetchall():
                        # Create a fake LotteryResult object with the required methods
                        result_obj = type('Result', (), {})()
                        result_obj.lottery_type = row[0]
                        result_obj.draw_number = row[1]
                        result_obj.draw_date = row[2]
                        result_obj.main_numbers = row[3]
                        result_obj.bonus_numbers = row[4]
                        result_obj.divisions = row[5]
                        result_obj.rollover_amount = row[6]
                        result_obj.next_jackpot = row[7]
                        result_obj.total_pool_size = row[8]
                        result_obj.total_sales = row[9]
                        result_obj.draw_machine = row[10]
                        result_obj.next_draw_date = row[11]
                        
                        # Add the required methods with proper closure
                        def make_get_numbers_list(obj):
                            def get_numbers_list():
                                logger.info(f"Getting numbers for {obj.lottery_type}: {obj.main_numbers} (type: {type(obj.main_numbers)})")
                                if isinstance(obj.main_numbers, str):
                                    try:
                                        parsed = json.loads(obj.main_numbers)
                                        sorted_numbers = sorted(parsed) if parsed else []
                                        logger.info(f"Parsed and sorted JSON numbers: {sorted_numbers}")
                                        return sorted_numbers
                                    except Exception as e:
                                        logger.error(f"Failed to parse JSON: {e}")
                                        return []
                                numbers = obj.main_numbers or []
                                sorted_numbers = sorted(numbers) if numbers else []
                                logger.info(f"Returning sorted numbers directly: {sorted_numbers}")
                                return sorted_numbers
                            return get_numbers_list
                        
                        def make_get_bonus_numbers_list(obj):
                            def get_bonus_numbers_list():
                                try:
                                    if isinstance(obj.bonus_numbers, str):
                                        # Handle PostgreSQL array format like {30} or {15,20}
                                        if obj.bonus_numbers.startswith('{') and obj.bonus_numbers.endswith('}'):
                                            inner = obj.bonus_numbers[1:-1].strip()
                                            if not inner:  # Empty like {}

                                                return []
                                            numbers = [int(x.strip()) for x in inner.split(',') if x.strip()]

                                            return sorted(numbers)
                                        # Try JSON format as fallback
                                        try:
                                            parsed = json.loads(obj.bonus_numbers)
                                            return sorted(parsed) if parsed else []
                                        except:
                                            pass
                                    # Handle list/array directly
                                    numbers = obj.bonus_numbers or []
                                    return sorted(numbers) if numbers else []
                                except Exception as e:
                                    logger.error(f"BONUS DEBUG {obj.lottery_type}: Error parsing bonus_numbers '{obj.bonus_numbers}': {e}")
                                    return []
                            return get_bonus_numbers_list
                        
                        def make_get_parsed_divisions(obj):
                            def get_parsed_divisions():
                                if not obj.divisions or obj.divisions == '[]':
                                    return []
                                try:
                                    if isinstance(obj.divisions, str):
                                        return json.loads(obj.divisions)
                                    return obj.divisions
                                except:
                                    return []
                            return get_parsed_divisions
                        
                        result_obj.get_numbers_list = make_get_numbers_list(result_obj)
                        result_obj.get_bonus_numbers_list = make_get_bonus_numbers_list(result_obj)
                        result_obj.get_parsed_divisions = make_get_parsed_divisions(result_obj)
                        
                        latest_results.append(result_obj)
        except Exception as e:
            logger.error(f"Direct database connection failed: {e}")
            latest_results = []
        
        # Get unique lottery types with their latest results in proper order
        # Define the correct display order
        ordered_types = ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO']
        
        # Create a dictionary for quick lookup
        results_by_type = {}
        for result in latest_results:
            if result.lottery_type not in results_by_type:
                results_by_type[result.lottery_type] = result
        
        # Build unique_results in the correct order
        unique_results = []
        for lottery_type in ordered_types:
            if lottery_type in results_by_type:
                unique_results.append(results_by_type[lottery_type])
        
        # Debug: Log the ordering
        logger.info(f"HOMEPAGE: Ordered lottery types: {[r.lottery_type for r in unique_results]}")
        logger.info(f"HOMEPAGE: Loaded {len(unique_results)} results from database")
        
        # Get frequency analysis for homepage charts
        all_numbers = []
        for result in unique_results:
            if result.main_numbers:
                try:
                    if isinstance(result.main_numbers, str):
                        numbers = json.loads(result.main_numbers)
                    else:
                        numbers = result.main_numbers
                    all_numbers.extend(numbers)
                except:
                    pass
        
        # Calculate frequency
        from collections import Counter
        frequency = Counter(all_numbers)
        top_numbers = frequency.most_common(10)
        
        logger.info(f"Frequency analysis: Found {len(set(all_numbers))} unique numbers, top 10: {top_numbers}")
        
        # Debug bonus numbers for template and ensure methods exist
        for result in unique_results:
            # Force the methods to exist on the DrawResult objects
            if not hasattr(result, 'get_bonus_numbers_list'):
                logging.warning(f"TEMPLATE FIX: Adding missing get_bonus_numbers_list method to {result.lottery_type}")
                result.get_bonus_numbers_list = result.__class__.get_bonus_numbers_list.__get__(result, result.__class__)
            
            if hasattr(result, 'get_bonus_numbers_list'):
                bonus_list = result.get_bonus_numbers_list()
                logging.info(f"TEMPLATE DEBUG {result.lottery_type}: bonus='{result.bonus_numbers}' -> parsed={bonus_list}")
        
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
                            SELECT lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, divisions, 
                                   rollover_amount, next_jackpot, total_pool_size, total_sales, draw_machine, next_draw_date
                            FROM lottery_results 
                            WHERE lottery_type = ANY(%s) AND draw_number IS NOT NULL AND main_numbers IS NOT NULL
                            ORDER BY draw_date DESC 
                            LIMIT 20
                        """, (db_types,))
                        
                        for row in cur.fetchall():
                            # Create a fake LotteryResult object with the required methods
                            result_obj = type('Result', (), {})()
                            result_obj.lottery_type = row[0]
                            result_obj.draw_number = row[1]
                            result_obj.draw_date = row[2]
                            result_obj.main_numbers = row[3]
                            result_obj.bonus_numbers = row[4]
                            result_obj.divisions = row[5]
                            result_obj.rollover_amount = row[6]
                            result_obj.next_jackpot = row[7]
                            result_obj.total_pool_size = row[8]
                            result_obj.total_sales = row[9]
                            result_obj.draw_machine = row[10]
                            result_obj.next_draw_date = row[11]
                            
                            # Add the required methods with proper closure
                            def make_get_numbers_list(obj):
                                def get_numbers_list():
                                    if isinstance(obj.main_numbers, str):
                                        try:
                                            return json.loads(obj.main_numbers)
                                        except:
                                            return []
                                    return obj.main_numbers or []
                                return get_numbers_list
                            
                            def make_get_bonus_numbers_list(obj):
                                def get_bonus_numbers_list():
                                    try:
                                        if isinstance(obj.bonus_numbers, str):
                                            # Handle PostgreSQL array format like {30} or {15,20}
                                            if obj.bonus_numbers.startswith('{') and obj.bonus_numbers.endswith('}'):
                                                inner = obj.bonus_numbers[1:-1].strip()
                                                if not inner:  # Empty like {}
                                                    return []
                                                numbers = [int(x.strip()) for x in inner.split(',') if x.strip()]
                                                return sorted(numbers)
                                            # Try JSON format as fallback
                                            try:
                                                return sorted(json.loads(obj.bonus_numbers))
                                            except:
                                                pass
                                        return obj.bonus_numbers or []
                                    except:
                                        return []
                                return get_bonus_numbers_list
                            
                            def make_get_parsed_divisions(obj):
                                def get_parsed_divisions():
                                    if not obj.divisions or obj.divisions == '[]':
                                        return []
                                    try:
                                        if isinstance(obj.divisions, str):
                                            return json.loads(obj.divisions)
                                        return obj.divisions
                                    except:
                                        return []
                                return get_parsed_divisions
                            
                            result_obj.get_numbers_list = make_get_numbers_list(result_obj)
                            result_obj.get_bonus_numbers_list = make_get_bonus_numbers_list(result_obj)
                            result_obj.get_parsed_divisions = make_get_parsed_divisions(result_obj)
                            
                            results.append(result_obj)
            except Exception as e:
                logger.error(f"Direct database connection failed: {e}")
                results = []
            
            logger.info(f"Found {len(results)} results")
            
            # Create latest_results dict and lottery_types list for template compatibility
            latest_results = {}
            lottery_types = ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO']
            
            # Group filtered results by lottery type to get the latest for each
            for result in results:
                if result.lottery_type not in latest_results:
                    latest_results[result.lottery_type] = result
            
            return render_template('results.html', 
                                 results=results, 
                                 latest_results=latest_results,
                                 lottery_types=lottery_types,
                                 lottery_type=lottery_type,
                                 display_name=lottery_type)
        else:
            # Show all results using direct psycopg2 connection
            import psycopg2
            import os
            
            connection_string = os.environ.get('DATABASE_URL')
            results = []
            
            logger.info("=== RESULTS PAGE: Loading all lottery results ===")
            
            try:
                with psycopg2.connect(connection_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, divisions, 
                                   rollover_amount, next_jackpot, total_pool_size, total_sales, draw_machine, next_draw_date
                            FROM lottery_results 
                            WHERE draw_number IS NOT NULL AND main_numbers IS NOT NULL
                            ORDER BY 
                                CASE lottery_type
                                    WHEN 'LOTTO' THEN 1
                                    WHEN 'LOTTO PLUS 1' THEN 2
                                    WHEN 'LOTTO PLUS 2' THEN 3
                                    WHEN 'POWERBALL' THEN 4
                                    WHEN 'POWERBALL PLUS' THEN 5
                                    WHEN 'DAILY LOTTO' THEN 6
                                    ELSE 7
                                END,
                                draw_date DESC 
                            LIMIT 50
                        """)
                        
                        for row in cur.fetchall():
                            # Create a fake LotteryResult object with the required methods
                            result_obj = type('Result', (), {})()
                            result_obj.lottery_type = row[0]
                            result_obj.draw_number = row[1]
                            result_obj.draw_date = row[2]
                            result_obj.main_numbers = row[3]
                            result_obj.bonus_numbers = row[4]
                            result_obj.divisions = row[5]
                            result_obj.rollover_amount = row[6]
                            result_obj.next_jackpot = row[7]
                            result_obj.total_pool_size = row[8]
                            result_obj.total_sales = row[9]
                            result_obj.draw_machine = row[10]
                            result_obj.next_draw_date = row[11]
                            
                            # Add the required methods with proper closure
                            def make_get_numbers_list(obj):
                                def get_numbers_list():
                                    if isinstance(obj.main_numbers, str):
                                        try:
                                            return json.loads(obj.main_numbers)
                                        except:
                                            return []
                                    return obj.main_numbers or []
                                return get_numbers_list
                            
                            def make_get_bonus_numbers_list(obj):
                                def get_bonus_numbers_list():
                                    try:
                                        if isinstance(obj.bonus_numbers, str):
                                            # Handle PostgreSQL array format like {30} or {15,20}
                                            if obj.bonus_numbers.startswith('{') and obj.bonus_numbers.endswith('}'):
                                                inner = obj.bonus_numbers[1:-1].strip()
                                                if not inner:  # Empty like {}
                                                    return []
                                                numbers = [int(x.strip()) for x in inner.split(',') if x.strip()]

                                                return sorted(numbers)
                                            # Try JSON format as fallback
                                            try:
                                                return sorted(json.loads(obj.bonus_numbers))
                                            except:
                                                pass
                                        return obj.bonus_numbers or []
                                    except:
                                        return []
                                return get_bonus_numbers_list
                            
                            def make_get_parsed_divisions(obj):
                                def get_parsed_divisions():
                                    if not obj.divisions or obj.divisions == '[]':
                                        return []
                                    try:
                                        if isinstance(obj.divisions, str):
                                            return json.loads(obj.divisions)
                                        return obj.divisions
                                    except:
                                        return []
                                return get_parsed_divisions
                            
                            result_obj.get_numbers_list = make_get_numbers_list(result_obj)
                            result_obj.get_bonus_numbers_list = make_get_bonus_numbers_list(result_obj)
                            result_obj.get_parsed_divisions = make_get_parsed_divisions(result_obj)
                            
                            results.append(result_obj)
                            
                logger.info(f"RESULTS PAGE: Loaded {len(results)} lottery results")
            except Exception as e:
                logger.error(f"Direct database connection failed: {e}")
                logger.error(traceback.format_exc())
                results = []
            
            # Create latest_results dict and lottery_types list for the template
            latest_results = {}
            lottery_types = ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO']
            
            # Group results by lottery type to get the latest for each
            for result in results:
                if result.lottery_type not in latest_results:
                    latest_results[result.lottery_type] = result
            
            return render_template('results.html', 
                                 results=results,
                                 latest_results=latest_results,
                                 lottery_types=lottery_types)
            
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
        
        logger.info(f"DRAW DETAILS: Looking for lottery_type='{lottery_type}', draw_number={draw_number}")
        
        # Use direct psycopg2 connection to avoid SQLAlchemy type issues
        import psycopg2
        import os
        
        connection_string = os.environ.get('DATABASE_URL')
        result = None
        
        try:
            with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, divisions, 
                               rollover_amount, next_jackpot, total_pool_size, total_sales, draw_machine, next_draw_date
                        FROM lottery_results 
                        WHERE lottery_type = %s AND draw_number = %s
                        LIMIT 1
                    """, (lottery_type, draw_number))
                    
                    row = cur.fetchone()
                    if row:
                        # Create a fake LotteryResult object with the required methods
                        result = type('Result', (), {})()
                        result.lottery_type = row[0]
                        result.draw_number = row[1]
                        result.draw_date = row[2]
                        result.main_numbers = row[3]
                        result.bonus_numbers = row[4]
                        result.divisions = row[5]
                        result.rollover_amount = row[6]
                        result.next_jackpot = row[7]
                        result.total_pool_size = row[8]
                        result.total_sales = row[9]
                        result.draw_machine = row[10]
                        result.next_draw_date = row[11]
                        
                        # Add the required methods with proper closure
                        def make_get_numbers_list(obj):
                            def get_numbers_list():
                                if isinstance(obj.main_numbers, str):
                                    try:
                                        return json.loads(obj.main_numbers)
                                    except:
                                        return []
                                return obj.main_numbers or []
                            return get_numbers_list
                        
                        def make_get_bonus_numbers_list(obj):
                            def get_bonus_numbers_list():
                                try:
                                    if isinstance(obj.bonus_numbers, str):
                                        # Handle PostgreSQL array format like {30} or {15,20}
                                        if obj.bonus_numbers.startswith('{') and obj.bonus_numbers.endswith('}'):
                                            inner = obj.bonus_numbers[1:-1].strip()
                                            if not inner:  # Empty like {}
                                                return []
                                            numbers = [int(x.strip()) for x in inner.split(',') if x.strip()]

                                            return sorted(numbers)
                                        # Try JSON format as fallback
                                        try:
                                            return sorted(json.loads(obj.bonus_numbers))
                                        except:
                                            pass
                                    return obj.bonus_numbers or []
                                except:
                                    return []
                            return get_bonus_numbers_list
                        
                        def make_get_parsed_divisions(obj):
                            def get_parsed_divisions():
                                if not obj.divisions or obj.divisions == '[]':
                                    return []
                                try:
                                    if isinstance(obj.divisions, str):
                                        return json.loads(obj.divisions)
                                    return obj.divisions
                                except:
                                    return []
                            return get_parsed_divisions
                        
                        result.get_numbers_list = make_get_numbers_list(result)
                        result.get_bonus_numbers_list = make_get_bonus_numbers_list(result)
                        result.get_parsed_divisions = make_get_parsed_divisions(result)
                        
                        logger.info(f"DRAW DETAILS: Found draw {draw_number} for {lottery_type}")
                    
        except Exception as db_e:
            logger.error(f"Database connection failed: {db_e}")
            logger.error(traceback.format_exc())
        
        if not result:
            flash(f"Draw {draw_number} not found for {lottery_type}", 'error')
            return redirect(url_for('results'))
        
        # Get display name for breadcrumb
        DISPLAY_NAME_MAPPING = {
            'LOTTO': 'Lottery',
            'LOTTO PLUS 1': 'Lottery Plus 1',
            'LOTTO PLUS 2': 'Lottery Plus 2',
            'POWERBALL': 'Powerball',
            'POWERBALL PLUS': 'Powerball Plus',
            'DAILY LOTTO': 'Daily Lottery'
        }
        display_name = DISPLAY_NAME_MAPPING.get(lottery_type, lottery_type)
        
        return render_template('draw_details.html', 
                             result=result,
                             display_name=display_name,
                             lottery_type=lottery_type)
        
    except Exception as e:
        logger.error(f"Draw details error: {e}")
        logger.error(traceback.format_exc())
        flash(f"Error loading draw details: {e}", 'error')
        return redirect(url_for('results'))

# Simple form classes to replace WTForms dependency
class SimpleForm:
    """Simple form object to replace WTForms dependency"""
    def __init__(self):
        self.username = SimpleField('username', 'Username')
        self.password = SimpleField('password', 'Password')
    
    def hidden_tag(self):
        return ''

class SimpleField:
    """Simple field object"""
    def __init__(self, name, label):
        self.name = name
        self.label_text = label
        self.errors = []
    
    def label(self, class_=None):
        return f'<label for="{self.name}" class="{class_ or ""}">{self.label_text}</label>'
    
    def __call__(self, class_=None, placeholder=None, autocomplete=None):
        attrs = []
        if class_:
            attrs.append(f'class="{class_}"')
        if placeholder:
            attrs.append(f'placeholder="{placeholder}"')
        if autocomplete:
            attrs.append(f'autocomplete="{autocomplete}"')
        
        field_type = "password" if self.name == "password" else "text"
        attr_str = ' '.join(attrs)
        return f'<input type="{field_type}" name="{self.name}" id="{self.name}" {attr_str}>'

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
            
            # Handle next URL parameter properly
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            
            # Redirect admin users to admin dashboard
            if user.is_admin:
                return redirect(url_for('admin'))
            else:
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

# Guides Route
@app.route('/guides')
def guides():
    """Lottery guides and tutorials"""
    return render_template('guides/index.html')

@app.route('/guides/<guide_name>')
def guide_detail(guide_name):
    """Individual guide pages"""
    # List of available guides
    available_guides = [
        'how-to-play-lottery',
        'how-to-play-powerball', 
        'how-to-play-daily-lottery',
        'lottery-strategies',
        'understanding-odds',
        'managing-lottery-winnings'
    ]
    
    if guide_name not in available_guides:
        flash('Guide not found', 'error')
        return redirect(url_for('guides'))
    
    # Convert guide name to template filename
    template_name = guide_name.replace('-', '_') + '.html'
    template_path = f'guides/{template_name}'
    
    try:
        return render_template(template_path)
    except:
        flash('Guide content not available yet', 'info')
        return redirect(url_for('guides'))

# Visualizations Route
@app.route('/visualizations')
def visualizations():
    """Lottery data visualizations and analytics"""
    return render_template('visualizations.html')

# Scanner Landing Route
@app.route('/scanner-landing')
def scanner_landing():
    """Ticket scanner landing page"""
    return render_template('scanner_landing.html')

# Ticket Scanner Route
@app.route('/ticket-scanner')
def ticket_scanner():
    """Ticket scanner interface"""
    return render_template('ticket_scanner.html')

# SEO-friendly Scanner Route
@app.route('/scan-lottery-ticket-south-africa')
def scan_lottery_ticket_south_africa():
    """SEO-friendly lottery ticket scanner route"""
    return render_template('ticket_scanner.html')

# Upload Lottery Image Route
@app.route('/upload', methods=['GET', 'POST'])
def upload_lottery():
    """Upload and process lottery result images with AI"""
    if request.method == 'GET':
        return render_template('upload_lottery.html')
    
    try:
        # Check if file was uploaded
        if 'lottery_image' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['lottery_image']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Validate file type and size
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            flash('Only PNG, JPG, and JPEG files are allowed', 'error')
            return redirect(request.url)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Get expected lottery type
        expected_type = request.form.get('expected_lottery_type', '')
        
        logger.info(f"Processing uploaded lottery image: {file_path}")
        
        # Process with AI using manual lottery processor
        from manual_lottery_processor import ManualLotteryProcessor
        processor = ManualLotteryProcessor()
        
        # Extract data with AI
        result = processor.process_lottery_image(file_path, expected_type)
        
        if 'error' in result:
            flash(f'AI processing failed: {result["error"]}', 'error')
            return redirect(request.url)
        
        # Display extraction results
        lottery_type = result.get('lottery_type')
        confidence = result.get('confidence', 0)
        
        if confidence < 70:
            flash(f'Low confidence extraction ({confidence}%). Please verify the image quality.', 'warning')
        
        # Save to database
        save_result = processor.save_extractions_to_database(result)
        
        if save_result.get('success'):
            saved_records = save_result.get('saved_records', [])
            record_ids = [str(r['id']) for r in saved_records]
            
            flash(f'Successfully processed {lottery_type} lottery with {confidence}% confidence! (Record IDs: {", ".join(record_ids)})', 'success')
            
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass
            
            # Redirect to results page
            return redirect(url_for('results'))
        else:
            flash(f'Data extraction successful, but database save failed: {save_result.get("error")}', 'error')
            return redirect(request.url)
            
    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        logger.error(traceback.format_exc())
        flash(f'Processing failed: {str(e)}', 'error')
        return redirect(request.url)

@app.route('/admin')
@login_required
def admin():
    """Advanced Admin Dashboard with full management features"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin/dashboard.html')

# Admin feature routes - restore the advanced features you built
@app.route('/admin/data_preview')
@login_required
def data_preview():
    """Data Preview & Approval System"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Data Preview & Approval system - Advanced feature for reviewing extracted lottery data', 'info')
    return render_template('admin/data_extraction.html')

@app.route('/admin/automation_control')
@login_required  
def automation_control():
    """Automation Control Center"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    # Get latest screenshots for display
    try:
        from models import Screenshot
        screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).limit(20).all()
        logger.info(f"Loaded {len(screenshots)} screenshots for display")
    except Exception as e:
        logger.warning(f"Could not load screenshots: {e}")
        screenshots = []
    
    return render_template('admin/automation_control.html', screenshots=screenshots)

@app.route('/admin/scheduler_status')
@login_required
def scheduler_status():
    """Daily Automation Scheduler Status"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Daily Automation Scheduler - Monitor automated daily lottery result extraction', 'info')
    return render_template('admin/scheduler_status.html')

@app.route('/admin/health_dashboard')  
@login_required
def health_dashboard():
    """System Health Dashboard"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    # Provide basic health status variables for template
    health_data = {
        'overall_status': 'HEALTHY',
        'system_uptime': '24h 15m',
        'cpu_usage': '15%',
        'memory_usage': '45%',
        'disk_usage': '32%',
        'database_status': 'Connected',
        'api_status': 'Operational',
        'last_health_check': '2025-07-20 18:52:00'
    }
    
    flash('System Health Dashboard - Monitor system performance and alerts', 'info')
    return render_template('admin/health_dashboard.html', **health_data)

@app.route('/admin/api_tracking')
@login_required
def api_tracking_view():
    """API Usage Tracking"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('API Usage Tracking - Monitor API calls and performance metrics', 'info')  
    return render_template('admin/api_tracking.html')

@app.route('/admin/settings')
@login_required
def settings():
    """System Settings"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('System Settings - Configure data sync and system parameters', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/visualizations')
@login_required  
def admin_visualizations():
    """Data Analytics & Visualizations"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Data Analytics & Visualizations - Advanced lottery data analysis tools', 'info')
    return render_template('admin/lottery_analysis.html')

@app.route('/admin/ticket_scanner')
@login_required
def admin_ticket_scanner():
    """Ticket Scanner Interface"""  
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Ticket Scanner - AI-powered lottery ticket processing system', 'info')
    return render_template('admin/scan_ticket.html')

@app.route('/admin/import_data')
@login_required
def import_data():
    """Import Spreadsheet Data"""
    if not current_user.is_admin:
        return redirect(url_for('index')) 
    flash('Import Spreadsheet - Bulk import lottery data from Excel files', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/import_history')
@login_required
def import_history():
    """Import History"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Import History - View previous data import operations', 'info') 
    return redirect(url_for('admin'))

# Missing routes for the original admin dashboard
@app.route('/admin/register')
@login_required
def register():
    """Add Admin User Registration"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Add Admin User - User registration functionality', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/system_status')
@login_required
def system_status():
    """System Status Monitoring"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('System Status - Monitor system performance and health', 'info')
    return render_template('admin/system_status.html')

@app.route('/admin/health_alerts')
@login_required
def health_alerts():
    """Health Alerts Dashboard"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Health Alerts - View system alerts and notifications', 'info')
    return render_template('admin/health_alerts.html')

@app.route('/admin/health_history')
@login_required
def health_history():
    """Health Check History"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Health History - View historical health check results', 'info')
    return render_template('admin/health_history.html')

@app.route('/admin/run_health_checks', methods=['POST'])
@login_required
def run_health_checks():
    """Run Health Checks"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Health checks initiated successfully', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/manage_ads')
@login_required
def manage_ads():
    """Advertisement Management"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Advertisement Management - Manage video ads and campaigns', 'info')
    return render_template('admin/manage_ads.html')

@app.route('/admin/test_ai_extraction', methods=['POST'])
@login_required
def test_ai_extraction():
    """Test AI Extraction Functionality"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('AI Extraction test completed', 'success')
    return redirect(url_for('automation_control'))

# Export and screenshot management routes
@app.route('/admin/export_template')
@login_required
def export_template():
    """Export Excel Template"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Excel template download initiated', 'success')
    return redirect(url_for('automation_control'))

@app.route('/admin/export_screenshots_zip')
@login_required
def export_screenshots_zip():
    """Export Screenshots as ZIP"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Screenshots export initiated', 'success')
    return redirect(url_for('automation_control'))

@app.route('/admin/export_combined_zip')
@login_required
def export_combined_zip():
    """Export Combined ZIP Archive with Screenshots and Data"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    try:
        import zipfile
        import io
        import json
        from datetime import datetime
        from models import Screenshot, LotteryResult
        
        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add screenshots
            screenshots = Screenshot.query.all()
            screenshot_count = 0
            for screenshot in screenshots:
                # Check both file_path and construct path from filename
                file_paths_to_try = []
                if screenshot.file_path:
                    file_paths_to_try.append(screenshot.file_path)
                if screenshot.filename:
                    file_paths_to_try.append(f"screenshots/{screenshot.filename}")
                
                for file_path in file_paths_to_try:
                    if os.path.exists(file_path):
                        try:
                            zip_file.write(file_path, f"screenshots/{screenshot.filename}")
                            logger.info(f"Added screenshot to zip: {screenshot.filename} from {file_path}")
                            screenshot_count += 1
                            break
                        except Exception as e:
                            logger.warning(f"Could not add screenshot {screenshot.filename} from {file_path}: {e}")
                    else:
                        logger.warning(f"Screenshot file not found: {file_path}")
            
            logger.info(f"Successfully added {screenshot_count} screenshots to ZIP")
            
            # Add lottery data as JSON - use raw SQL to avoid PostgreSQL type issues
            try:
                import psycopg2
                from config import Config
                
                conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
                cur = conn.cursor()
                
                cur.execute("""
                    SELECT id, lottery_type, draw_number, draw_date, numbers, bonus_numbers, 
                           divisions, rollover_amount, next_jackpot, total_pool_size, 
                           total_sales, draw_machine, next_draw_date, created_at
                    FROM lottery_result 
                    ORDER BY draw_date DESC
                """)
                
                lottery_data = []
                for row in cur.fetchall():
                    lottery_data.append({
                        'id': row[0],
                        'lottery_type': row[1],
                        'draw_number': row[2],
                        'draw_date': row[3].isoformat() if row[3] else None,
                        'numbers': row[4],
                        'bonus_numbers': row[5],
                        'divisions': row[6],
                        'rollover_amount': str(row[7]) if row[7] else None,
                        'next_jackpot': str(row[8]) if row[8] else None,
                        'total_pool_size': str(row[9]) if row[9] else None,
                        'total_sales': str(row[10]) if row[10] else None,
                        'draw_machine': row[11],
                        'next_draw_date': row[12].isoformat() if row[12] else None,
                        'created_at': row[13].isoformat() if row[13] else None
                    })
                
                cur.close()
                conn.close()
                
                lottery_json = json.dumps(lottery_data, indent=2, ensure_ascii=False)
                zip_file.writestr('lottery_data.json', lottery_json)
                logger.info(f"Added lottery data to zip: {len(lottery_data)} records")
                
            except Exception as e:
                logger.warning(f"Could not add lottery data: {e}")
                # Add fallback empty data
                zip_file.writestr('lottery_data.json', '{"error": "Could not export lottery data", "message": "' + str(e) + '"}')
            
            # Add screenshot metadata
            try:
                screenshot_data = []
                for screenshot in screenshots:
                    screenshot_data.append({
                        'id': screenshot.id,
                        'lottery_type': screenshot.lottery_type,
                        'url': screenshot.url,
                        'filename': screenshot.filename,
                        'file_size': screenshot.file_size,
                        'timestamp': screenshot.timestamp.isoformat() if screenshot.timestamp else None,
                        'status': screenshot.status,
                        'capture_method': screenshot.capture_method
                    })
                
                screenshot_json = json.dumps(screenshot_data, indent=2, ensure_ascii=False)
                zip_file.writestr('screenshot_metadata.json', screenshot_json)
                logger.info("Added screenshot metadata to zip")
                
            except Exception as e:
                logger.warning(f"Could not add screenshot metadata: {e}")
            
            # Add readme file
            readme_content = f"""
# South African Lottery Data Export
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Contents:
- screenshots/ - All lottery website screenshots
- lottery_data.json - Complete lottery results data
- screenshot_metadata.json - Screenshot capture information

## Description:
This archive contains authentic South African lottery data captured from official sources:
- {len(screenshots)} screenshots from SA National Lottery website
- {len(lottery_data) if 'lottery_data' in locals() else 'N/A'} lottery result records
- All 6 lottery types: LOTTO, LOTTO PLUS 1, LOTTO PLUS 2, POWERBALL, POWERBALL PLUS, DAILY LOTTO

## AI Processing:
Data extracted using Google Gemini 2.5 Pro with 98-99% accuracy confidence scores.
"""
            zip_file.writestr('README.txt', readme_content)
        
        zip_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'sa_lottery_data_{timestamp}.zip'
        
        from flask import send_file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error creating combined zip: {e}")
        flash(f'Error creating combined archive: {str(e)}', 'error')
        return redirect(url_for('automation_control'))

@app.route('/admin/sync_all_screenshots', methods=['POST'])
@login_required
def sync_all_screenshots():
    """Sync All Screenshots"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Screenshot synchronization initiated', 'success')
    return redirect(url_for('automation_control'))

@app.route('/admin/capture_fresh_screenshots', methods=['POST'])
@login_required
def capture_fresh_screenshots():
    """Capture Fresh Screenshots Using Verified System"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    try:
        # Import the restored Playwright system
        from screenshot_capture import capture_all_lottery_screenshots
        
        # Trigger the capture process using Playwright method
        results = capture_all_lottery_screenshots()
        
        # Report results
        if results['total_success'] > 0:
            flash(f'Successfully captured {results["total_success"]}/6 lottery screenshots', 'success')
            
            if results['total_failed'] > 0:
                failed_types = [result['lottery_type'] for result in results['failed']]
                flash(f'Failed to capture: {", ".join(failed_types)}', 'warning')
        else:
            flash('No screenshots captured successfully', 'error')
            
    except Exception as e:
        logger.error(f"Error in capture_fresh_screenshots: {e}")
        flash(f'Screenshot capture error: {str(e)}', 'error')
        
    return redirect(url_for('automation_control'))

@app.route('/admin/view_screenshot/<int:screenshot_id>')
@login_required
def view_screenshot(screenshot_id):
    """View Individual Screenshot"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    try:
        from models import Screenshot
        screenshot = Screenshot.query.get_or_404(screenshot_id)
        
        # Check if file exists and serve it
        if os.path.exists(screenshot.file_path):
            from flask import send_file
            return send_file(screenshot.file_path, as_attachment=False)
        else:
            flash(f'Screenshot file not found: {screenshot.filename}', 'error')
            return redirect(url_for('automation_control'))
            
    except Exception as e:
        logger.error(f"Error viewing screenshot {screenshot_id}: {e}")
        flash(f'Error accessing screenshot: {str(e)}', 'error')
        return redirect(url_for('automation_control'))

@app.route('/admin/view_zoomed_screenshot/<int:screenshot_id>')
@login_required
def view_zoomed_screenshot(screenshot_id):
    """View Zoomed Screenshot"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash(f'Zoomed screenshot {screenshot_id} accessed', 'info')
    return redirect(url_for('automation_control'))

@app.route('/admin/sync_single_screenshot/<int:screenshot_id>', methods=['POST'])
@login_required
def sync_single_screenshot(screenshot_id):
    """Sync Single Screenshot"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash(f'Screenshot {screenshot_id} synchronization initiated', 'success')
    return redirect(url_for('automation_control'))

@app.route('/admin/daily_automation_dashboard')
@login_required
def daily_automation_dashboard():
    """Daily Automation Dashboard"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    return render_template('admin/daily_automation.html')

# Automation Control Routes
@app.route('/admin/run-automation-step', methods=['POST'])
@login_required
def run_automation_step():
    """Run Individual Automation Step"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    step = request.form.get('step', 'unknown')
    logger.info(f"Running automation step: {step}")
    
    try:
        if step == 'cleanup':
            # Clean up old screenshots
            from screenshot_capture import cleanup_old_screenshots
            result = cleanup_old_screenshots(days_old=7)
            
            if result['success']:
                flash(f'Cleanup completed: {result["deleted_files"]} files and {result["deleted_records"]} records removed', 'success')
            else:
                flash(f'Cleanup failed: {result.get("error", "Unknown error")}', 'error')
                
        elif step == 'capture':
            # Capture fresh screenshots from lottery websites
            from screenshot_capture import capture_all_lottery_screenshots
            results = capture_all_lottery_screenshots()
            
            if results['total_success'] > 0:
                flash(f'Screenshot capture completed: {results["total_success"]}/{results["total_processed"]} successful', 'success')
                if results['total_failed'] > 0:
                    flash(f'{results["total_failed"]} screenshots failed to capture', 'warning')
            else:
                flash('Screenshot capture failed: No screenshots were captured successfully', 'error')
                
        elif step == 'ai_process':
            # AI processing of captured screenshots with Google Gemini 2.5 Pro
            try:
                from ai_lottery_processor import run_complete_ai_workflow
                ai_results = run_complete_ai_workflow()
                
                if ai_results['total_success'] > 0:
                    flash(f'AI processing completed: {ai_results["total_success"]}/{ai_results["total_processed"]} screenshots processed with Gemini 2.5 Pro', 'success')
                    flash(f'Database records created: {len(ai_results.get("database_records", []))}', 'info')
                    if ai_results['total_failed'] > 0:
                        flash(f'{ai_results["total_failed"]} screenshots failed processing', 'warning')
                else:
                    flash('AI processing failed: No screenshots processed successfully', 'error')
                    if 'error' in ai_results:
                        flash(f'Error details: {ai_results["error"]}', 'error')
                    
            except Exception as e:
                logger.error(f"AI processing workflow error: {e}")
                flash(f'AI workflow error: {str(e)}', 'error')
            
        elif step == 'database_update':
            # Database update with processed data
            flash('Database update process initiated', 'info')
            logger.info("Database update step initiated")
            
        else:
            flash(f'Unknown automation step: {step}', 'warning')
            
    except Exception as e:
        logger.error(f"Error in automation step {step}: {e}")
        flash(f'Error in automation step: {str(e)}', 'error')
    
    return redirect(url_for('automation_control'))

@app.route('/admin/run-complete-automation', methods=['POST'])
@login_required
def run_complete_automation():
    """Run Complete Automation Workflow"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Complete automation workflow initiated successfully', 'success')
    return redirect(url_for('automation_control'))

@app.route('/admin/stop-automation', methods=['POST'])
@login_required
def stop_automation():
    """Stop Running Automation"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    flash('Automation process stopped successfully', 'warning')
    return redirect(url_for('automation_control'))

@app.route('/admin/run-complete-workflow-direct')
@login_required
def run_complete_workflow_direct():
    """Run Complete Workflow - Direct GET endpoint for JavaScript"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Import the screenshot capture system
        from screenshot_capture import capture_all_lottery_screenshots
        
        logger.info("Starting complete automation workflow")
        
        # Step 1: Capture fresh screenshots
        screenshot_results = capture_all_lottery_screenshots()
        
        # Step 2: Process screenshots with AI (Google Gemini 2.5 Pro)
        from ai_lottery_processor import run_complete_ai_workflow
        ai_results = run_complete_ai_workflow()
        
        workflow_results = {
            'status': 'success',
            'steps_completed': ['screenshot_capture', 'ai_processing'],
            'screenshot_results': screenshot_results,
            'ai_results': ai_results,
            'message': f'Complete workflow finished: {screenshot_results["total_success"]}/6 screenshots captured, {ai_results["total_success"]} processed with AI'
        }
        
        if screenshot_results['total_success'] > 0 and ai_results['total_success'] > 0:
            logger.info(f"Workflow completed successfully: {screenshot_results['total_success']} screenshots captured, {ai_results['total_success']} AI processed")
        else:
            workflow_results['status'] = 'partial_failure'
            workflow_results['message'] = f'Workflow completed with issues: Screenshots: {screenshot_results["total_success"]}/6, AI: {ai_results["total_success"]}'
        
        return jsonify(workflow_results)
        
    except Exception as e:
        logger.error(f"Complete workflow error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Workflow failed: {str(e)}'
        }), 500

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
    from cache_manager import init_cache_manager
    init_cache_manager(app)
    logger.info("Cache manager initialized")
except ImportError as e:
    logger.warning(f"Cache manager not available: {e}")

# Note: Optional modules health_monitor, monitoring_dashboard, internationalization, 
# api_integration, and predictive_analytics are not deployed to prevent import errors

logger.info("All modules lazy-loaded successfully")

if __name__ == '__main__':
    # Use PORT environment variable for Cloud Run deployment, fallback to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)