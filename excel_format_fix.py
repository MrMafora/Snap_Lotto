import pandas as pd
import logging
import os
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_excel_import(excel_path):
    """
    Direct fix for Excel import issues with lottery data.
    This script handles various Excel formats and ensures proper importing
    of all lottery types including Daily Lottery and PowerBall.
    
    Args:
        excel_path (str): Path to the Excel file to process
    
    Returns:
        dict: Summary of processed data
    """
    logger.info(f"Starting Excel format fix for: {excel_path}")
    
    # Check if file exists
    if not os.path.exists(excel_path):
        logger.error(f"File not found: {excel_path}")
        return {"error": "File not found"}
    
    try:
        # Get file info
        file_size = os.path.getsize(excel_path)
        logger.info(f"Excel file size: {file_size} bytes")

        # Try multiple engines for maximum compatibility
        df = None
        errors = []
        
        # Try openpyxl (modern Excel files)
        try:
            logger.info("Trying openpyxl engine...")
            df = pd.read_excel(excel_path, engine="openpyxl")
        except Exception as e:
            errors.append(f"openpyxl error: {str(e)}")
            logger.warning(f"Failed with openpyxl: {str(e)}")
        
        # Try xlrd (older Excel files)
        if df is None:
            try:
                logger.info("Trying xlrd engine...")
                df = pd.read_excel(excel_path, engine="xlrd")
            except Exception as e:
                errors.append(f"xlrd error: {str(e)}")
                logger.warning(f"Failed with xlrd: {str(e)}")
        
        # Try default engine
        if df is None:
            try:
                logger.info("Trying default engine...")
                df = pd.read_excel(excel_path)
            except Exception as e:
                errors.append(f"default engine error: {str(e)}")
                logger.error(f"All engines failed: {str(e)}")
                return {"error": f"Could not read Excel file: {str(e)}"}
        
        # Check for empty dataframe
        if df is None or df.empty:
            logger.error("Dataframe is empty")
            return {"error": "Excel file contains no data"}
        
        # Check all sheets if main one is empty
        if len(df.columns) < 2:  # Not enough columns
            logger.info("First sheet has too few columns, checking all sheets...")
            xlsx = pd.ExcelFile(excel_path)
            
            for sheet_name in xlsx.sheet_names:
                logger.info(f"Checking sheet: {sheet_name}")
                if sheet_name.lower() in ['instructions', 'info', 'readme']:
                    continue  # Skip instruction sheets
                    
                sheet_df = pd.read_excel(excel_path, sheet_name=sheet_name)
                if not sheet_df.empty and len(sheet_df.columns) >= 3:
                    logger.info(f"Using data from sheet: {sheet_name}")
                    df = sheet_df
                    break
            
        # Report on what we found
        logger.info(f"Columns found: {', '.join(str(col) for col in df.columns)}")
        
        # Extract all lottery types
        lottery_types = set()
        
        # Look for "Game Name" or similar column
        game_name_col = None
        for col in df.columns:
            if str(col).lower() in ['game name', 'game type', 'lottery type', 'lottery']:
                game_name_col = col
                break
                
        if game_name_col:
            # Extract all game types
            for index, row in df.iterrows():
                game = row[game_name_col]
                if isinstance(game, str) and game.strip():
                    normalized = normalize_lottery_type(game.strip())
                    lottery_types.add(normalized)
                
        logger.info(f"Lottery types found: {', '.join(lottery_types)}")
        
        # Return info about what was found
        return {
            "status": "success",
            "file_size": file_size,
            "rows": len(df),
            "columns": list(df.columns),
            "lottery_types": list(lottery_types)
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        return {"error": f"Error processing Excel file: {str(e)}"}

def normalize_lottery_type(lottery_type):
    """
    Normalize lottery type names, prioritizing "Lottery" terminology.
    
    Args:
        lottery_type (str): The lottery type name
        
    Returns:
        str: Normalized lottery type
    """
    if not lottery_type:
        return "Unknown"
    
    # Convert to uppercase for case-insensitive matching
    upper_type = lottery_type.upper()
    
    # Prioritize "Lottery" terminology
    if upper_type == 'LOTTO' or upper_type == 'LOTTERY':
        return 'Lottery'
    elif 'LOTTERY PLUS 1' in upper_type or 'LOTTO PLUS 1' in upper_type:
        return 'Lottery Plus 1'
    elif 'LOTTERY PLUS 2' in upper_type or 'LOTTO PLUS 2' in upper_type:
        return 'Lottery Plus 2' 
    elif 'POWERBALL PLUS' in upper_type:
        return 'Powerball Plus'
    elif 'POWERBALL' in upper_type:
        return 'Powerball'
    elif 'DAILY LOTTERY' in upper_type or 'DAILY LOTTO' in upper_type:
        return 'Daily Lottery'
        
    # If no match, return original with proper capitalization
    return lottery_type.strip()

# When run directly, analyze the most recent Excel file
if __name__ == "__main__":
    # Find the most recent Excel file
    excel_files = []
    
    # Check in uploads directory
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir) and os.path.isdir(uploads_dir):
        for filename in os.listdir(uploads_dir):
            if filename.endswith(".xlsx") or filename.endswith(".xls"):
                full_path = os.path.join(uploads_dir, filename)
                excel_files.append((full_path, os.path.getmtime(full_path)))
                
    # Check in attached_assets directory
    assets_dir = "attached_assets"
    if os.path.exists(assets_dir) and os.path.isdir(assets_dir):
        for filename in os.listdir(assets_dir):
            if filename.endswith(".xlsx") or filename.endswith(".xls"):
                full_path = os.path.join(assets_dir, filename)
                excel_files.append((full_path, os.path.getmtime(full_path)))
    
    # Sort by modification time (newest first)
    excel_files.sort(key=lambda x: x[1], reverse=True)
    
    if excel_files:
        newest_file = excel_files[0][0]
        logger.info(f"Processing newest Excel file: {newest_file}")
        result = fix_excel_import(newest_file)
        print(json.dumps(result, indent=2))
    else:
        logger.error("No Excel files found in uploads or attached_assets directories")