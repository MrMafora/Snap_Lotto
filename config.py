"""
Configuration settings for the South African Lottery Scanner application.
"""

import os
from datetime import timedelta

class Config:
    """Application configuration settings"""
    
    # Environment and Debug Settings
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')  # 'development' or 'production'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Security Settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'lottery-scraper-default-secret')
    SESSION_COOKIE_SECURE = ENVIRONMENT == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///lottery.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,  # Reduced pool size to prevent too many connections
        "max_overflow": 10,  # Reduced max overflow
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 30
    }
    
    # API Keys
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY', '')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # Default lottery URLs for scraping
    DEFAULT_LOTTERY_URLS = [
        'https://www.nationallottery.co.za/lotto-history',
        'https://www.nationallottery.co.za/lotto-plus-1-history',
        'https://www.nationallottery.co.za/lotto-plus-2-history',
        'https://www.nationallottery.co.za/powerball-history',
        'https://www.nationallottery.co.za/powerball-plus-history',
        'https://www.nationallottery.co.za/daily-lotto-history'
    ]
    
    # Results URLs for current data
    RESULTS_URLS = [
        {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
        {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
        {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
        {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
    ]
    
    # Automation Settings
    AUTOMATION_ENABLED = os.environ.get('AUTOMATION_ENABLED', 'True').lower() == 'true'
    DEFAULT_HOUR = 1  # 1 AM
    DEFAULT_MINUTE = 0
    
    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "100 per day;10 per hour"
    
    # Caching
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Monitoring
    HEALTH_CHECK_INTERVAL = 300  # 5 minutes
    LOG_RETENTION_DAYS = 30
    
    # Internationalization
    LANGUAGES = ['en', 'af']  # English and Afrikaans
    DEFAULT_LANGUAGE = 'en'
    
    # API Settings
    API_RATE_LIMIT = "5 per minute"
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        
        # Create required directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
        
        # Set up logging for production
        if Config.ENVIRONMENT == 'production':
            import logging
            from logging.handlers import RotatingFileHandler
            
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler('logs/lottery_app.log', maxBytes=10240000, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Lottery Scanner application startup')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set to True for SQL debugging

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Production-specific settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
        "pool_timeout": 60
    }

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}