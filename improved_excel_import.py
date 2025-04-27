"""
Improved Excel import functionality for lottery data
This module adds more robust handling of Excel spreadsheets, with better error messages
and column identification regardless of header names.
"""
import os
import sys
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for column identification
EXPECTED_COLUMNS = {
    'game_name': ['Game Name', 'Lottery Type', 'Game Type', 'Game', 'Type'],
    'draw_number': ['Draw Number', 'Draw #', 'Draw No', 'Drawing Number'],
    'draw_date': ['Draw Date', 'Date', 'Drawing Date'],
    'winning_numbers': ['Winning Numbers', 'Winning Numbers (Numerical)', 'Numbers', 'Main Numbers'],
    'bonus_ball': ['Bonus Ball', 'Bonus', 'Powerball', 'Bonus Number', 'Extra Ball'],
    'div_winners': ['Winners', 'Div Winners'],
    'div_winnings': ['Winnings', 'Prize', 'Div Winnings']
}

class ExcelImportError(Exception):
    """Custom exception for Excel import errors"""
    pass

def identify_column(df: pd.DataFrame, column_types: List[str]) -> Optional[str]:
    """
    Find a column in the DataFrame that matches one of the column types.
    
    Args:
        df: DataFrame containing the data
        column_types: List of possible column names
        
    Returns:
        Column name if found, None otherwise
    """
    # Convert all column names to strings just in case
    df_columns = [str(col) for col in df.columns]
    
    # Look for exact matches first
    for col_type in column_types:
        if col_type in df_columns:
            return col_type
            
    # Try case-insensitive matches
    for col_type in column_types:
        for col in df_columns:
            if col_type.lower() == col.lower():
                return col
                
    # Try partial matches
    for col_type in column_types:
        for col in df_columns:
            if col_type.lower() in col.lower() or col.lower() in col_type.lower():
                return col
                
    # Check unnamed columns with header data
    if 'Unnamed: 0' in df_columns and len(df) > 3:
        # Check if we have header information in row 3
        header_row = df.iloc[3]
        for i, header_val in enumerate(header_row):
            if header_val and isinstance(header_val, str):
                col_name = f'Unnamed: {i}'
                if col_name in df_columns:
                    for col_type in column_types:
                        if col_type.lower() in header_val.lower() or header_val.lower() in col_type.lower():
                            return col_name
    
    return None

def extract_lottery_data(file_path: str, sheet_name: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Extract lottery data from Excel file with better error handling and column identification.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Specific sheet to import, or None for first sheet
        
    Returns:
        Tuple of (processed_df, column_mapping)
    """
    try:
        # Read all sheets or specific sheet
        if sheet_name:
            logger.info(f"Reading sheet '{sheet_name}' from {file_path}")
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except ValueError:
                sheets = pd.ExcelFile(file_path).sheet_names
                raise ExcelImportError(f"Sheet '{sheet_name}' not found. Available sheets: {', '.join(sheets)}")
        else:
            logger.info(f"Reading first sheet from {file_path}")
            sheets = pd.ExcelFile(file_path).sheet_names
            if not sheets:
                raise ExcelImportError(f"No sheets found in {file_path}")
            df = pd.read_excel(file_path, sheet_name=sheets[0])
            sheet_name = sheets[0]
    except Exception as e:
        raise ExcelImportError(f"Error reading Excel file: {str(e)}")
    
    # Check if dataframe is empty
    if df.empty:
        raise ExcelImportError(f"No data found in sheet '{sheet_name}'")
        
    # The first few rows might be metadata or headers
    # Try to identify if we need to skip rows by looking for known column names
    start_row = 0
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        potential_headers = [str(val).lower() for val in row if str(val).lower() != 'nan']
        matches = 0
        for column_types in EXPECTED_COLUMNS.values():
            for col_type in column_types:
                if any(col_type.lower() in header for header in potential_headers):
                    matches += 1
        
        if matches >= 3:  # Threshold to consider this a header row
            logger.info(f"Found potential header row at index {i}")
            start_row = i
            break
    
    # If we found a header row, reset the dataframe to use this as header
    if start_row > 0:
        header_row = df.iloc[start_row]
        # Start from the FIRST data row (don't skip row 2)
        df = df.iloc[start_row+1:].reset_index(drop=True)
        df.columns = header_row
        
        # Debug log to verify data is being read
        logger.info(f"Processing {len(df)} data rows starting with row 2")
        if len(df) > 0:
            logger.info(f"First row data: {df.iloc[0].to_dict()}")
    
    # Identify columns
    column_mapping = {}
    for col_key, col_types in EXPECTED_COLUMNS.items():
        identified_col = identify_column(df, col_types)
        if identified_col:
            column_mapping[col_key] = identified_col
            
    # Check if we have the minimum required columns
    minimum_columns = ['game_name', 'draw_number', 'draw_date', 'winning_numbers']
    missing_columns = [col for col in minimum_columns if col not in column_mapping]
    
    if missing_columns:
        raise ExcelImportError(
            f"Missing required columns: {', '.join(missing_columns)}. "
            f"Available columns: {', '.join(str(c) for c in df.columns)}"
        )
    
    # Clean up the data
    # Convert date columns if found
    if 'draw_date' in column_mapping:
        date_col = column_mapping['draw_date']
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        except Exception as e:
            logger.warning(f"Could not convert column {date_col} to date: {str(e)}")
    
    # Ensure draw numbers are integers
    if 'draw_number' in column_mapping:
        draw_col = column_mapping['draw_number']
        try:
            df[draw_col] = pd.to_numeric(df[draw_col], errors='coerce').fillna(0).astype(int)
        except Exception as e:
            logger.warning(f"Could not convert column {draw_col} to integers: {str(e)}")
            
    return df, column_mapping

def process_row(row: pd.Series, column_mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Process a single row into a dictionary with standardized keys.
    
    Args:
        row: DataFrame row
        column_mapping: Mapping of standard keys to actual column names
        
    Returns:
        Dictionary with standardized data
    """
    result = {}
    
    # Extract basic fields
    for std_key, col_name in column_mapping.items():
        if col_name in row and pd.notna(row[col_name]):
            result[std_key] = row[col_name]
        else:
            result[std_key] = None
            
    # Handle special case where draw number is embedded in game name (like "Lottery 2536")
    if 'game_name' in result and result['game_name'] is not None:
        import re
        match = re.match(r'(lottery|lotto)\s+(\d+)', str(result['game_name']).strip().lower())
        if match and ('draw_number' not in result or result['draw_number'] is None):
            # Extract the draw number from the game name
            draw_number = match.group(2)
            logger.info(f"Extracted draw number {draw_number} from game name '{result['game_name']}'")
            result['draw_number'] = draw_number
            
    # Special handling for winning numbers
    if 'winning_numbers' in result and result['winning_numbers'] is not None:
        # Try to convert winning numbers to a list of integers
        try:
            # Handle different formats (comma-separated, space-separated, etc.)
            numbers_str = str(result['winning_numbers'])
            numbers_str = numbers_str.replace('[', '').replace(']', '')
            
            # Try comma first, then space
            if ',' in numbers_str:
                numbers = [int(n.strip()) for n in numbers_str.split(',') if n.strip().isdigit()]
            else:
                numbers = [int(n.strip()) for n in numbers_str.split() if n.strip().isdigit()]
                
            result['winning_numbers'] = numbers
        except Exception as e:
            logger.warning(f"Could not parse winning numbers: {result['winning_numbers']} - {str(e)}")
            result['winning_numbers'] = str(result['winning_numbers'])
    
    # Format dates consistently
    if 'draw_date' in result and result['draw_date'] is not None:
        if isinstance(result['draw_date'], datetime):
            result['draw_date'] = result['draw_date'].strftime('%Y-%m-%d')
        else:
            # Try to parse the date if it's not already a datetime
            try:
                dt = pd.to_datetime(result['draw_date'])
                result['draw_date'] = dt.strftime('%Y-%m-%d')
            except:
                pass
    
    return result

def import_excel_file(file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Import lottery data from an Excel file.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Specific sheet to import, or None for first sheet
        
    Returns:
        List of dictionaries with standardized lottery data
    """
    # Check if file exists
    if not os.path.isfile(file_path):
        raise ExcelImportError(f"File {file_path} does not exist")
        
    # Extract data with better error handling
    df, column_mapping = extract_lottery_data(file_path, sheet_name)
    
    # Process each row
    results = []
    for _, row in df.iterrows():
        try:
            processed_row = process_row(row, column_mapping)
            
            # Skip rows with no game name or draw number, but log them first
            if (processed_row.get('game_name') is None or 
                processed_row.get('draw_number') is None or 
                processed_row.get('draw_date') is None):
                logger.warning(f"Skipping row with incomplete data: {processed_row}")
                continue
                
            # Make sure we log successful rows with their key data
            logger.info(f"Processing valid row: {processed_row.get('game_name')} {processed_row.get('draw_number')}")
                
            results.append(processed_row)
        except Exception as e:
            logger.warning(f"Error processing row: {str(e)}")
            
    logger.info(f"Successfully imported {len(results)} records from {file_path}")
    return results

if __name__ == '__main__':
    # Handle command line arguments
    if len(sys.argv) < 2:
        print("Usage: python improved_excel_import.py <excel_file_path> [sheet_name]")
        sys.exit(1)
        
    file_path = sys.argv[1]
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        results = import_excel_file(file_path, sheet_name)
        print(f"Successfully imported {len(results)} records")
        
        # Print first 5 records for preview
        for i, record in enumerate(results[:5]):
            print(f"\nRecord {i+1}:")
            for key, value in record.items():
                print(f"  {key}: {value}")
    except ExcelImportError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)