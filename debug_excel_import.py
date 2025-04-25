#!/usr/bin/env python
"""
Excel row processing debug script.
This script will analyze the Excel file structure and show exactly which rows
are being skipped and why.
"""

import os
import sys
import logging
import pandas as pd
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_excel_file(excel_file):
    """Analyze Excel file structure and data rows"""
    logger.info(f"Analyzing Excel file: {excel_file}")
    
    try:
        # First read without skipping
        df_raw = pd.read_excel(excel_file)
        logger.info(f"Excel columns (original): {', '.join(str(col) for col in df_raw.columns)}")
        logger.info(f"Total rows (original): {len(df_raw)}")
        
        # Show first 3 rows of raw data
        for i in range(min(3, len(df_raw))):
            logger.info(f"RAW ROW {i}: {df_raw.iloc[i].to_dict()}")
        
        # Now try with skip_header
        df = df_raw.iloc[1:].reset_index(drop=True)
        logger.info(f"Total rows (after header skip): {len(df)}")
        
        # Show first 3 rows of processed data
        for i in range(min(3, len(df))):
            # This corresponds to rows 2, 3, 4 in Excel (indexes 1, 2, 3)
            logger.info(f"PROCESSED ROW {i} (Excel row {i+2}): {df.iloc[i].to_dict()}")
        
        # Check emptiness
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            empty_percentage = row.isna().sum() / len(row) * 100
            logger.info(f"ROW {i} (Excel {i+2}) - Empty fields: {row.isna().sum()}/{len(row)} ({empty_percentage:.1f}%)")
            
            # Check if row would be skipped by 50% rule vs 75% rule
            if row.isna().sum() > len(row) * 0.5:
                logger.warning(f"ROW {i} would be SKIPPED with 50% empty threshold")
            if row.isna().sum() > len(row) * 0.75:
                logger.warning(f"ROW {i} would be SKIPPED with 75% empty threshold")
        
        return True
    except Exception as e:
        logger.error(f"Error analyzing Excel file: {str(e)}")
        return False

if __name__ == "__main__":
    # Get the latest Excel file
    excel_files = []
    directory = "attached_assets"
    pattern = "lottery_data_"
    
    for filename in os.listdir(directory):
        if pattern in filename and filename.endswith(".xlsx"):
            excel_files.append(os.path.join(directory, filename))
    
    if not excel_files:
        logger.error("No Excel files found")
        sys.exit(1)
    
    # Use the most recent file
    latest_file = max(excel_files, key=os.path.getmtime)
    logger.info(f"Using most recent file: {latest_file}")
    
    # Analyze the file
    analyze_excel_file(latest_file)