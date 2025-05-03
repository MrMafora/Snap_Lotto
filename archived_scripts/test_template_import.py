#!/usr/bin/env python3
"""
Direct test script for multi-sheet template import without running the full app.
This tests the import of the template file directly.
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_import(template_path, verbose=False):
    """Test direct import of template file without the Flask app"""
    logger.info(f"Testing import of template file: {template_path}")
    
    # Import the module
    try:
        import multi_sheet_import
        logger.info("Successfully imported multi_sheet_import module")
    except ImportError as e:
        logger.error(f"Failed to import multi_sheet_import module: {e}")
        return False
    
    # Try to import the file
    try:
        # Run without Flask context, so data is processed but not saved to database
        import_stats = multi_sheet_import.import_multisheet_excel(template_path)
        
        # Print results
        if import_stats['success']:
            logger.info("Template import successful")
            logger.info(f"  Total rows processed: {import_stats['total']}")
            logger.info(f"  Rows that would be added: {import_stats['added']}")
            logger.info(f"  Rows that would be updated: {import_stats['updated']}")
            logger.info(f"  Errors: {import_stats['errors']}")
            
            # If verbose, print record details
            if verbose and 'imported_records' in import_stats:
                logger.info("Processed records:")
                for i, record in enumerate(import_stats['imported_records']):
                    logger.info(f"  Record {i+1}:")
                    for key, value in record.items():
                        logger.info(f"    {key}: {value}")
            return True
        else:
            error = import_stats.get('error', 'Unknown error')
            logger.error(f"Template import failed: {error}")
            return False
    except Exception as e:
        logger.error(f"Error during template import: {e}")
        if verbose:
            import traceback
            logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Get template file path from command line or use default
    if len(sys.argv) > 1:
        template_path = sys.argv[1]
    else:
        template_path = "attached_assets/lottery_data_template_new.xlsx"
    
    # Check if file exists
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        sys.exit(1)
    
    # Run the test
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    success = test_direct_import(template_path, verbose)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)