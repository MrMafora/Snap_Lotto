import pandas as pd
import logging
import traceback
import os
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_excel_structure(excel_path):
    """
    Debug the Excel file structure and print detailed diagnostics
    
    Args:
        excel_path (str): Path to the Excel file
        
    Returns:
        None: Just prints diagnostic information
    """
    try:
        logger.info(f"Analyzing Excel file: {excel_path}")
        
        # Check if file exists
        if not os.path.exists(excel_path):
            logger.error(f"File does not exist: {excel_path}")
            return
            
        # Get file info
        file_size = os.path.getsize(excel_path)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(excel_path))
        logger.info(f"File size: {file_size} bytes")
        logger.info(f"Last modified: {file_mtime}")
        
        # Try reading with pandas
        logger.info("Attempting to read Excel file with pandas...")
        try:
            # First try with default arguments
            xls = pd.ExcelFile(excel_path)
            sheet_names = xls.sheet_names
            logger.info(f"Excel sheets found: {sheet_names}")
            
            for sheet_name in sheet_names:
                logger.info(f"Reading sheet: {sheet_name}")
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                
                # Get basic info about the dataframe
                logger.info(f"Shape: {df.shape}")
                if not df.empty:
                    logger.info(f"Columns: {list(df.columns)}")
                    
                    # Print first few rows
                    logger.info("First 5 rows:")
                    for i, row in df.head().iterrows():
                        logger.info(f"Row {i}: {row.to_dict()}")
                else:
                    logger.warning(f"Sheet '{sheet_name}' is empty")
        except Exception as e:
            logger.error(f"Error reading Excel with pandas: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Try with different arguments
            logger.info("Trying with engine='openpyxl'...")
            try:
                xls = pd.ExcelFile(excel_path, engine='openpyxl')
                sheet_names = xls.sheet_names
                logger.info(f"Excel sheets found with openpyxl: {sheet_names}")
                
                for sheet_name in sheet_names:
                    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine='openpyxl')
                    logger.info(f"Sheet '{sheet_name}' shape: {df.shape}")
            except Exception as e:
                logger.error(f"Error with openpyxl engine: {str(e)}")
                
    except Exception as e:
        logger.error(f"Unexpected error during Excel analysis: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "attached_assets/lottery_data_template_new.xlsx"
    
    debug_excel_structure(excel_path)