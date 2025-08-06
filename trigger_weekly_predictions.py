#!/usr/bin/env python3
"""
Simple script to trigger weekly predictions manually
Generates 3 predictions per game for all lottery games
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run weekly predictions"""
    logger.info("Triggering weekly AI predictions...")
    
    try:
        # Run weekly prediction scheduler
        result = subprocess.run([
            sys.executable, 'weekly_prediction_scheduler.py'
        ], timeout=1800)  # 30 minute timeout
        
        if result.returncode == 0:
            logger.info("Weekly predictions completed successfully")
        else:
            logger.error("Weekly predictions failed")
            
    except subprocess.TimeoutExpired:
        logger.error("Weekly predictions timed out")
    except Exception as e:
        logger.error(f"Failed to run weekly predictions: {e}")

if __name__ == "__main__":
    main()