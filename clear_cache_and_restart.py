#!/usr/bin/env python3
"""
Clear application cache and force fresh data reload
"""

import os
import sys
from cache_manager import CacheManager

def main():
    """Clear all cached data and force fresh reload"""
    print("Clearing application cache...")
    
    # Clear the cache
    cache = CacheManager()
    cache.clear()
    
    print("Cache cleared successfully")
    print("Application will now load fresh data from database")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)