#!/usr/bin/env python3
"""
Re-import lottery data from Excel files to ensure bonus numbers are correctly processed
with the enhanced parsing logic.
"""

import os
import glob
import sys
import json
import logging
from datetime import datetime
from single_sheet_import import import_single_sheet

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reimport_all_excel_files(directory='attached_assets'):
    """
    Reimport all Excel files in the specified directory
    using the enhanced bonus number detection.
    
    Args:
        directory (str): Directory containing Excel files
        
    Returns:
        dict: Import statistics
    """
    logger.info(f"Searching for Excel files in {directory}")
    excel_files = glob.glob(os.path.join(directory, '*.xlsx'))
    
    if not excel_files:
        logger.warning(f"No Excel files found in {directory}")
        return {'success': False, 'error': f'No Excel files found in {directory}'}
    
    logger.info(f"Found {len(excel_files)} Excel files")
    
    results = {
        'files_processed': 0,
        'total_draws_imported': 0,
        'errors': 0,
        'by_file': {}
    }
    
    for excel_file in excel_files:
        logger.info(f"Processing file: {excel_file}")
        
        try:
            import_result = import_single_sheet(excel_file)
            
            file_basename = os.path.basename(excel_file)
            results['by_file'][file_basename] = import_result
            
            if import_result.get('success', False):
                results['files_processed'] += 1
                results['total_draws_imported'] += import_result.get('stats', {}).get('imported', 0)
            else:
                results['errors'] += 1
                
        except Exception as e:
            logger.error(f"Error processing file {excel_file}: {str(e)}")
            results['errors'] += 1
            results['by_file'][os.path.basename(excel_file)] = {
                'success': False,
                'error': str(e)
            }
    
    logger.info(f"Reimport completed. Stats: {results}")
    return results

def reimport_specific_file(excel_path):
    """
    Reimport a specific Excel file using the enhanced bonus number detection.
    
    Args:
        excel_path (str): Path to Excel file
        
    Returns:
        dict: Import statistics
    """
    logger.info(f"Reimporting file: {excel_path}")
    
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
        return {'success': False, 'error': f'Excel file not found: {excel_path}'}
    
    try:
        import_result = import_single_sheet(excel_path)
        logger.info(f"Reimport completed. Stats: {import_result}")
        return import_result
    except Exception as e:
        logger.error(f"Error processing file {excel_path}: {str(e)}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
        result = reimport_specific_file(excel_path)
    else:
        result = reimport_all_excel_files()
    
    print(json.dumps(result, indent=2))