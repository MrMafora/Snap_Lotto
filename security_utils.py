"""
Security Utilities Module
Extracted from main.py for better code organization (Phase 2 refactoring)
Contains rate limiting, input validation, and security functions
"""

import re
import time
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify

class RateLimiter:
    """In-memory rate limiter for API endpoints"""
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_ips = defaultdict(float)
    
    def is_allowed(self, identifier, max_requests=10, window=60):
        """Check if request is allowed under rate limit"""
        now = time.time()
        
        # Check if IP is temporarily blocked
        if identifier in self.blocked_ips:
            if now < self.blocked_ips[identifier]:
                return False
            else:
                del self.blocked_ips[identifier]
        
        # Clean old requests
        while self.requests[identifier] and self.requests[identifier][0] < now - window:
            self.requests[identifier].popleft()
        
        # Check rate limit
        if len(self.requests[identifier]) >= max_requests:
            # Block IP for 5 minutes
            self.blocked_ips[identifier] = now + 300
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_requests=10, window=60):
    """Decorator for rate limiting endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr
            
            if not rate_limiter.is_allowed(identifier, max_requests, window):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.'
                }), 429
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_lottery_type(lottery_type):
    """Validate lottery type input"""
    valid_types = ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'PowerBall', 'POWERBALL PLUS', 'DAILY LOTTO']
    if lottery_type not in valid_types:
        raise ValueError(f"Invalid lottery type: {lottery_type}")
    return lottery_type

def validate_draw_number(draw_number):
    """Validate draw number input"""
    try:
        num = int(draw_number)
        if num < 1 or num > 99999:
            raise ValueError("Draw number must be between 1 and 99999")
        return num
    except (ValueError, TypeError):
        raise ValueError("Draw number must be a valid integer")

def sanitize_input(input_str, max_length=255):
    """Sanitize string input to prevent XSS"""
    if not input_str:
        return ""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>&"\']', '', str(input_str))
    return sanitized[:max_length]

def validate_file_upload(file, allowed_extensions=None, max_size_mb=10):
    """Validate uploaded file"""
    if allowed_extensions is None:
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
    
    if not file or not file.filename:
        raise ValueError("No file provided")
    
    # Check file extension
    file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"File too large. Maximum size: {max_size_mb}MB")
    
    return True

def log_security_event(event_type, details, request_ip=None):
    """Log security-related events"""
    import logging
    logger = logging.getLogger('security')
    
    ip = request_ip or (request.remote_addr if request else 'unknown')
    logger.warning(f"Security Event [{event_type}] from {ip}: {details}")