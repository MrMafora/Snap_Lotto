"""
Security Utilities Module
Phase 1 Security Implementation - CSRF Protection and Input Validation
"""

from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
import html
from functools import wraps
from flask import request, jsonify, flash, redirect, url_for
from werkzeug.exceptions import TooManyRequests

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize rate limiter
# Only apply rate limits to specific routes that need protection (admin, API, sensitive actions)
# No default limits - let users browse freely
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)

class RateLimitExceeded(Exception):
    """Custom exception for rate limiting"""
    pass

def sanitize_input(input_string):
    """
    Sanitize user input to prevent XSS attacks
    """
    if not input_string:
        return ""
    
    # HTML escape the input
    sanitized = html.escape(str(input_string))
    
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized

def validate_form_data(form_data, required_fields=None, field_types=None):
    """
    Validate form data with type checking and required field validation
    """
    errors = {}
    
    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                errors[field] = f"{field} is required"
    
    # Check field types
    if field_types:
        for field, expected_type in field_types.items():
            if field in form_data and form_data[field]:
                try:
                    if expected_type == 'email':
                        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', form_data[field]):
                            errors[field] = "Invalid email format"
                    elif expected_type == 'int':
                        int(form_data[field])
                    elif expected_type == 'float':
                        float(form_data[field])
                    elif expected_type == 'alphanumeric':
                        if not re.match(r'^[a-zA-Z0-9_]+$', form_data[field]):
                            errors[field] = "Only alphanumeric characters and underscores allowed"
                except (ValueError, TypeError):
                    errors[field] = f"Invalid {expected_type} format"
    
    return errors

def require_auth(f):
    """
    Decorator to require authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """
    Decorator to require admin privileges
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_api(limit="5 per minute"):
    """
    Rate limiting decorator for API endpoints
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return limiter.limit(limit)(f)(*args, **kwargs)
            except TooManyRequests:
                raise RateLimitExceeded("Rate limit exceeded")
        return decorated_function
    return decorator

def validate_file_upload(file):
    """
    Validate uploaded files for security
    """
    if not file:
        return False, "No file selected"
    
    # Check file size (16MB limit)
    MAX_FILE_SIZE = 16 * 1024 * 1024
    if hasattr(file, 'content_length') and file.content_length > MAX_FILE_SIZE:
        return False, "File too large (max 16MB)"
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    if '.' not in file.filename:
        return False, "File must have an extension"
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
    
    return True, "File is valid"

def secure_headers(response):
    """
    Add security headers to response
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
    return response

def init_security(app):
    """
    Initialize security features
    """
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Add security headers to all responses
    @app.after_request
    def after_request(response):
        return secure_headers(response)
    
    # Handle CSRF errors
    @app.errorhandler(400)
    def csrf_error(error):
        return jsonify({'error': 'CSRF token missing or invalid'}), 400