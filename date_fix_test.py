"""
Debug script to directly test our Excel timestamp parsing logic.
This will pinpoint exactly what's going wrong with the date parsing.
"""

import sys
import importlib.util
import datetime
import json
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("date_fix_test")

def parse_date_directly(date_str):
    """Our own implementation of the date parsing logic for testing"""
    print(f"Trying to parse date: '{date_str}'")
    
    # If it's already a datetime object, return it directly
    if isinstance(date_str, datetime.datetime):
        print("  - Already a datetime object")
        return date_str
    
    # Convert to string if it's not already
    date_str = str(date_str).strip()
    print(f"  - Converted to string: '{date_str}'")
    
    # Explicit handling for Excel timestamp format (2025-04-05 00:00:00)
    if ' 00:00:00' in date_str:
        print("  - Detected Excel timestamp format with 00:00:00")
        date_part = date_str.split(' ')[0]  # Get '2025-04-05' part
        try:
            print(f"  - Extracted date part: '{date_part}'")
            parts = date_part.split('-')
            print(f"  - Split into parts: {parts}")
            if len(parts) == 3:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                print(f"  - Creating date with year={year}, month={month}, day={day}")
                # Create date with year, month, day directly
                return datetime.datetime(year, month, day)
        except Exception as e:
            print(f"  - ERROR: Failed to parse Excel timestamp: {e}")
            print(f"  - Traceback: {traceback.format_exc()}")
            # If explicit parsing fails, use a hardcoded replacement date
            return datetime.datetime(2025, 4, 1)  # Default date as fallback
    
    # Try various date formats in order of likelihood
    date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y']
    for fmt in date_formats:
        try:
            print(f"  - Trying format: {fmt}")
            result = datetime.datetime.strptime(date_str, fmt)
            print(f"  - SUCCESS with format {fmt}: {result}")
            return result
        except ValueError:
            print(f"  - Failed with format {fmt}")
            continue
    
    print("  - All parsing methods failed")
    return None

def test_standalone_parsing():
    """Test date parsing logic on a standalone basis"""
    test_dates = [
        '2025-04-05 00:00:00',
        '2025-04-04 00:00:00',
        '2025-03-31 00:00:00',
        '2025-04-25',
        '7/25/2025',
        '25/7/2025',
    ]
    
    print("===== TESTING STANDALONE DATE PARSING =====\n")
    
    for date_str in test_dates:
        print(f"\nTESTING DATE: {date_str}")
        result = parse_date_directly(date_str)
        print(f"RESULT: {result}")

def reload_import_modules():
    """Reload the import modules to ensure we're testing the latest code"""
    print("\n===== RELOADING IMPORT MODULES =====\n")
    try:
        # Load (or reload) the import_excel module
        import importlib
        import sys
        if 'import_excel' in sys.modules:
            importlib.reload(sys.modules['import_excel'])
            print("Reloaded import_excel module")
        else:
            import import_excel
            print("Imported import_excel module")
        
        # Test the module's parse_date function
        test_dates = [
            '2025-04-05 00:00:00',
            '2025-04-04 00:00:00'
        ]
        
        print("\nTesting import_excel.parse_date function:")
        for date_str in test_dates:
            result = import_excel.parse_date(date_str)
            print(f"  import_excel.parse_date('{date_str}') = {result}")
            
        if 'import_snap_lotto_data' in sys.modules:
            importlib.reload(sys.modules['import_snap_lotto_data'])
            print("Reloaded import_snap_lotto_data module")
        else:
            import import_snap_lotto_data
            print("Imported import_snap_lotto_data module")
            
        print("\nTesting import_snap_lotto_data.parse_date function:")
        for date_str in test_dates:
            result = import_snap_lotto_data.parse_date(date_str)
            print(f"  import_snap_lotto_data.parse_date('{date_str}') = {result}")
            
    except Exception as e:
        print(f"Error reloading modules: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        # Test our own implementation first
        test_standalone_parsing()
        
        # Then try to reload and test the module functions
        reload_import_modules()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()