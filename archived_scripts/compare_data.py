import pandas as pd
import os
import sys
import json
from sqlalchemy import create_engine, text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variable"""
    return os.environ.get('DATABASE_URL')

def compare_excel_with_database(excel_path):
    """
    Compare Excel file data with database records.
    
    Args:
        excel_path (str): Path to Excel file
        
    Returns:
        dict: Comparison results
    """
    logger.info(f"Comparing Excel data with database records: {excel_path}")
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return {'success': False, 'error': 'Database URL not set'}
    
    # Check if Excel file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
        return {'success': False, 'error': f'Excel file not found: {excel_path}'}
    
    results = {
        'total_excel_draws': 0,
        'total_db_draws': 0,
        'matching_draws': 0,
        'missing_draws': [],
        'by_lottery_type': {}
    }
    
    try:
        # Create database engine
        engine = create_engine(db_url)
        
        # Open Excel file
        xls = pd.ExcelFile(excel_path, engine='openpyxl')
        
        # Determine sheet approach
        logger.info(f"Excel sheets: {xls.sheet_names}")
        
        # Process the Lottery sheet
        if 'Lottery' in xls.sheet_names:
            df = pd.read_excel(excel_path, sheet_name='Lottery', engine='openpyxl')
            
            if df.empty:
                logger.warning("Lottery sheet is empty")
                return {'success': False, 'error': 'Lottery sheet is empty'}
                
            # Find game name and draw number columns
            game_name_col = None
            draw_number_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'game' in col_lower and 'name' in col_lower:
                    game_name_col = col
                elif 'draw' in col_lower and ('number' in col_lower or 'no' in col_lower):
                    draw_number_col = col
            
            if not game_name_col or not draw_number_col:
                logger.error("Could not identify game name or draw number columns")
                return {'success': False, 'error': 'Could not identify essential columns'}
                
            logger.info(f"Using columns: Game={game_name_col}, Draw={draw_number_col}")
                
            # Get all valid draws from Excel
            excel_draws = []
            
            for _, row in df.iterrows():
                if row[game_name_col] and row[draw_number_col]:
                    if isinstance(row[game_name_col], str) and 'example' in row[game_name_col].lower():
                        continue
                        
                    lottery_type = str(row[game_name_col])
                    draw_number = str(row[draw_number_col])
                    
                    # Normalize lottery type names
                    lottery_type = lottery_type.replace('Lotto', 'Lottery')
                    if lottery_type.lower() == 'daily lotto':
                        lottery_type = 'Daily Lottery'
                        
                    excel_draws.append((lottery_type, draw_number))
                    
                    # Track by lottery type
                    if lottery_type not in results['by_lottery_type']:
                        results['by_lottery_type'][lottery_type] = {
                            'excel_count': 0,
                            'db_count': 0,
                            'matching': 0,
                            'missing': []
                        }
                    results['by_lottery_type'][lottery_type]['excel_count'] += 1
            
            results['total_excel_draws'] = len(excel_draws)
            logger.info(f"Found {len(excel_draws)} valid draws in Excel")
            
            # Now check each draw against the database
            with engine.connect() as conn:
                # Get count of all lottery results
                count_query = text("SELECT COUNT(*) FROM lottery_result")
                total_db_draws = conn.execute(count_query).scalar()
                results['total_db_draws'] = total_db_draws
                
                # For each Excel draw, check if it exists in the database
                for lottery_type, draw_number in excel_draws:
                    check_query = text("""
                        SELECT lottery_type, draw_number 
                        FROM lottery_result 
                        WHERE lottery_type = :lottery_type AND draw_number = :draw_number
                    """)
                    
                    result = conn.execute(check_query, {
                        'lottery_type': lottery_type,
                        'draw_number': draw_number
                    })
                    
                    if result.fetchone():
                        results['matching_draws'] += 1
                        results['by_lottery_type'][lottery_type]['matching'] += 1
                    else:
                        missing_draw = {
                            'lottery_type': lottery_type,
                            'draw_number': draw_number
                        }
                        results['missing_draws'].append(missing_draw)
                        results['by_lottery_type'][lottery_type]['missing'].append(draw_number)
                        
                # Get counts by lottery type from database
                type_query = text("""
                    SELECT lottery_type, COUNT(*) 
                    FROM lottery_result 
                    GROUP BY lottery_type
                """)
                
                for lottery_type, count in conn.execute(type_query):
                    if lottery_type in results['by_lottery_type']:
                        results['by_lottery_type'][lottery_type]['db_count'] = count
                    else:
                        results['by_lottery_type'][lottery_type] = {
                            'excel_count': 0,
                            'db_count': count,
                            'matching': 0,
                            'missing': []
                        }
                        
        else:
            logger.error("Required sheet 'Lottery' not found")
            return {'success': False, 'error': "Required sheet 'Lottery' not found"}
        
        return {'success': True, 'results': results}
    
    except Exception as e:
        logger.error(f"Error comparing data: {str(e)}")
        return {'success': False, 'error': f'Error comparing data: {str(e)}'}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "attached_assets/lottery_data_template_20250429_020457.xlsx"
    
    result = compare_excel_with_database(excel_path)
    print(json.dumps(result, indent=2))