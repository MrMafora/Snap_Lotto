"""
Performance Cache Manager for Snap Lotto
Implements smart caching to dramatically improve page load speeds
"""

import time
import logging
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    """In-memory cache for frequent lottery data queries"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.default_ttl = 300  # 5 minutes default cache
        
    def get(self, key):
        """Get cached value if not expired"""
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.default_ttl:
                logger.debug(f"Cache HIT for key: {key}")
                return self.cache[key]
            else:
                # Expired, remove from cache
                del self.cache[key]
                del self.cache_timestamps[key]
                logger.debug(f"Cache EXPIRED for key: {key}")
        
        logger.debug(f"Cache MISS for key: {key}")
        return None
    
    def set(self, key, value, ttl=None):
        """Set cached value with TTL"""
        if ttl is None:
            ttl = self.default_ttl
            
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()
        logger.debug(f"Cache SET for key: {key} (TTL: {ttl}s)")
    
    def clear(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Cache cleared")
    
    def get_stats(self):
        """Get cache statistics"""
        total_keys = len(self.cache)
        expired_keys = 0
        current_time = time.time()
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp >= self.default_ttl:
                expired_keys += 1
        
        return {
            'total_keys': total_keys,
            'active_keys': total_keys - expired_keys,
            'expired_keys': expired_keys
        }

# Global cache instance
cache = CacheManager()

def cached_query(ttl=300):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache first
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

def get_optimized_latest_results(limit=10):
    """Optimized query for latest lottery results - loads fresh data from database"""
    from models import LotteryResult, db
    from sqlalchemy import desc, func
    from datetime import datetime
    
    # Force fresh connection 
    db.session.close()
    
    # Get the latest result for each lottery type using window function
    subquery = db.session.query(
        LotteryResult.id,
        LotteryResult.lottery_type,
        LotteryResult.draw_number,
        LotteryResult.draw_date,
        LotteryResult.main_numbers,
        LotteryResult.bonus_numbers,
        LotteryResult.created_at,
        func.row_number().over(
            partition_by=LotteryResult.lottery_type,
            order_by=desc(LotteryResult.created_at)
        ).label('rn')
    ).subquery()
    
    # Select only the most recent record for each lottery type
    results = db.session.query(LotteryResult)\
        .join(subquery, LotteryResult.id == subquery.c.id)\
        .filter(subquery.c.rn == 1)\
        .order_by(desc(LotteryResult.created_at))\
        .all()
    
    return results

def get_optimized_lottery_stats():
    """Get lottery statistics with caching"""
    from models import LotteryResult, db
    
    cache_key = "lottery_stats"
    cached_stats = cache.get(cache_key)
    
    if cached_stats is not None:
        return cached_stats
    
    # Get counts efficiently
    stats = {
        'total_draws': db.session.query(LotteryResult).count(),
        'lottery_types': db.session.query(LotteryResult.lottery_type).distinct().count(),
        'latest_update': db.session.query(db.func.max(LotteryResult.created_at)).scalar()
    }
    
    # Cache for 10 minutes
    cache.set(cache_key, stats, 600)
    return stats

def clear_results_cache():
    """Clear results-related cache when new data is added"""
    keys_to_clear = [key for key in cache.cache.keys() if 'results' in key or 'stats' in key]
    for key in keys_to_clear:
        if key in cache.cache:
            del cache.cache[key]
            del cache.cache_timestamps[key]
    logger.info(f"Cleared {len(keys_to_clear)} result cache entries")