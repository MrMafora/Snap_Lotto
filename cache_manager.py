"""
Performance Cache Manager for Snap Lotto
Implements smart caching to dramatically improve page load speeds
"""

import time
import logging
from functools import wraps
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)

class CacheManager:
    """In-memory cache for frequent lottery data queries"""
    
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = Lock()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key):
        """Get cached value if not expired"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.hit_count += 1
                    return value
                else:
                    # Expired
                    del self.cache[key]
            
            self.miss_count += 1
            return None
    
    def set(self, key, value, ttl=None):
        """Set cached value with TTL"""
        if ttl is None:
            ttl = 300  # 5 minutes default
        
        expiry = time.time() + ttl
        
        with self.lock:
            # Remove oldest items if cache is full
            while len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            self.cache[key] = (value, expiry)
    
    def clear(self):
        """Clear all cached data"""
        with self.lock:
            self.cache.clear()
            self.hit_count = 0
            self.miss_count = 0
    
    def get_stats(self):
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate
        }

# Global cache instance
cache = CacheManager()

def cached_query(ttl=300):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, result cached")
            
            return result
        return wrapper
    return decorator

@cached_query(ttl=600)  # Cache for 10 minutes
def get_optimized_latest_results(limit=10):
    """Optimized query for latest lottery results - loads fresh data from database"""
    from models import db, LotteryResult
    
    try:
        results = db.session.query(LotteryResult)\
            .order_by(LotteryResult.draw_date.desc())\
            .limit(limit)\
            .all()
        
        logger.info(f"Loaded {len(results)} latest results from database")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching latest results: {e}")
        return []

@cached_query(ttl=1800)  # Cache for 30 minutes
def get_optimized_lottery_stats():
    """Get lottery statistics with caching"""
    from models import db
    from sqlalchemy import text
    
    try:
        stats_query = text("""
            SELECT 
                lottery_type,
                COUNT(*) as total_draws,
                MAX(draw_number) as latest_draw,
                MAX(draw_date) as latest_date,
                MIN(draw_date) as earliest_date
            FROM lottery_result 
            GROUP BY lottery_type 
            ORDER BY lottery_type
        """)
        
        result = db.session.execute(stats_query)
        stats = result.fetchall()
        
        return [dict(row._mapping) for row in stats]
        
    except Exception as e:
        logger.error(f"Error getting lottery statistics: {e}")
        return []

def clear_results_cache():
    """Clear results-related cache when new data is added"""
    cache.clear()
    logger.info("Results cache cleared due to new data")

# Additional cache utilities
def warm_cache():
    """Pre-populate cache with commonly requested data"""
    logger.info("Warming up cache...")
    
    # Pre-load latest results
    get_optimized_latest_results(10)
    get_optimized_latest_results(20)
    
    # Pre-load statistics
    get_optimized_lottery_stats()
    
    logger.info("Cache warmed up successfully")

def get_cache_performance():
    """Get cache performance metrics"""
    stats = cache.get_stats()
    
    return {
        'cache_stats': stats,
        'performance_impact': {
            'estimated_db_queries_saved': stats['hit_count'],
            'estimated_response_time_improvement': f"{stats['hit_rate'] * 100:.1f}%"
        }
    }