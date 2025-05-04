#!/usr/bin/env python3
"""
Comprehensive script to capture all lottery screenshots with enhanced anti-bot measures.

This script:
1. Ensures Playwright and all requirements are installed
2. Captures all missing results and history URLs
3. Implements advanced anti-bot measures
4. Saves all screenshots to the database
"""
import os
import logging
import time
import sys
import argparse
import random
import subprocess
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/enhanced_capture_all.log')
    ]
)
logger = logging.getLogger(__name__)

# Make sure we can find our module
sys.path.append(os.getcwd())

def check_playwright_installation():
    """
    Check if Playwright is installed and install it if needed.
    
    Returns:
        bool: Success status
    """
    try:
        # Check if playwright module is installed
        import playwright
        logger.info(f"Playwright module found (version {playwright.__version__})")
        
        # Check if browsers are installed
        try:
            # Run the installation command if they're not already installed
            logger.info("Checking Playwright browser installation...")
            result = subprocess.run(
                ["python", "-m", "playwright", "install", "chromium"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("Playwright browsers are installed successfully")
                return True
            else:
                logger.error(f"Browser installation failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error during browser installation: {str(e)}")
            return False
    except ImportError:
        logger.warning("Playwright not found. Attempting to install...")
        try:
            # Try to install Playwright
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "playwright"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("Playwright installed successfully")
                
                # Install browsers
                browser_result = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                if browser_result.returncode == 0:
                    logger.info("Playwright browser installed successfully")
                    return True
                else:
                    logger.error(f"Browser installation failed: {browser_result.stderr}")
                    return False
            else:
                logger.error(f"Playwright installation failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing Playwright: {str(e)}")
            return False

def create_app_context():
    """Create and return Flask app context."""
    from main import app
    return app.app_context()

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        'logs',
        'screenshots',
        'cookies'
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Created directory: {dir_path}")

def main():
    """Main entry point for comprehensive capture."""
    parser = argparse.ArgumentParser(description="Capture all lottery screenshots with enhanced anti-bot measures")
    parser.add_argument('--results-only', action='store_true', help='Only capture results URLs')
    parser.add_argument('--history-only', action='store_true', help='Only capture history URLs')
    parser.add_argument('--force', action='store_true', help='Force recapture of all URLs, even existing ones')
    parser.add_argument('--type', type=str, help='Specific lottery type to capture (e.g., "Lotto", "Powerball")')
    parser.add_argument('--max-captures', type=int, default=0, help='Maximum number of captures to perform (0 for all)')
    parser.add_argument('--delay', type=int, default=60, help='Base delay between captures in seconds (default: 60)')
    
    args = parser.parse_args()
    
    # Ensure directories
    ensure_directories()
    
    # Check and install Playwright if needed
    if not check_playwright_installation():
        logger.error("Failed to set up Playwright. Exiting.")
        return 1

    from screenshot_manager import ensure_playwright_browsers
    # Ensure browsers are installed
    ensure_playwright_browsers()
    
    # Import the modules after setup
    import capture_missing_results
    import capture_missing_history
    
    # Track results
    success_count = 0
    total_attempts = 0
    
    # Process URLs based on arguments
    if args.type:
        logger.info(f"Limiting capture to lottery type: {args.type}")
    
    if not args.history_only:
        # Capture results URLs
        logger.info("Starting capture of results URLs")
        if args.force:
            success = capture_missing_results.force_recapture_results(args.type)
        else:
            success = capture_missing_results.capture_missing_results()
        
        if success:
            logger.info("Results URL capture completed successfully")
            success_count += 1
        else:
            logger.error("Results URL capture completed with errors")
        
        total_attempts += 1
    
    if not args.results_only:
        # Capture history URLs
        logger.info("Starting capture of history URLs")
        if args.force:
            success = capture_missing_history.force_recapture_history(args.type)
        else:
            success = capture_missing_history.capture_missing_history()
        
        if success:
            logger.info("History URL capture completed successfully")
            success_count += 1
        else:
            logger.error("History URL capture completed with errors")
        
        total_attempts += 1
    
    # Report results
    if success_count == total_attempts:
        logger.info("All captures completed successfully!")
        return 0
    else:
        logger.warning(f"{success_count} out of {total_attempts} capture operations succeeded")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        import traceback
        logger.critical(traceback.format_exc())
        sys.exit(1)