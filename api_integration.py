"""
RESTful API for Third-Party Integration
Phase 4 Implementation - External API Access and Integration
"""

import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, g
# Note: flask-limiter integration would be added here when available
import jwt
from models import db, LotteryResult, User
from security_utils import rate_limit
from predictive_analytics import get_lottery_predictions
from advanced_reporting import report_generator

logger = logging.getLogger(__name__)

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# API Configuration
API_CONFIG = {
    'version': '1.0',
    'name': 'Snap Lottery API',
    'description': 'RESTful API for South African lottery data and analytics',
    'base_url': '/api/v1',
    'authentication': 'JWT Bearer Token',
    'rate_limit': '1000 requests per hour',
    'supported_formats': ['json'],
    'documentation': '/api/v1/docs'
}

class APIKeyManager:
    """Manage API keys and authentication"""
    
    def __init__(self):
        self.api_keys = {}
        self.secret_key = "your-secret-key-here"  # Should be in environment
    
    def generate_api_key(self, user_id, permissions=None):
        """Generate a new API key for a user"""
        if permissions is None:
            permissions = ['read:results', 'read:analytics']
        
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'issued_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def validate_api_key(self, token):
        """Validate an API key"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if datetime.utcnow() > expires_at:
                return None, "Token expired"
            
            return payload, None
            
        except jwt.InvalidTokenError as e:
            return None, str(e)
    
    def has_permission(self, payload, required_permission):
        """Check if API key has required permission"""
        permissions = payload.get('permissions', [])
        return required_permission in permissions or 'admin' in permissions

# Global API key manager
api_key_manager = APIKeyManager()

def require_api_key(permission=None):
    """Decorator to require valid API key"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Missing or invalid Authorization header',
                    'message': 'Please provide a valid Bearer token'
                }), 401
            
            token = auth_header.split(' ')[1]
            payload, error = api_key_manager.validate_api_key(token)
            
            if error:
                return jsonify({
                    'error': 'Invalid API key',
                    'message': error
                }), 401
            
            # Check permissions
            if permission and not api_key_manager.has_permission(payload, permission):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'Required permission: {permission}'
                }), 403
            
            # Store user info in request context
            g.api_user = payload
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# API Documentation Endpoint
@api_bp.route('/docs')
def api_documentation():
    """API documentation and schema"""
    return jsonify({
        'api_info': API_CONFIG,
        'endpoints': {
            'authentication': {
                'POST /auth/token': 'Generate API token',
                'description': 'Authenticate and receive Bearer token'
            },
            'lottery_results': {
                'GET /results': 'Get latest lottery results',
                'GET /results/{lottery_type}': 'Get results for specific lottery type',
                'GET /results/{lottery_type}/{draw_number}': 'Get specific draw result'
            },
            'analytics': {
                'GET /analytics/frequency': 'Get number frequency analysis',
                'GET /analytics/predictions': 'Get AI predictions',
                'GET /analytics/trends': 'Get trend analysis'
            },
            'reports': {
                'POST /reports/generate': 'Generate comprehensive report',
                'GET /reports/export': 'Export report data'
            }
        },
        'authentication': {
            'type': 'Bearer Token',
            'header': 'Authorization: Bearer {token}',
            'obtain_token': 'POST /api/v1/auth/token'
        },
        'rate_limits': {
            'default': '1000 requests per hour',
            'burst': '10 requests per second'
        },
        'response_format': {
            'success': {
                'status': 'success',
                'data': '...',
                'meta': {...}
            },
            'error': {
                'status': 'error',
                'error': 'Error type',
                'message': 'Human readable message'
            }
        }
    })

# Authentication Endpoints
@api_bp.route('/auth/token', methods=['POST'])
@rate_limit(max_requests=5, window=60)  # 5 requests per minute
def generate_token():
    """Generate API token for authenticated user"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'error': 'Missing credentials',
            'message': 'Username and password required'
        }), 400
    
    # Authenticate user
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({
            'status': 'error',
            'error': 'Authentication failed',
            'message': 'Invalid username or password'
        }), 401
    
    # Generate API key
    permissions = ['read:results', 'read:analytics']
    if user.is_admin:
        permissions.extend(['write:data', 'admin'])
    
    token = api_key_manager.generate_api_key(user.id, permissions)
    
    return jsonify({
        'status': 'success',
        'data': {
            'token': token,
            'permissions': permissions,
            'expires_in': 31536000  # 1 year in seconds
        },
        'meta': {
            'user_id': user.id,
            'username': user.username,
            'admin': user.is_admin
        }
    })

# Lottery Results Endpoints
@api_bp.route('/results')
@require_api_key('read:results')
@rate_limit(max_requests=100, window=3600)  # 100 requests per hour
def get_lottery_results():
    """Get latest lottery results"""
    try:
        # Parse query parameters
        lottery_type = request.args.get('lottery_type')
        limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 results
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = db.session.query(LotteryResult)
        
        if lottery_type:
            query = query.filter(LotteryResult.lottery_type == lottery_type)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(LotteryResult.draw_date >= date_from_obj)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'error': 'Invalid date format',
                    'message': 'date_from must be in YYYY-MM-DD format'
                }), 400
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(LotteryResult.draw_date <= date_to_obj)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'error': 'Invalid date format',
                    'message': 'date_to must be in YYYY-MM-DD format'
                }), 400
        
        # Execute query
        results = query.order_by(LotteryResult.draw_date.desc()).limit(limit).all()
        
        # Format response
        formatted_results = []
        for result in results:
            formatted_result = {
                'id': result.id,
                'lottery_type': result.lottery_type,
                'draw_number': result.draw_number,
                'draw_date': result.draw_date.isoformat(),
                'main_numbers': json.loads(result.main_numbers.replace("'", '"')) if result.main_numbers else [],
                'bonus_numbers': json.loads(result.bonus_numbers.replace("'", '"')) if result.bonus_numbers else [],
                'divisions': json.loads(result.divisions) if result.divisions and isinstance(result.divisions, str) else result.divisions,
                'rollover_amount': result.rollover_amount,
                'next_jackpot': result.next_jackpot,
                'total_sales': result.total_sales,
                'created_at': result.created_at.isoformat() if result.created_at else None
            }
            formatted_results.append(formatted_result)
        
        return jsonify({
            'status': 'success',
            'data': formatted_results,
            'meta': {
                'count': len(formatted_results),
                'limit': limit,
                'filters': {
                    'lottery_type': lottery_type,
                    'date_from': date_from,
                    'date_to': date_to
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_lottery_results: {e}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'message': 'Unable to fetch lottery results'
        }), 500

@api_bp.route('/results/<lottery_type>')
@require_api_key('read:results')
@rate_limit(max_requests=100, window=3600)
def get_lottery_results_by_type(lottery_type):
    """Get results for specific lottery type"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        
        results = db.session.query(LotteryResult)\
            .filter(LotteryResult.lottery_type == lottery_type)\
            .order_by(LotteryResult.draw_date.desc())\
            .limit(limit)\
            .all()
        
        if not results:
            return jsonify({
                'status': 'success',
                'data': [],
                'meta': {
                    'count': 0,
                    'lottery_type': lottery_type,
                    'message': 'No results found for this lottery type'
                }
            })
        
        # Format results (same as above)
        formatted_results = []
        for result in results:
            formatted_result = {
                'id': result.id,
                'lottery_type': result.lottery_type,
                'draw_number': result.draw_number,
                'draw_date': result.draw_date.isoformat(),
                'main_numbers': json.loads(result.main_numbers.replace("'", '"')) if result.main_numbers else [],
                'bonus_numbers': json.loads(result.bonus_numbers.replace("'", '"')) if result.bonus_numbers else [],
                'divisions': json.loads(result.divisions) if result.divisions and isinstance(result.divisions, str) else result.divisions
            }
            formatted_results.append(formatted_result)
        
        return jsonify({
            'status': 'success',
            'data': formatted_results,
            'meta': {
                'count': len(formatted_results),
                'lottery_type': lottery_type,
                'latest_draw': formatted_results[0]['draw_number'] if formatted_results else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting results for {lottery_type}: {e}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'message': f'Unable to fetch results for {lottery_type}'
        }), 500

# Analytics Endpoints
@api_bp.route('/analytics/frequency')
@require_api_key('read:analytics')
@rate_limit(max_requests=50, window=3600)
def get_frequency_analysis():
    """Get number frequency analysis"""
    try:
        lottery_type = request.args.get('lottery_type')
        days = min(int(request.args.get('days', 365)), 1095)  # Max 3 years
        
        # Generate report for frequency analysis
        report = report_generator.generate_comprehensive_report(lottery_type, days)
        
        if 'error' in report:
            return jsonify({
                'status': 'error',
                'error': 'Analysis failed',
                'message': report['error']
            }), 400
        
        frequency_data = report.get('frequency_analysis', {})
        
        return jsonify({
            'status': 'success',
            'data': frequency_data,
            'meta': {
                'lottery_type': lottery_type or 'all',
                'analysis_period_days': days,
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in frequency analysis: {e}")
        return jsonify({
            'status': 'error',
            'error': 'Analysis failed',
            'message': 'Unable to generate frequency analysis'
        }), 500

@api_bp.route('/analytics/predictions')
@require_api_key('read:analytics')
@rate_limit(max_requests=20, window=3600)  # Limited predictions
def get_predictions():
    """Get AI-powered lottery predictions"""
    try:
        lottery_type = request.args.get('lottery_type')
        
        if not lottery_type:
            return jsonify({
                'status': 'error',
                'error': 'Missing parameter',
                'message': 'lottery_type parameter is required'
            }), 400
        
        predictions = get_lottery_predictions(lottery_type, 365)
        
        if not predictions:
            return jsonify({
                'status': 'error',
                'error': 'Prediction failed',
                'message': 'Unable to generate predictions for this lottery type'
            }), 400
        
        return jsonify({
            'status': 'success',
            'data': predictions,
            'meta': {
                'lottery_type': lottery_type,
                'prediction_model': 'ML Enhanced Pattern Recognition',
                'generated_at': datetime.utcnow().isoformat(),
                'disclaimer': 'Predictions are for entertainment only. Lottery numbers are random.'
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        return jsonify({
            'status': 'error',
            'error': 'Prediction failed',
            'message': 'Unable to generate predictions'
        }), 500

# Health Check Endpoint
@api_bp.route('/health')
def health_check():
    """API health check"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': API_CONFIG['version'],
            'services': {
                'database': 'healthy',
                'api': 'healthy'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

# Error Handlers
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({
        'status': 'error',
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@api_bp.errorhandler(429)
def api_rate_limit_exceeded(error):
    return jsonify({
        'status': 'error',
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please slow down.'
    }), 429

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({
        'status': 'error',
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

def init_api_integration(app):
    """Initialize API integration"""
    app.register_blueprint(api_bp)
    logger.info("API integration initialized")
    return api_bp