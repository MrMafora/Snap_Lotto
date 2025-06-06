"""
Force clear all cached data and restart with fresh lottery numbers
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from cache_manager import CacheManager

def force_clear_all_cache():
    """Force clear all cached data"""
    with app.app_context():
        # Clear application cache
        cache = CacheManager()
        cache.clear()
        
        # Clear SQLAlchemy session
        db.session.remove()
        
        print("✅ All cache cleared successfully")
        print("✅ Database session refreshed")
        print("✅ Ready to load fresh lottery data")

if __name__ == "__main__":
    force_clear_all_cache()