#!/usr/bin/env python
"""
Script to import the most recent lottery data Excel spreadsheet in the attached_assets directory.
This handles dynamic filenames with timestamps automatically.
"""

import os
import sys
import glob
import logging
import argparse
from datetime import datetime
# Import these inside functions to avoid circular imports
# from import_excel import import_excel_data
# from import_snap_lotto_data import import_snap_lotto_data
# import main  # Import main to get Flask application context

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_latest_spreadsheet(directory="attached_assets", pattern="lottery_data_*.xlsx"):
    """
    Find the most recent Excel spreadsheet matching the pattern in the specified directory.
    If no files match the specified pattern, try to find any Excel file.
    
    Args:
        directory (str): Directory to search in
        pattern (str): Filename pattern to match
        
    Returns:
        str: Path to the most recent matching file, or None if not found
    """
    # Get full path to the directory for the primary pattern
    search_path = os.path.join(directory, pattern)
    matching_files = glob.glob(search_path)
    
    # If no files match the primary pattern, try other common patterns
    if not matching_files:
        logger.warning(f"No files matching '{pattern}' found in '{directory}', trying alternative patterns...")
        alternative_patterns = ["*.xlsx", "lottery*.xlsx", "*lottery*.xlsx", "*data*.xlsx"]
        
        for alt_pattern in alternative_patterns:
            alt_search_path = os.path.join(directory, alt_pattern)
            matching_files = glob.glob(alt_search_path)
            if matching_files:
                logger.info(f"Found files matching alternative pattern '{alt_pattern}'")
                break
    
    # If still no files found, try to find any Excel files in the uploads folder
    if not matching_files:
        uploads_dir = "uploads"
        if os.path.exists(uploads_dir):
            uploads_search_path = os.path.join(uploads_dir, "*.xlsx")
            matching_files = glob.glob(uploads_search_path)
            if matching_files:
                logger.info(f"Found Excel files in the uploads directory")
    
    # If no matching files found after all attempts
    if not matching_files:
        logger.error(f"No Excel files found in '{directory}' or in uploads directory")
        return None
    
    # Find the most recently modified file
    latest_file = max(matching_files, key=os.path.getmtime)
    logger.info(f"Found latest spreadsheet: {latest_file}")
    return latest_file

def import_latest_spreadsheet(directory="attached_assets", pattern="lottery_data_*.xlsx", 
                             import_type="excel", purge=False):
    """
    Import the most recent lottery spreadsheet from the specified directory.
    
    Args:
        directory (str): Directory to search in
        pattern (str): Filename pattern to match
        import_type (str): Type of import to perform ("excel" or "snap_lotto")
        purge (bool): Whether to purge existing data before import
        
    Returns:
        bool: Success status
    """
    # Import here to avoid circular imports
    import main
    from import_excel import import_excel_data
    from import_snap_lotto_data import import_snap_lotto_data
    from models import ImportHistory, ImportedRecord, db
    from flask_login import current_user
    
    latest_file = find_latest_spreadsheet(directory, pattern)
    
    if not latest_file:
        return False
    
    logger.info(f"Starting import of {latest_file} using {import_type} importer")
    
    # Handle different import types
    with main.app.app_context():
        # Add explicit warnings about data import to ensure we never miss rows
        logger.warning("⚠️ CRITICAL: Only skipping the header row to prevent data loss")
        logger.warning("⚠️ REMINDER: Previous bug was skipping first 4 rows causing lottery results to be missed")
        
        if import_type.lower() == "excel":
            # Call the import function with detailed logging
            result = import_excel_data(latest_file, main.app)
            
            # Detailed logging of import results for verification
            if result and isinstance(result, dict):
                logger.info(f"Successfully imported {result.get('total', 0)} records")
                logger.info(f"Records before: {result.get('initial_count', 0)}, after: {result.get('final_count', 0)}")
                logger.info(f"Added {result.get('added', 0)} new records with {result.get('errors', 0)} errors")
                
                # Create import history record
                try:
                    # Create import history record
                    import_history = ImportHistory(
                        import_type='excel',
                        file_name=os.path.basename(latest_file),
                        records_added=result.get('added', 0),
                        records_updated=result.get('updated', 0),
                        total_processed=result.get('total', 0),
                        errors=result.get('errors', 0),
                        user_id=current_user.id if hasattr(current_user, 'id') else None
                    )
                    db.session.add(import_history)
                    db.session.commit()
                    
                    # Save individual imported records if available
                    imported = result.get('imported_records', [])
                    if imported and len(imported) > 0:
                        logger.info(f"First imported record: {imported[0]}")
                        
                        for record_data in imported:
                            if 'lottery_result_id' in record_data and record_data['lottery_result_id']:
                                imported_record = ImportedRecord(
                                    import_id=import_history.id,
                                    lottery_type=record_data.get('lottery_type', ''),
                                    draw_number=record_data.get('draw_number', ''),
                                    draw_date=record_data.get('draw_date'),
                                    is_new=record_data.get('is_new', True),
                                    lottery_result_id=record_data['lottery_result_id']
                                )
                                db.session.add(imported_record)
                        
                        db.session.commit()
                        logger.info(f"Saved {len(imported)} records to import history")
                except Exception as e:
                    logger.error(f"Error creating import history: {str(e)}")
                    db.session.rollback()
                
            return result
            
        elif import_type.lower() == "snap_lotto":
            result = import_snap_lotto_data(latest_file, main.app)
            
            # Add more detailed logging for snap_lotto imports
            if result and isinstance(result, dict):
                logger.info(f"Successfully imported {result.get('total', 0)} records")
                logger.info(f"Records before: {result.get('initial_count', 0)}, after: {result.get('final_count', 0)}")
                logger.info(f"Added {result.get('added', 0)} new records with {result.get('errors', 0)} errors")
                
                # Create import history record
                try:
                    # Create import history record
                    import_history = ImportHistory(
                        import_type='snap_lotto',
                        file_name=os.path.basename(latest_file),
                        records_added=result.get('added', 0),
                        records_updated=result.get('updated', 0),
                        total_processed=result.get('total', 0),
                        errors=result.get('errors', 0),
                        user_id=current_user.id if hasattr(current_user, 'id') else None
                    )
                    db.session.add(import_history)
                    db.session.commit()
                    
                    # Save individual imported records if available
                    imported = result.get('imported_records', [])
                    if imported and len(imported) > 0:
                        logger.info(f"First imported record: {imported[0]}")
                        
                        for record_data in imported:
                            if 'lottery_result_id' in record_data and record_data['lottery_result_id']:
                                imported_record = ImportedRecord(
                                    import_id=import_history.id,
                                    lottery_type=record_data.get('lottery_type', ''),
                                    draw_number=record_data.get('draw_number', ''),
                                    draw_date=record_data.get('draw_date'),
                                    is_new=record_data.get('is_new', True),
                                    lottery_result_id=record_data['lottery_result_id']
                                )
                                db.session.add(imported_record)
                        
                        db.session.commit()
                        logger.info(f"Saved {len(imported)} records to import history")
                except Exception as e:
                    logger.error(f"Error creating import history: {str(e)}")
                    db.session.rollback()
            
            return result
            
        else:
            logger.error(f"Unknown import type: {import_type}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import most recent lottery data spreadsheet')
    parser.add_argument('--directory', '-d', default='attached_assets',
                        help='Directory containing spreadsheets (default: attached_assets)')
    parser.add_argument('--pattern', '-p', default='lottery_data_*.xlsx',
                        help='Filename pattern to match (default: lottery_data_*.xlsx)')
    parser.add_argument('--type', '-t', default='excel', choices=['excel', 'snap_lotto'],
                        help='Type of import to perform (default: excel)')
    
    args = parser.parse_args()
    
    success = import_latest_spreadsheet(args.directory, args.pattern, args.type)
    
    if success:
        logger.info("Import completed successfully!")
        sys.exit(0)
    else:
        logger.error("Import failed!")
        sys.exit(1)