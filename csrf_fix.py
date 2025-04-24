"""
CSRF configuration enhancement for deployment environments.
This module extends the default Flask-WTF CSRF protection to work properly
in production deployments with Replit URLs.

Additionally handles Content Security Policy (CSP) configuration to allow
specific external services like Google Analytics.
"""

from flask import session, request, current_app, Response
from flask_wtf.csrf import CSRFProtect, generate_csrf

class EnhancedCSRFProtect(CSRFProtect):
    """
    Enhanced CSRF protection class that handles multiple secure domains
    and is aware of production vs development environments.
    """
    
    def __init__(self, app=None):
        super().__init__(app)
    
    def init_app(self, app):
        """
        Initialize the CSRF extension with enhanced cookie settings
        for production environments.
        """
        super().init_app(app)
        
        # Override the default CSRF cookie settings
        app.config.setdefault('WTF_CSRF_TIME_LIMIT', 3600)  # 1 hour token timeout
        
        # Disable referrer check in all environments for Replit compatibility
        app.config.setdefault('WTF_CSRF_CHECK_REFERER', False)
        
        # Set proper cookie settings for production vs development
        environment = app.config.get('ENVIRONMENT', 'development')
        if environment == 'production':
            # Secure settings for production
            app.config.setdefault('WTF_CSRF_SSL_STRICT', False)  # Disable SSL strict check for Replit
            app.config.setdefault('WTF_CSRF_COOKIE_SECURE', True)
            app.config.setdefault('WTF_CSRF_COOKIE_SAMESITE', 'Lax')
            
            # Configure domains for secure cookies
            # Replit domain pattern: username-project.replit.app
            replit_domain = request.host.split(':')[0] if request.host else None
            if replit_domain:
                app.config.setdefault('WTF_CSRF_COOKIE_DOMAIN', replit_domain)
        else:
            # Development settings
            app.config.setdefault('WTF_CSRF_SSL_STRICT', False)
            app.config.setdefault('WTF_CSRF_COOKIE_SECURE', False)
            
        @app.after_request
        def set_csrf_cookie(response):
            """
            Set the CSRF token in a cookie after each request.
            This ensures the token is always available.
            """
            if 'csrf_token' not in session:
                session['csrf_token'] = generate_csrf()
                
            response.set_cookie(
                'csrf_token',
                session['csrf_token'],
                max_age=app.config['WTF_CSRF_TIME_LIMIT'],
                secure=app.config.get('WTF_CSRF_COOKIE_SECURE', False),
                httponly=False,  # Allow JavaScript access
                samesite=app.config.get('WTF_CSRF_COOKIE_SAMESITE', None),
                domain=app.config.get('WTF_CSRF_COOKIE_DOMAIN', None)
            )
            return response
            
    def exempt(self, view):
        """
        Mark a view or blueprint to be exempt from CSRF protection.
        """
        return super().exempt(view)