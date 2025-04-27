#!/usr/bin/env python3
"""
Script to specifically test and fix the issue with row 2 data (Lottery 2536)
in Excel imports.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_row2')

def test_excel_import(file_path, sheet_name=None):
    """
    Test the Excel import functionality specifically for row 2 data.
    Directly calls the improved Excel import functions and prints the results.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Optional sheet name to import
    """
    try:
        # Import the functions we need
        from improved_excel_import import import_excel_file
        from integrate_excel_import import normalize_lottery_type
        
        logger.info(f"Testing Excel import with file: {file_path}, sheet: {sheet_name or 'default'}")
        
        # Import the Excel file
        records = import_excel_file(file_path, sheet_name)
        
        # Check for records
        if not records:
            logger.error("No records found in the Excel file.")
            return False
            
        logger.info(f"Found {len(records)} records in the Excel file.")
        
        # Print the first few records to check for "Lottery 2536" type data
        for i, record in enumerate(records[:5]):
            game_name = record.get('game_name', 'Unknown')
            draw_number = record.get('draw_number', 'Unknown')
            
            # Check if this is the problematic "Lottery 2536" format
            import re
            match = re.match(r'(lottery|lotto)\s+(\d+)', str(game_name).strip().lower())
            
            if match:
                logger.info(f"Found problematic format in record {i+1}: {game_name}")
                extracted_number = match.group(2)
                logger.info(f"  Extracted draw number: {extracted_number}")
                logger.info(f"  Current draw number value: {draw_number}")
                
                # Check if we correctly normalized the lottery type
                normalized = normalize_lottery_type(game_name)
                logger.info(f"  Normalized lottery type: {normalized}")
                
                if normalized == "Lottery" and str(draw_number) == str(extracted_number):
                    logger.info("  ✓ This record was correctly processed!")
                else:
                    logger.warning("  ✗ This record has issues. Check normalization and draw number extraction.")
            
            # Print the full record for reference
            logger.info(f"Record {i+1}:")
            for key, value in sorted(record.items()):
                logger.info(f"  {key}: {value}")
                
        return True
            
    except Exception as e:
        logger.error(f"Error testing Excel import: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Test Excel import specifically for row 2 data.')
    parser.add_argument('file_path', help='Path to the Excel file to test')
    parser.add_argument('--sheet', help='Specific sheet to test', default=None)
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.file_path):
        logger.error(f"File not found: {args.file_path}")
        return 1
        
    success = test_excel_import(args.file_path, args.sheet)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())