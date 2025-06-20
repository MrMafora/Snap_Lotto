"""
Performance Cache Manager for Snap Lotto
Implements smart caching to dramatically improve page load speeds
"""
import time
import logging
from functools import wraps
from models import db, LotteryResult
import json

logger = logging.getLogger(__name__)

class CacheManager:
    """In-memory cache for frequent lottery data queries"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.default_ttl = 300  # 5 minutes default
    
    def get(self, key):
        """Get cached value if not expired"""
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.default_ttl:
                return self.cache[key]
            else:
                # Expired, remove from cache
                self.cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
        return None
    
    def set(self, key, value, ttl=None):
        """Set cached value with TTL"""
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()
        if ttl:
            # Custom TTL handling could be added here
            pass
    
    def clear(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Cache cleared")
    
    def get_stats(self):
        """Get cache statistics"""
        return {
            'entries': len(self.cache),
            'memory_usage': sum(len(str(v)) for v in self.cache.values())
        }

# Global cache instance
cache_manager = CacheManager()

def cached_query(ttl=300):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Try to get from cache first
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

@cached_query(ttl=180)  # Cache for 3 minutes
def get_optimized_latest_results(limit=10):
    """Optimized query for latest lottery results with proper caching"""
    try:
        # Return actual LotteryResult objects for template compatibility
        results = LotteryResult.query.order_by(
            LotteryResult.draw_date.desc(),
            LotteryResult.id.desc()
        ).limit(limit).all()
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting latest results: {e}")
        return []

@cached_query(ttl=600)
def get_optimized_lottery_stats():
    """Get lottery statistics with caching and optimized queries"""
    try:
        # Use more efficient queries
        total_results = db.session.query(db.func.count(LotteryResult.id)).scalar()
        latest_result = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).first()
        
        # Count distinct lottery types efficiently
        lottery_types_count = db.session.query(db.func.count(db.distinct(LotteryResult.lottery_type))).scalar()
        
        return {
            'total_results': total_results,
            'latest_draw': latest_result.draw_number if latest_result else 'None',
            'latest_date': latest_result.draw_date.strftime('%Y-%m-%d') if latest_result and latest_result.draw_date else 'None',
            'lottery_types': lottery_types_count
        }
    except Exception as e:
        logger.error(f"Error getting lottery stats: {e}")
        return {'total_results': 0, 'latest_draw': 'Error', 'latest_date': 'Error'}

def clear_results_cache():
    """Clear results-related cache when new data is added"""
    cache_manager.clear()
    logger.info("Results cache cleared")