"""
Cache Manager Module
Simple caching system for lottery analysis
"""

import logging
from functools import wraps
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache = {}

def cached_query(ttl=300):
    """Decorator for caching query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            if cache_key in _cache:
                cached_data, timestamp = _cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=ttl):
                    logger.info(f"Cache hit for {cache_key}")
                    return cached_data
                else:
                    # Cache expired
                    del _cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, datetime.now())
            logger.info(f"Cache miss for {cache_key} - result cached")
            
            return result
        return wrapper
    return decorator

def init_cache_manager(app):
    """Initialize cache manager"""
    logger.info("Simple cache manager initialized")
    
def clear_cache():
    """Clear all cached data"""
    global _cache
    _cache.clear()
    logger.info("Cache cleared")
    
def get_cache_stats():
    """Get cache statistics"""
    return {
        'size': len(_cache),
        'keys': list(_cache.keys())
    }