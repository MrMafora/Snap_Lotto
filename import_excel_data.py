#!/usr/bin/env python
"""
Command line tool for importing lottery data from Excel files.
This combines the improved Excel import functionality with the 
Flask application context for database operations.

Usage:
  python import_excel_data.py <excel_file_path> [--sheet SHEET_NAME]

Examples:
  python import_excel_data.py lottery_data.xlsx
  python import_excel_data.py lottery_data.xlsx --sheet "Lottery"
"""
import os
import sys
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Import lottery data from Excel file')
    parser.add_argument('file_path', help='Path to the Excel file')
    parser.add_argument('--sheet', help='Optional specific sheet to import', default=None)
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Set log level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting import from {args.file_path}")
    if args.sheet:
        logger.info(f"Using sheet: {args.sheet}")
    
    # Check if file exists
    if not os.path.isfile(args.file_path):
        logger.error(f"File not found: {args.file_path}")
        sys.exit(1)
    
    try:
        # Import the integration module
        from integrate_excel_import import run_import
        
        # Run the import
        start_time = datetime.now()
        logger.info(f"Import started at {start_time}")
        
        success_count, error_count, error_messages = run_import(args.file_path, args.sheet)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print summary
        logger.info("-" * 50)
        logger.info(f"Import Summary:")
        logger.info(f"  File: {args.file_path}")
        if args.sheet:
            logger.info(f"  Sheet: {args.sheet}")
        logger.info(f"  Duration: {duration}")
        logger.info(f"  Success: {success_count} records")
        logger.info(f"  Errors: {error_count} records")
        
        if error_count > 0:
            logger.info("\nError details:")
            for i, msg in enumerate(error_messages):
                logger.info(f"  {i+1}. {msg}")
        
        logger.info("-" * 50)
        
        # Return status code
        if error_count > 0:
            logger.warning("Import completed with errors.")
            sys.exit(1)
        else:
            logger.info("Import completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Import cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()