"""
Production Configuration and Optimization
Phase 3 Implementation - Production-ready settings
"""

import os
import logging
from datetime import timedelta

class ProductionConfig:
    """Production-optimized configuration"""
    
    # Security Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-change-me'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Session Security
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 30,
        "connect_args": {"sslmode": "require"}
    }
    
    # Caching Configuration
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # File Upload Security
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif']
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Logging Configuration
    LOG_LEVEL = logging.INFO
    LOG_FILE = 'logs/production.log'
    
    # Performance Settings
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=30)  # Static file caching
    
    # API Configuration
    API_RATE_LIMIT = {
        'scan_ticket': '5 per minute',
        'frequency_analysis': '20 per minute', 
        'general': '100 per hour'
    }
    
    # Monitoring Settings
    MONITORING_ENABLED = True
    HEALTH_CHECK_INTERVAL = 60  # seconds
    ALERT_EMAIL = os.environ.get('ALERT_EMAIL')
    
    # Google Gemini Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = 'gemini-2.5-pro'
    GEMINI_TIMEOUT = 30
    
    @staticmethod
    def init_app(app):
        """Initialize production settings"""
        # Set up logging
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        logging.basicConfig(
            level=ProductionConfig.LOG_LEVEL,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
            handlers=[
                logging.FileHandler(ProductionConfig.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
        # Security headers
        @app.after_request
        def security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            return response

class DevelopmentConfig:
    """Development configuration"""
    
    DEBUG = True
    SECRET_KEY = 'dev-secret-key'
    WTF_CSRF_ENABLED = True
    
    # Less strict session settings for development
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///lottery_dev.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Caching disabled for development
    CACHE_TYPE = "null"
    
    # Logging
    LOG_LEVEL = logging.DEBUG
    
    @staticmethod
    def init_app(app):
        """Initialize development settings"""
        logging.basicConfig(level=logging.DEBUG)

class TestingConfig:
    """Testing configuration"""
    
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False  # Disable for easier testing
    
    # In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Disable caching for testing
    CACHE_TYPE = "null"
    
    @staticmethod
    def init_app(app):
        """Initialize testing settings"""
        logging.disable(logging.CRITICAL)

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get appropriate configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    @staticmethod
    def optimize_database_queries():
        """Database query optimization recommendations"""
        return {
            'indexes_to_add': [
                'CREATE INDEX IF NOT EXISTS idx_lottery_results_created_at ON lottery_results(created_at DESC)',
                'CREATE INDEX IF NOT EXISTS idx_health_check_timestamp ON health_check_history(timestamp DESC)',
                'CREATE INDEX IF NOT EXISTS idx_api_request_timestamp ON api_request_log(timestamp DESC)'
            ],
            'maintenance_queries': [
                'ANALYZE lottery_results',
                'VACUUM ANALYZE',
                'REINDEX INDEX idx_lottery_results_type_date'
            ]
        }
    
    @staticmethod
    def get_cache_strategy():
        """Caching strategy recommendations"""
        return {
            'lottery_results': {
                'cache_key': 'lottery_results_{lottery_type}_{limit}',
                'timeout': 3600,  # 1 hour
                'description': 'Cache lottery results by type and limit'
            },
            'frequency_analysis': {
                'cache_key': 'frequency_analysis_{days}_{lottery_type}',
                'timeout': 1800,  # 30 minutes
                'description': 'Cache frequency analysis results'
            },
            'database_stats': {
                'cache_key': 'database_stats',
                'timeout': 600,  # 10 minutes
                'description': 'Cache database statistics'
            }
        }
    
    @staticmethod
    def get_cdn_config():
        """CDN configuration for static assets"""
        return {
            'static_files': [
                '/static/css/*.css',
                '/static/js/*.js',
                '/static/images/*'
            ],
            'cache_headers': {
                'css': 'public, max-age=86400',  # 1 day
                'js': 'public, max-age=86400',   # 1 day
                'images': 'public, max-age=604800'  # 1 week
            },
            'compression': ['gzip', 'deflate'],
            'minification': True
        }

class SecurityScanner:
    """Security scanning and recommendations"""
    
    @staticmethod
    def scan_dependencies():
        """Scan for dependency vulnerabilities"""
        import subprocess
        
        try:
            # Run safety check on dependencies
            result = subprocess.run(['safety', 'check'], 
                                  capture_output=True, text=True)
            return {
                'status': 'completed',
                'vulnerabilities': result.stdout,
                'recommendations': 'Update vulnerable packages immediately'
            }
        except FileNotFoundError:
            return {
                'status': 'tool_missing',
                'message': 'Install safety: pip install safety'
            }
    
    @staticmethod
    def security_checklist():
        """Production security checklist"""
        return {
            'required_settings': [
                'SECRET_KEY set to strong value',
                'DATABASE_URL using SSL',
                'CSRF protection enabled',
                'Secure session cookies',
                'Rate limiting configured',
                'Input validation implemented',
                'Error handling configured'
            ],
            'recommended_headers': [
                'Content-Security-Policy',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Strict-Transport-Security'
            ],
            'monitoring_requirements': [
                'Health checks enabled',
                'Performance monitoring',
                'Error tracking',
                'Security event logging'
            ]
        }

def validate_production_readiness():
    """Validate that application is production-ready"""
    issues = []
    warnings = []
    
    # Check required environment variables
    required_env = ['SECRET_KEY', 'DATABASE_URL', 'GEMINI_API_KEY']
    for var in required_env:
        if not os.environ.get(var):
            issues.append(f"Missing required environment variable: {var}")
    
    # Check security settings
    if os.environ.get('SECRET_KEY') == 'dev-secret-key':
        issues.append("SECRET_KEY is using default development value")
    
    # Check database SSL
    db_url = os.environ.get('DATABASE_URL', '')
    if 'sslmode=require' not in db_url and db_url.startswith('postgres'):
        warnings.append("Database SSL not explicitly required")
    
    return {
        'ready': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'timestamp': os.environ.get('DEPLOYMENT_TIME', 'unknown')
    }