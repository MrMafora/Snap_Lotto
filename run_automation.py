#!/usr/bin/env python3
"""
Direct automation script to update lottery database with latest results
"""
import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_complete_automation():
    """Run the complete automation workflow to update database with latest lottery results"""
    try:
        logger.info("Starting complete lottery automation workflow...")
        
        # Use the modular daily automation system
        from daily_automation import run_complete_automation
        result = run_complete_automation()
        
        if result.get('overall_success'):
            logger.info("Complete automation workflow completed successfully")
        else:
            logger.warning("Complete automation workflow completed with some errors")
            logger.info(f"Step results: {result}")
            
        return result.get('overall_success', False)
        
    except Exception as e:
        logger.error(f"Complete automation failed: {e}")
        return False

if __name__ == "__main__":
    run_complete_automation()