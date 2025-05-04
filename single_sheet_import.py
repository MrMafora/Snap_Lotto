import pandas as pd
import os
import json
from datetime import datetime
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import re
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variable"""
    return os.environ.get('DATABASE_URL')

def parse_numbers(numbers_str):
    """
    Parse lottery numbers from string format to list of integers.
    Enhanced to handle various formats including single numbers.
    
    Args:
        numbers_str (str): String representation of numbers
        
    Returns:
        list: List of numbers as integers
    """
    if pd.isna(numbers_str) or not numbers_str:
        return []
        
    # If already a list of integers, return as is
    if isinstance(numbers_str, list):
        return [int(n) for n in numbers_str if str(n).isdigit()]
    
    # If just a single integer, return as a list with one item
    if isinstance(numbers_str, (int, float)) and not pd.isna(numbers_str):
        return [int(numbers_str)]
        
    # Handle different formats of number strings
    if isinstance(numbers_str, str):
        # Remove any prefix like "Example:" and other non-essential text
        numbers_str = re.sub(r'example:|bonus:|ball:|powerball:', '', numbers_str.lower()).strip()
        
        # Special case: "33" or single number as string
        if numbers_str.isdigit():
            return [int(numbers_str)]
            
        # Handle comma-separated format: "1, 2, 3, 4, 5, 6"
        if ',' in numbers_str:
            # Extract all numbers using regex to catch digits that might have text around them
            matches = re.findall(r'\d+', numbers_str)
            if matches:
                return [int(n) for n in matches]
            
        # Handle space-separated format: "1 2 3 4 5 6"
        # Extract all numbers using regex to be more robust
        matches = re.findall(r'\d+', numbers_str)
        if matches:
            return [int(n) for n in matches]
        
    # Default empty list if we can't parse
    return []

def parse_excel_date(date_value):
    """
    Parse Excel date value into Python datetime.
    
    Args:
        date_value: Date value from Excel (can be string, datetime, or integer)
        
    Returns:
        datetime: Parsed datetime object or None if parsing fails
    """
    if pd.isna(date_value):
        return None
        
    # If already a datetime, return as is
    if isinstance(date_value, datetime):
        return date_value
        
    # Handle string date formats
    if isinstance(date_value, str):
        date_str = date_value.strip()
        
        # Skip placeholder dates
        if date_str in ['YYYY-MM-DD', 'Example: 2023-01-01']:
            return None
            
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',           # 2023-01-31
            '%d/%m/%Y',           # 31/01/2023
            '%m/%d/%Y',           # 01/31/2023
            '%d-%m-%Y',           # 31-01-2023
            '%d %b %Y',           # 31 Jan 2023
            '%d %B %Y',           # 31 January 2023
            '%B %d, %Y',          # January 31, 2023
            '%Y/%m/%d',           # 2023/01/31
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
                
    # Handle numeric date (Excel serial date)
    if isinstance(date_value, (int, float)):
        try:
            # Excel dates start from 1900-01-01, which is day 1
            # Convert to Python datetime (library handles this conversion)
            return pd.to_datetime(date_value, unit='D', origin='1899-12-30')
        except Exception:
            pass
            
    logger.warning(f"Could not parse date: {date_value}")
    return None

def parse_divisions(row):
    """
    Parse division data from Excel row.
    
    Args:
        row (pandas.Series): Row data from Excel
        
    Returns:
        dict: Division data with winners and prizes
    """
    divisions = {}
    
    # Look for division information in various column naming formats
    for i in range(1, 9):  # Support up to 8 divisions
        # Define common prefixes and column patterns
        prefixes = [
            f'Division {i}',
            f'Div {i}',
            f'Div{i}',
            f'Division{i}'
        ]
        
        # Search for matching columns with these prefixes
        for prefix in prefixes:
            found_data = False
            
            # Try various suffix combinations
            for winners_suffix in [' Winners', ' Winner', ' Wnrs', 'Winners', 'Winner', 'Wnrs']:
                for payout_suffix in [' Payout', ' Prize', ' Winnings', 'Payout', 'Prize', 'Winnings']:
                    winners_key = f"{prefix}{winners_suffix}"
                    payout_key = f"{prefix}{payout_suffix}"
                    
                    # Case-insensitive column lookup
                    winners_col = next((col for col in row.index if col.lower() == winners_key.lower()), None)
                    payout_col = next((col for col in row.index if col.lower() == payout_key.lower()), None)
                    
                    if winners_col is not None or payout_col is not None:
                        # Use standardized division key format "Division X"
                        division_key = f"Division {i}"
                        divisions[division_key] = {
                            'winners': '0',
                            'prize': 'R0.00',
                            'match': f'{i} correct numbers'  # Default match description
                        }
                        
                        # Process winners
                        if winners_col is not None:
                            winners = row.get(winners_col)
                            if winners is not None and not pd.isna(winners):
                                if isinstance(winners, str):
                                    # Clean up the string
                                    winners = winners.replace('Example:', '').strip()
                                    winners_value = re.sub(r'[^\d]', '', winners)
                                    if winners_value.isdigit():
                                        divisions[division_key]['winners'] = str(int(winners_value))
                                elif isinstance(winners, (int, float)):
                                    divisions[division_key]['winners'] = str(int(winners))
                        
                        # Process payouts
                        if payout_col is not None:
                            payout = row.get(payout_col)
                            if payout is not None and not pd.isna(payout):
                                if isinstance(payout, str):
                                    # Clean up the string
                                    payout = payout.replace('Example:', '').strip()
                                    
                                    # Remove any existing R prefix to standardize formatting
                                    if payout.startswith('R'):
                                        payout = payout[1:]
                                    
                                    # Handle different numeric formats
                                    # Remove any commas or spaces in the number
                                    payout_clean = payout.replace(',', '').replace(' ', '')
                                    
                                    try:
                                        # Try to convert to float for proper formatting
                                        payout_value = float(payout_clean)
                                        # Format with commas for thousands and 2 decimal places
                                        formatted_payout = f'R{payout_value:,.2f}'
                                        divisions[division_key]['prize'] = formatted_payout
                                    except ValueError:
                                        # If conversion fails, just add R prefix
                                        divisions[division_key]['prize'] = f'R{payout}'
                                elif isinstance(payout, (int, float)):
                                    # Format with commas for thousands and 2 decimal places
                                    # Ensure proper currency formatting with commas for thousands
                                    if payout >= 1:
                                        divisions[division_key]['prize'] = f'R{payout:,.2f}'
                                    else:
                                        divisions[division_key]['prize'] = f'R{payout:.2f}'
                        
                        # Determine match description based on lottery type
                        lottery_type = row.get('Game Name', '')
                        if isinstance(lottery_type, str):
                            if 'powerball' in lottery_type.lower():
                                if i == 1:
                                    divisions[division_key]['match'] = "5 CORRECT NUMBERS + POWERBALL"
                                elif i == 2:
                                    divisions[division_key]['match'] = "5 CORRECT NUMBERS"
                                elif i == 3:
                                    divisions[division_key]['match'] = "4 CORRECT NUMBERS + POWERBALL"
                                elif i == 4:
                                    divisions[division_key]['match'] = "4 CORRECT NUMBERS"
                                elif i == 5:
                                    divisions[division_key]['match'] = "3 CORRECT NUMBERS + POWERBALL"
                                elif i == 6:
                                    divisions[division_key]['match'] = "3 CORRECT NUMBERS"
                                elif i == 7:
                                    divisions[division_key]['match'] = "2 CORRECT NUMBERS + POWERBALL"
                                elif i == 8:
                                    divisions[division_key]['match'] = "1 CORRECT NUMBER + POWERBALL"
                            elif 'lottery' in lottery_type.lower() or 'lotto' in lottery_type.lower():
                                if i == 1:
                                    divisions[division_key]['match'] = "6 CORRECT NUMBERS"
                                elif i == 2:
                                    divisions[division_key]['match'] = "5 CORRECT NUMBERS + BONUS BALL"
                                elif i == 3:
                                    divisions[division_key]['match'] = "5 CORRECT NUMBERS"
                                elif i == 4:
                                    divisions[division_key]['match'] = "4 CORRECT NUMBERS + BONUS BALL"
                                elif i == 5:
                                    divisions[division_key]['match'] = "4 CORRECT NUMBERS"
                                elif i == 6:
                                    divisions[division_key]['match'] = "3 CORRECT NUMBERS + BONUS BALL"
                                elif i == 7:
                                    divisions[division_key]['match'] = "3 CORRECT NUMBERS"
                                elif i == 8:
                                    divisions[division_key]['match'] = "2 CORRECT NUMBERS + BONUS BALL"
                            elif 'daily' in lottery_type.lower():
                                if i == 1:
                                    divisions[division_key]['match'] = "5 CORRECT NUMBERS"
                                elif i == 2:
                                    divisions[division_key]['match'] = "4 CORRECT NUMBERS"
                                elif i == 3:
                                    divisions[division_key]['match'] = "3 CORRECT NUMBERS"
                                elif i == 4:
                                    divisions[division_key]['match'] = "2 CORRECT NUMBERS"
                                elif i == 5:
                                    divisions[division_key]['match'] = "1 CORRECT NUMBER"
                        
                        found_data = True
                        break
                
                if found_data:
                    break
    
    return divisions

def normalize_lottery_type(lottery_type):
    """
    Normalize lottery type names to standard format.
    
    Args:
        lottery_type (str): The lottery type name
        
    Returns:
        str: Normalized lottery type
    """
    if not lottery_type or pd.isna(lottery_type):
        return None
        
    lottery_type = str(lottery_type).strip()
    
    # Replace 'Lotto' with 'Lottery' for SEO
    if lottery_type.lower() == 'lotto':
        return 'Lottery'
    elif lottery_type.lower() == 'daily lotto':
        return 'Daily Lottery'
    elif lottery_type.lower() in ['lotto plus 1', 'lottery plus 1']:
        return 'Lottery Plus 1'
    elif lottery_type.lower() in ['lotto plus 2', 'lottery plus 2']:
        return 'Lottery Plus 2'
    
    return lottery_type

def import_single_sheet(excel_path):
    """
    Import lottery data from a single-sheet Excel file.
    
    Args:
        excel_path (str): Path to Excel file
        
    Returns:
        dict: Import statistics
    """
    logger.info(f"Importing lottery data from single-sheet file: {excel_path}")
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return {'success': False, 'error': 'Database URL not set'}
    
    # Check if Excel file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
        return {'success': False, 'error': f'Excel file not found: {excel_path}'}
    
    stats = {
        'total_processed': 0,
        'imported': 0,
        'errors': 0,
        'by_lottery_type': {}
    }
    
    try:
        # Create database engine
        engine = create_engine(db_url)
        
        # Open Excel file
        xls = pd.ExcelFile(excel_path, engine='openpyxl')
        
        # Verify sheet names
        if 'Lottery' not in xls.sheet_names:
            logger.error(f"Required sheet 'Lottery' not found. Available sheets: {xls.sheet_names}")
            return {'success': False, 'error': f"Required sheet 'Lottery' not found"}
        
        # Process the main Lottery sheet
        logger.info("Processing Lottery sheet")
        df = pd.read_excel(excel_path, sheet_name='Lottery', engine='openpyxl')
        
        if df.empty:
            logger.warning("Lottery sheet is empty")
            return {'success': False, 'error': 'Lottery sheet is empty'}
        
        # Check for required columns
        required_columns = ['Game Name', 'Draw Number', 'Draw Date']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Required column '{col}' not found")
                return {'success': False, 'error': f"Required column '{col}' not found"}
        
        logger.info(f"Found {len(df)} total rows in the sheet")
        
        # Identify column for winning numbers
        numbers_col = next((col for col in df.columns if 'Winning Numbers' in col), None)
        if not numbers_col:
            logger.error("No 'Winning Numbers' column found")
            return {'success': False, 'error': "No 'Winning Numbers' column found"}
        
        # Enhanced identification of bonus number columns with more comprehensive detection
        bonus_col = None
        potential_bonus_cols = []
        
        for col in df.columns:
            col_lower = str(col).lower()
            if ('bonus' in col_lower or 
                'power' in col_lower or 
                'powerball' in col_lower or 
                'ball' in col_lower or
                'extra' in col_lower or
                'supplementary' in col_lower):
                potential_bonus_cols.append(col)
                logger.info(f"Found potential bonus column: {col}")
        
        # Use the first potential bonus column found
        if potential_bonus_cols:
            bonus_col = potential_bonus_cols[0]
            logger.info(f"Using bonus column: {bonus_col}")
            
        # Special check for specific lottery types
        lottery_type_cols = {}
        for idx, row in df.iterrows():
            if pd.isna(row.get('Game Name')):
                continue
                
            lottery_type = normalize_lottery_type(row['Game Name'])
            if not lottery_type:
                continue
                
            for col in potential_bonus_cols:
                if not pd.isna(row.get(col)):
                    lottery_type_cols.setdefault(lottery_type, set()).add(col)
                    
        logger.info(f"Lottery type specific bonus columns: {lottery_type_cols}")
        
        # Process each draw
        for _, row in df.iterrows():
            # Skip empty or example rows
            if pd.isna(row['Game Name']) or pd.isna(row['Draw Number']) or str(row['Game Name']).startswith('Example'):
                continue
                
            stats['total_processed'] += 1
            
            try:
                # Normalize and extract data
                lottery_type = normalize_lottery_type(row['Game Name'])
                draw_number = str(row['Draw Number'])
                draw_date = parse_excel_date(row['Draw Date'])
                
                # Skip invalid draws
                if not lottery_type or not draw_number or not draw_date:
                    logger.warning(f"Skipping draw with invalid data: {row['Game Name']} - {row['Draw Number']}")
                    stats['errors'] += 1
                    continue
                
                # Parse winning numbers
                numbers = parse_numbers(row[numbers_col])
                if not numbers:
                    logger.warning(f"Could not parse winning numbers for {lottery_type} draw {draw_number}")
                    stats['errors'] += 1
                    continue
                
                # Parse bonus numbers (if available)
                bonus_numbers = []
                
                # Get current lottery type to check for type-specific bonus columns
                current_lottery_type = normalize_lottery_type(row['Game Name'])
                
                # First, try lottery-type specific bonus column if available
                if current_lottery_type in lottery_type_cols:
                    for specific_col in lottery_type_cols[current_lottery_type]:
                        if specific_col in row and not pd.isna(row[specific_col]):
                            bonus_num = parse_numbers(row[specific_col])
                            if bonus_num:
                                bonus_numbers = bonus_num
                                logger.info(f"Using lottery-specific bonus column {specific_col} for {current_lottery_type}: {bonus_numbers}")
                                break
                
                # If no lottery-specific bonus numbers found, use the default bonus column
                if not bonus_numbers and bonus_col and not pd.isna(row[bonus_col]):
                    bonus_numbers = parse_numbers(row[bonus_col])
                    logger.info(f"Using default bonus column {bonus_col} for {current_lottery_type}: {bonus_numbers}")
                
                # Try all potential bonus columns if still no bonus numbers found
                if not bonus_numbers:
                    for col in potential_bonus_cols:
                        if col in row and not pd.isna(row[col]):
                            bonus_num = parse_numbers(row[col])
                            if bonus_num:
                                bonus_numbers = bonus_num
                                logger.info(f"Found bonus numbers in column {col} for {current_lottery_type}: {bonus_numbers}")
                                break
                
                # Parse division data
                divisions = parse_divisions(row)
                
                # Prepare data for insertion
                data = {
                    'lottery_type': lottery_type,
                    'draw_number': draw_number,
                    'draw_date': draw_date.strftime('%Y-%m-%d'),
                    'numbers': json.dumps(numbers),
                    'bonus_numbers': json.dumps(bonus_numbers),
                    'divisions': json.dumps(divisions),
                    'source_url': excel_path,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                logger.info(f"Processing draw {lottery_type} - {draw_number}")
                
                # Check if draw already exists
                with engine.connect() as conn:
                    query = text("""
                        SELECT id FROM lottery_result 
                        WHERE lottery_type = :lottery_type AND draw_number = :draw_number
                    """)
                    result = conn.execute(query, {'lottery_type': lottery_type, 'draw_number': draw_number})
                    existing_draw = result.fetchone()
                    
                    if existing_draw:
                        # Update existing draw
                        logger.info(f"Updating existing draw {lottery_type} - {draw_number}")
                        update_query = text("""
                            UPDATE lottery_result 
                            SET draw_date = :draw_date,
                                numbers = :numbers,
                                bonus_numbers = :bonus_numbers,
                                divisions = :divisions,
                                source_url = :source_url
                            WHERE lottery_type = :lottery_type AND draw_number = :draw_number
                        """)
                        conn.execute(update_query, data)
                    else:
                        # Insert new draw
                        logger.info(f"Inserting new draw {lottery_type} - {draw_number}")
                        insert_query = text("""
                            INSERT INTO lottery_result (
                                lottery_type, draw_number, draw_date, numbers, bonus_numbers,
                                divisions, source_url, created_at
                            ) VALUES (
                                :lottery_type, :draw_number, :draw_date, :numbers, :bonus_numbers,
                                :divisions, :source_url, :created_at
                            )
                        """)
                        conn.execute(insert_query, data)
                        
                    conn.commit()
                    stats['imported'] += 1
                    
                    # Track statistics by lottery type
                    if lottery_type not in stats['by_lottery_type']:
                        stats['by_lottery_type'][lottery_type] = 0
                    stats['by_lottery_type'][lottery_type] += 1
                
            except Exception as e:
                logger.error(f"Error processing draw {row.get('Game Name', 'Unknown')} - {row.get('Draw Number', 'Unknown')}: {str(e)}")
                stats['errors'] += 1
        
        # Log summary statistics
        logger.info(f"Import completed. Stats: {stats}")
        return {'success': True, 'stats': stats}
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return {'success': False, 'error': f'Database error: {str(e)}'}
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return {'success': False, 'error': f'General error: {str(e)}'}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "attached_assets/lottery_data_template_20250429_020457.xlsx"
    
    result = import_single_sheet(excel_path)
    print(json.dumps(result, indent=2))