"""
Date and time formatting utilities for the application.
"""
from datetime import datetime
from flask import current_app
from timezone_utils import utc_to_sast, now_sast, format_sast

def format_datetime(dt=None, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format a datetime in South African Standard Time (SAST)
    
    Args:
        dt (datetime, optional): Datetime to format. Defaults to current time.
        format_str (str, optional): Format string. Defaults to "%Y-%m-%d %H:%M:%S".
        
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        # Use current time in SAST
        dt = now_sast()
    else:
        # Convert to SAST
        dt = utc_to_sast(dt)
    
    return format_sast(dt, format_str)

def get_current_datetime_sast():
    """
    Get the current datetime in South African Standard Time (SAST)
    
    Returns:
        str: Current datetime formatted as string
    """
    return format_datetime(now_sast())

def format_date_for_display(dt):
    """
    Format a date for display in the UI
    
    Args:
        dt (datetime): Datetime to format
        
    Returns:
        str: Formatted date string
    """
    return format_datetime(dt, "%d %B %Y")  # e.g., "01 May 2025"

def format_time_for_display(dt):
    """
    Format a time for display in the UI
    
    Args:
        dt (datetime): Datetime to format
        
    Returns:
        str: Formatted time string
    """
    return format_datetime(dt, "%H:%M")  # e.g., "14:30"

def format_datetime_for_display(dt):
    """
    Format a datetime for display in the UI
    
    Args:
        dt (datetime): Datetime to format
        
    Returns:
        str: Formatted datetime string
    """
    return format_datetime(dt, "%d %B %Y at %H:%M")  # e.g., "01 May 2025 at 14:30"