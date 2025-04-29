import pandas as pd
import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variable"""
    return os.environ.get('DATABASE_URL')

def compare_excel_with_database(excel_path):
    """Compare Excel file data with database records"""
    logger.info(f"Comparing Excel file {excel_path} with database")
    
    # Check if Excel file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
        return
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return
    
    try:
        # Create database engine
        engine = create_engine(db_url)
        
        # Open Excel file
        xls = pd.ExcelFile(excel_path, engine='openpyxl')
        
        # Process each sheet
        for sheet_name in xls.sheet_names:
            if sheet_name.lower() == 'instructions':
                continue
                
            logger.info(f"Processing sheet: {sheet_name}")
            
            try:
                # Read sheet data
                df = pd.read_excel(excel_path, sheet_name=sheet_name, engine='openpyxl')
                
                # Skip empty sheets
                if df.empty:
                    logger.info(f"Sheet '{sheet_name}' is empty, skipping")
                    continue
                
                # Check if this is a template sheet with example data
                if ('Draw Number' in df.columns and 
                    df['Draw Number'].astype(str).str.contains('Example').any()):
                    logger.info(f"Sheet '{sheet_name}' contains example data, skipping")
                    continue
                
                # Get lottery type
                lottery_type = sheet_name
                if 'Game Name' in df.columns and not df['Game Name'].empty:
                    lottery_type = df['Game Name'].iloc[0]
                    if isinstance(lottery_type, str):
                        lottery_type = lottery_type.strip()
                
                logger.info(f"Analyzing lottery type: {lottery_type}")
                
                # Get latest draw numbers from Excel
                if 'Draw Number' in df.columns:
                    draw_numbers = df['Draw Number'].dropna().astype(str).tolist()
                    if draw_numbers:
                        logger.info(f"Excel contains {len(draw_numbers)} draw numbers, latest: {draw_numbers[0]}")
                        
                        # Query database for latest draw number for this lottery type
                        with engine.connect() as conn:
                            query = text("""
                                SELECT draw_number, draw_date 
                                FROM lottery_result 
                                WHERE lottery_type = :lottery_type 
                                ORDER BY draw_date DESC 
                                LIMIT 1
                            """)
                            result = conn.execute(query, {"lottery_type": lottery_type})
                            row = result.fetchone()
                            
                            if row:
                                db_draw = row[0]
                                db_date = row[1]
                                logger.info(f"Latest draw in database: {db_draw} from {db_date}")
                                
                                # Find new draws that aren't in the database
                                new_draws = []
                                for draw in draw_numbers:
                                    # Clean draw number to handle formats
                                    clean_draw = draw.replace('Draw ', '').strip()
                                    # Convert to same data type for comparison
                                    if clean_draw != db_draw:
                                        new_draws.append(clean_draw)
                                    else:
                                        # Stop when we hit a draw that matches database
                                        break
                                        
                                if new_draws:
                                    logger.info(f"Found {len(new_draws)} new draws in Excel: {', '.join(new_draws)}")
                                else:
                                    logger.info("No new draws found in Excel file")
                            else:
                                logger.info(f"No draws found in database for lottery type: {lottery_type}")
                else:
                    logger.warning(f"No 'Draw Number' column found in sheet '{sheet_name}'")
            except Exception as e:
                logger.error(f"Error processing sheet '{sheet_name}': {str(e)}")
    
    except Exception as e:
        logger.error(f"Error comparing Excel with database: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "attached_assets/lottery_data_template_20250429_020457.xlsx"
    
    compare_excel_with_database(excel_path)