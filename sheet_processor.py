import pandas as pd
import json
import logging
import os
from datetime import datetime
import traceback
import numpy as np
import sys
import re

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    upper_type = str(lottery_type).upper()
    
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
    return str(lottery_type).strip()

def parse_date(date_str):
    """
    Parse date from various formats to datetime object.
    
    Args:
        date_str: Date string or datetime object
        
    Returns:
        str: ISO format date string or None if parsing fails
    """
    if not date_str or pd.isna(date_str):
        return None
        
    if isinstance(date_str, datetime):
        return date_str.isoformat()
    
    try:
        # Try to parse date in different formats
        date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", 
                        "%Y/%m/%d", "%d.%m.%Y", "%Y.%m.%d"]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(date_str).split()[0], fmt)
                return parsed_date.isoformat()
            except ValueError:
                continue
    except Exception as e:
        logger.warning(f"Date parsing error: {str(e)}")
    
    return None

def parse_numbers(numbers_str):
    """
    Parse lottery numbers from string to list.
    
    Args:
        numbers_str: String containing numbers
        
    Returns:
        list: List of integers
    """
    if not numbers_str or pd.isna(numbers_str):
        return []
    
    # Handle numeric types
    if isinstance(numbers_str, (int, float)):
        return [int(numbers_str)]
    
    # Handle string types
    if isinstance(numbers_str, str):
        # Try different delimiters
        for delimiter in [',', ' ', ';']:
            parts = numbers_str.split(delimiter)
            if len(parts) > 1:
                try:
                    return [int(part.strip()) for part in parts if part.strip() and part.strip().isdigit()]
                except ValueError:
                    continue
    
    # If we couldn't parse anything, return empty list
    return []

def process_excel_sheets(file_path):
    """
    Process Excel file by reading each sheet individually.
    
    Args:
        file_path (str): Path to Excel file
        
    Returns:
        dict: Processed data by sheet
    """
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    results = {"sheets": {}}
    all_lottery_data = []
    
    try:
        # Get list of all sheets
        logger.info(f"Reading sheets from {file_path}")
        xlsx = pd.ExcelFile(file_path)
        sheet_names = xlsx.sheet_names
        
        logger.info(f"Found {len(sheet_names)} sheets: {', '.join(sheet_names)}")
        results["total_sheets"] = len(sheet_names)
        results["sheet_names"] = sheet_names
        
        # Skip common non-data sheets
        sheets_to_skip = ['instructions', 'info', 'readme', 'cover', 'index']
        valid_sheets = []
        
        for sheet_name in sheet_names:
            if sheet_name.lower() in sheets_to_skip:
                logger.info(f"Skipping non-data sheet: {sheet_name}")
                continue
                
            valid_sheets.append(sheet_name)
        
        # Process each valid sheet
        for sheet_name in valid_sheets:
            try:
                logger.info(f"Processing sheet: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Skip empty sheets
                if df.empty:
                    logger.info(f"Sheet {sheet_name} is empty")
                    results["sheets"][sheet_name] = {"status": "empty"}
                    continue
                
                # Replace NaN with None
                df = df.replace({np.nan: None})
                
                # Get column names
                columns = [str(col) for col in df.columns]
                logger.info(f"Sheet {sheet_name} columns: {', '.join(columns)}")
                
                # Try to determine lottery type from sheet name
                sheet_lottery_type = normalize_lottery_type(sheet_name)
                
                # Look for game name column
                game_name_col = None
                for col in columns:
                    if col.lower() in ['game name', 'game type', 'lottery type', 'lottery']:
                        game_name_col = col
                        break
                
                # Process rows in the sheet
                sheet_data = []
                
                for index, row in df.iterrows():
                    try:
                        # Skip empty or header-like rows
                        if all(pd.isna(value) for value in row):
                            continue
                            
                        # Determine lottery type
                        lottery_type = None
                        if game_name_col and not pd.isna(row[game_name_col]):
                            lottery_type = normalize_lottery_type(row[game_name_col])
                        else:
                            # If no game name column, use sheet name
                            lottery_type = sheet_lottery_type
                        
                        # Look for essential columns
                        draw_number = None
                        draw_date = None
                        numbers = []
                        bonus_ball = None
                        
                        for col in columns:
                            col_lower = col.lower()
                            value = row[col]
                            
                            # Skip empty values
                            if pd.isna(value):
                                continue
                                
                            # Extract draw number
                            if not draw_number and ('draw number' in col_lower or 'draw id' in col_lower):
                                draw_number = str(value)
                            
                            # Extract draw date
                            if not draw_date and ('draw date' in col_lower or 'date' in col_lower):
                                draw_date = parse_date(value)
                            
                            # Extract winning numbers
                            if len(numbers) == 0 and ('winning numbers' in col_lower or 'numbers' in col_lower):
                                numbers = parse_numbers(value)
                            
                            # Extract bonus ball
                            if bonus_ball is None and ('bonus' in col_lower or 'powerball' in col_lower):
                                if pd.isna(value):
                                    bonus_ball = None
                                elif isinstance(value, (int, float)):
                                    bonus_ball = [int(value)]
                                else:
                                    bonus_ball = parse_numbers(value)
                        
                        # Skip rows with insufficient data
                        if not lottery_type or not draw_number or not numbers:
                            logger.warning(f"Skipping row {index} due to insufficient data")
                            continue
                        
                        # Create record
                        record = {
                            "lottery_type": lottery_type,
                            "draw_number": draw_number,
                            "draw_date": draw_date,
                            "numbers": numbers,
                            "bonus_ball": bonus_ball
                        }
                        
                        # Add divisions if present
                        divisions = {}
                        div_pattern = re.compile(r'(div|division)\s*(\d+)', re.IGNORECASE)
                        
                        for col in columns:
                            col_lower = col.lower()
                            value = row[col]
                            
                            if pd.isna(value):
                                continue
                                
                            div_match = div_pattern.search(col_lower)
                            if div_match:
                                div_num = div_match.group(2)
                                div_key = f"Division {div_num}"
                                
                                if 'winner' in col_lower:
                                    if div_key not in divisions:
                                        divisions[div_key] = {}
                                    divisions[div_key]['winners'] = str(value)
                                elif 'prize' in col_lower or 'payout' in col_lower or 'winnings' in col_lower:
                                    if div_key not in divisions:
                                        divisions[div_key] = {}
                                    if isinstance(value, str) and not value.startswith("R"):
                                        divisions[div_key]['prize'] = f"R{value}"
                                    else:
                                        divisions[div_key]['prize'] = f"R{value}"
                        
                        if divisions:
                            record["divisions"] = divisions
                        
                        # Add to results
                        sheet_data.append(record)
                        all_lottery_data.append(record)
                        
                    except Exception as row_error:
                        logger.error(f"Error processing row {index}: {str(row_error)}")
                
                # Add sheet data to results
                results["sheets"][sheet_name] = {
                    "status": "processed",
                    "rows": len(sheet_data),
                    "data": sheet_data
                }
                
            except Exception as sheet_error:
                logger.error(f"Error processing sheet {sheet_name}: {str(sheet_error)}")
                results["sheets"][sheet_name] = {
                    "status": "error",
                    "error": str(sheet_error)
                }
        
        # Add summary
        results["total_processed"] = sum(1 for sheet in results["sheets"] if results["sheets"][sheet]["status"] == "processed")
        results["total_records"] = len(all_lottery_data)
        results["lottery_types_found"] = list(set(record["lottery_type"] for record in all_lottery_data))
        results["all_lottery_data"] = all_lottery_data
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        logger.error(traceback.format_exc())
        results["error"] = str(e)
    
    return results

if __name__ == "__main__":
    # Get file path from command line or use default
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "attached_assets/lottery_data_template_20250426_012917.xlsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    results = process_excel_sheets(file_path)
    
    # Print summary
    print("\n=== PROCESSING SUMMARY ===")
    print(f"Total sheets: {results.get('total_sheets', 0)}")
    print(f"Processed sheets: {results.get('total_processed', 0)}")
    print(f"Total records: {results.get('total_records', 0)}")
    print(f"Lottery types found: {', '.join(results.get('lottery_types_found', []))}")
    
    # Print detailed information
    if results.get('all_lottery_data'):
        print("\n=== DETAILED RECORDS ===")
        for idx, record in enumerate(results.get('all_lottery_data')):
            print(f"\nRecord {idx+1}:")
            print(f"  Lottery Type: {record.get('lottery_type', 'Unknown')}")
            print(f"  Draw Number: {record.get('draw_number', 'Unknown')}")
            print(f"  Draw Date: {record.get('draw_date', 'Unknown')}")
            print(f"  Numbers: {record.get('numbers', [])}")
            print(f"  Bonus Ball: {record.get('bonus_ball', [])}")
            
            if record.get('divisions'):
                print("  Divisions:")
                for div, data in record.get('divisions', {}).items():
                    print(f"    {div}: Winners={data.get('winners', 'Unknown')}, Prize={data.get('prize', 'Unknown')}")
    
    # Write results to file
    output_file = "excel_analysis.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results written to {output_file}")