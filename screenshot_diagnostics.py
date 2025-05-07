"""
Screenshot Synchronization Diagnostics

This module provides enhanced diagnostic logging and error tracking
for the screenshot synchronization process. It helps identify issues
with specific lottery types or URLs.
"""
import os
import logging
import traceback
import json
from datetime import datetime
from functools import wraps
from models import db, Screenshot, ScheduleConfig

# Set up specialized logger for diagnostics
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("screenshot_diagnostics")
file_handler = logging.FileHandler("logs/screenshot_diagnostics.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Track statistics for each sync run
sync_stats = {
    "last_run": None,
    "total_attempts": 0,
    "successful": 0,
    "failed": 0,
    "by_lottery_type": {},
    "errors": []
}

def log_sync_attempt(lottery_type, url, success, error_msg=None):
    """Log a synchronization attempt with detailed information"""
    sync_stats["total_attempts"] += 1
    
    if success:
        sync_stats["successful"] += 1
        status = "SUCCESS"
    else:
        sync_stats["failed"] += 1
        status = "FAILED"
        
    # Initialize lottery type stats if not already present
    if lottery_type not in sync_stats["by_lottery_type"]:
        sync_stats["by_lottery_type"][lottery_type] = {
            "attempts": 0,
            "successful": 0,
            "failed": 0,
            "last_success": None,
            "errors": []
        }
        
    # Update lottery type stats
    lottery_stats = sync_stats["by_lottery_type"][lottery_type]
    lottery_stats["attempts"] += 1
    
    if success:
        lottery_stats["successful"] += 1
        lottery_stats["last_success"] = datetime.now().isoformat()
    else:
        lottery_stats["failed"] += 1
        # Track error for this lottery type
        if error_msg:
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "error": error_msg
            }
            lottery_stats["errors"].append(error_entry)
            sync_stats["errors"].append({
                "lottery_type": lottery_type,
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "error": error_msg
            })
    
    # Log the attempt
    message = f"[{status}] Sync for {lottery_type} ({url})"
    if error_msg:
        message += f" - Error: {error_msg}"
        
    if success:
        logger.info(message)
    else:
        logger.error(message)
    
    # Update last run timestamp
    sync_stats["last_run"] = datetime.now().isoformat()
    
    # Save sync stats to file
    save_sync_stats()

def save_sync_stats():
    """Save synchronization statistics to a JSON file"""
    try:
        with open("logs/sync_stats.json", "w") as f:
            json.dump(sync_stats, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving sync stats: {str(e)}")

def load_sync_stats():
    """Load synchronization statistics from a JSON file if it exists"""
    try:
        if os.path.exists("logs/sync_stats.json"):
            with open("logs/sync_stats.json", "r") as f:
                global sync_stats
                sync_stats = json.load(f)
                logger.info("Loaded existing sync stats")
    except Exception as e:
        logger.error(f"Error loading sync stats: {str(e)}")

def track_sync(func):
    """Decorator to track synchronization function calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.info(f"Starting {func_name} with args: {args}, kwargs: {kwargs}")
        
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Completed {func_name} in {duration:.2f} seconds")
            return result
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.error(f"Error in {func_name} after {duration:.2f} seconds: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    return wrapper

def get_screenshot_status():
    """Get the status of all screenshots in the database"""
    try:
        screenshots = Screenshot.query.all()
        configs = ScheduleConfig.query.all()
        
        status = {
            "total_screenshots": len(screenshots),
            "total_configs": len(configs),
            "screenshots": [],
            "configs": []
        }
        
        # Collect screenshot info
        for screenshot in screenshots:
            status["screenshots"].append({
                "id": screenshot.id,
                "lottery_type": screenshot.lottery_type,
                "url": screenshot.url,
                "timestamp": screenshot.timestamp.isoformat() if screenshot.timestamp else None,
                "has_path": bool(screenshot.path)
            })
        
        # Collect config info
        for config in configs:
            status["configs"].append({
                "id": config.id,
                "lottery_type": config.lottery_type,
                "url": config.url,
                "active": config.active,
                "last_run": config.last_run.isoformat() if config.last_run else None
            })
        
        return status
    except Exception as e:
        logger.error(f"Error getting screenshot status: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def diagnose_sync_issues():
    """Diagnose synchronization issues by comparing screenshots and configs"""
    try:
        screenshots = Screenshot.query.all()
        configs = ScheduleConfig.query.all()
        
        # Create lookup tables
        screenshot_by_url = {s.url: s for s in screenshots}
        config_by_url = {c.url: c for c in configs}
        
        # Check for URLs in screenshots that don't have configs
        for url, screenshot in screenshot_by_url.items():
            if url not in config_by_url:
                logger.warning(f"Screenshot exists for URL {url}, but no matching ScheduleConfig")
        
        # Check for configs that don't have screenshots
        for url, config in config_by_url.items():
            if url not in screenshot_by_url:
                logger.warning(f"ScheduleConfig exists for URL {url}, but no matching Screenshot")
        
        # Check for mismatched timestamps
        issues = []
        for url in set(screenshot_by_url.keys()) & set(config_by_url.keys()):
            screenshot = screenshot_by_url[url]
            config = config_by_url[url]
            
            # Skip if either timestamp is missing
            if not screenshot.timestamp or not config.last_run:
                issues.append({
                    "url": url,
                    "lottery_type": screenshot.lottery_type,
                    "issue": "Missing timestamp",
                    "screenshot_time": screenshot.timestamp.isoformat() if screenshot.timestamp else None,
                    "config_time": config.last_run.isoformat() if config.last_run else None
                })
                continue
            
            # Check for significant timestamp differences (more than 1 minute)
            time_diff = abs((screenshot.timestamp - config.last_run).total_seconds())
            if time_diff > 60:
                issues.append({
                    "url": url,
                    "lottery_type": screenshot.lottery_type,
                    "issue": "Timestamp mismatch",
                    "screenshot_time": screenshot.timestamp.isoformat(),
                    "config_time": config.last_run.isoformat(),
                    "difference_seconds": time_diff
                })
        
        # Save issues to file
        with open("logs/sync_issues.json", "w") as f:
            json.dump(issues, f, indent=2)
        
        return issues
    except Exception as e:
        logger.error(f"Error diagnosing sync issues: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

# Initialize by loading existing stats
load_sync_stats()