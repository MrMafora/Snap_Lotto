"""
Timezone utilities for handling South African Standard Time (SAST) conversions.
"""
from datetime import datetime, timedelta, timezone

# South Africa Standard Time is UTC+2
SAST = timezone(timedelta(hours=2))

def utc_to_sast(utc_dt):
    """
    Convert a UTC datetime to South African Standard Time (SAST)
    
    Args:
        utc_dt (datetime): UTC datetime object (timezone-aware or naive)
        
    Returns:
        datetime: SAST datetime object (timezone-aware)
    """
    # Ensure we have a timezone-aware UTC datetime
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    # Convert to SAST
    sast_dt = utc_dt.astimezone(SAST)
    
    return sast_dt

def sast_to_utc(sast_dt):
    """
    Convert a South African Standard Time (SAST) datetime to UTC
    
    Args:
        sast_dt (datetime): SAST datetime object (timezone-aware or naive)
        
    Returns:
        datetime: UTC datetime object (timezone-aware)
    """
    # If the datetime is naive, assume it's in SAST
    if sast_dt.tzinfo is None:
        sast_dt = sast_dt.replace(tzinfo=SAST)
    
    # Convert to UTC
    utc_dt = sast_dt.astimezone(timezone.utc)
    
    return utc_dt

def now_sast():
    """
    Get the current time in South African Standard Time (SAST)
    
    Returns:
        datetime: Current time in SAST (timezone-aware)
    """
    return datetime.now(SAST)

def format_sast(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format a datetime in South African format
    
    Args:
        dt (datetime): Datetime object (timezone-aware or naive)
        format_str (str): Format string for datetime
        
    Returns:
        str: Formatted datetime string in SAST
    """
    # Convert to SAST if it's a timezone-aware datetime
    if dt.tzinfo is not None:
        dt = dt.astimezone(SAST)
    # Otherwise, assume it's already in SAST
    
    return dt.strftime(format_str)

def parse_sast_str(date_str, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Parse a date string in SAST timezone
    
    Args:
        date_str (str): Date string to parse
        format_str (str): Format string for datetime
        
    Returns:
        datetime: SAST datetime object (timezone-aware)
    """
    dt = datetime.strptime(date_str, format_str)
    dt = dt.replace(tzinfo=SAST)
    return dt

def get_sast_date_only(dt=None):
    """
    Get just the date part of a datetime in SAST, defaulting to today
    
    Args:
        dt (datetime, optional): Datetime to extract date from. Defaults to current time.
        
    Returns:
        datetime.date: Date in SAST
    """
    if dt is None:
        dt = now_sast()
    elif dt.tzinfo is not None and dt.tzinfo != SAST:
        dt = dt.astimezone(SAST)
        
    return dt.date()