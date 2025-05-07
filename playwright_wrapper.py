"""
Playwright Wrapper Module

This module wraps all playwright imports to prevent circular import issues.
By having a dedicated module that only imports playwright functionality,
we avoid circular dependencies when other modules import and use playwright.
"""
import logging
import traceback
from logger import setup_logger

# Set up module-specific logger
logger = setup_logger(__name__)

# Flag to track if playwright has been imported successfully
_playwright_imported = False
_sync_playwright = None
_async_playwright = None

def get_sync_playwright():
    """
    Get the sync_playwright function safely.
    
    Returns:
        function: The sync_playwright function or None if import failed
    """
    global _sync_playwright, _playwright_imported
    
    if _sync_playwright is not None:
        return _sync_playwright
        
    try:
        from playwright.sync_api import sync_playwright as sp
        _sync_playwright = sp
        _playwright_imported = True
        logger.info("Successfully imported sync_playwright")
        return _sync_playwright
    except ImportError as e:
        logger.error(f"Failed to import sync_playwright: {str(e)}")
        traceback.print_exc()
        return None
    except Exception as e:
        logger.error(f"Unexpected error importing sync_playwright: {str(e)}")
        traceback.print_exc()
        return None

def get_async_playwright():
    """
    Get the async_playwright function safely.
    
    Returns:
        function: The async_playwright function or None if import failed
    """
    global _async_playwright, _playwright_imported
    
    if _async_playwright is not None:
        return _async_playwright
        
    try:
        from playwright.async_api import async_playwright as ap
        _async_playwright = ap
        _playwright_imported = True
        logger.info("Successfully imported async_playwright")
        return _async_playwright
    except ImportError as e:
        logger.error(f"Failed to import async_playwright: {str(e)}")
        traceback.print_exc()
        return None
    except Exception as e:
        logger.error(f"Unexpected error importing async_playwright: {str(e)}")
        traceback.print_exc()
        return None

def is_playwright_available():
    """Check if playwright has been successfully imported"""
    global _playwright_imported
    
    # Try importing if we haven't already
    if not _playwright_imported:
        _playwright_imported = get_sync_playwright() is not None or get_async_playwright() is not None
        
    return _playwright_imported

def handle_playwright_error(error, default_message="Error in Playwright operation"):
    """
    Safely handle playwright errors without creating circular imports.
    
    Args:
        error: The exception object
        default_message: Default message to use if error type can't be determined
        
    Returns:
        str: Error message
    """
    error_message = str(error)
    error_type = type(error).__name__
    
    # Common error patterns to check for
    if "net::" in error_message or "network" in error_message.lower():
        return f"Network error: {error_message}"
    elif "timeout" in error_message.lower():
        return f"Timeout error: {error_message}"
    elif "navigation" in error_message.lower():
        return f"Navigation error: {error_message}"
    else:
        return f"{default_message}: {error_type}: {error_message}"

def ensure_playwright_browsers():
    """
    Ensure that Playwright browsers are installed.
    This should be run once at the start of the application.
    """
    try:
        import subprocess
        subprocess.check_call(['playwright', 'install', 'chromium'])
        logger.info("Playwright browsers installed successfully")
        return True
    except Exception as e:
        logger.error(f"Error installing Playwright browsers: {str(e)}")
        return False