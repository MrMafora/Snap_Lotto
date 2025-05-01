#!/usr/bin/env python3
"""
Import script for specific missing lottery draws.
This script directly uses SQLAlchemy to import data without relying on the import template mechanism.
"""
import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import LotteryResult, ImportHistory
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_numbers(numbers_str):
    """Parse numbers string into a list of integers"""
    if not numbers_str or not isinstance(numbers_str, str):
        return []
    
    # Handle different formats: space-separated, comma-separated, or both
    try:
        # First try comma-separated format like "7, 16, 19, 20, 39"
        if ',' in numbers_str:
            return [int(num.strip()) for num in numbers_str.split(',') if num.strip().isdigit()]
        # Fall back to space-separated format
        else:
            return [int(num.strip()) for num in numbers_str.split() if num.strip().isdigit()]
    except Exception as e:
        logger.error(f"Error parsing numbers '{numbers_str}': {e}")
        return []

def parse_bonus_ball(bonus_str):
    """Parse bonus ball to integer"""
    if pd.isna(bonus_str):
        return None
    try:
        return int(bonus_str)
    except:
        return None

def import_missing_draws(excel_path):
    """
    Import specific missing draws from Excel file
    
    Args:
        excel_path (str): Path to Excel file with missing draws
        
    Returns:
        dict: Import statistics
    """
    try:
        logger.info(f"Importing missing draws from: {excel_path}")
        
        # Check if file exists
        if not os.path.exists(excel_path):
            return {"success": False, "error": f"File not found: {excel_path}", "stats": {}}
        
        # Read Excel file
        df = pd.read_excel(excel_path)
        logger.info(f"Found {len(df)} rows in Excel file")
        
        # Get database URI from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {"success": False, "error": "DATABASE_URL environment variable not set", "stats": {}}
        
        # Connect to database
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        stats = {
            "added": 0,
            "updated": 0,
            "errors": 0,
            "by_lottery_type": {}
        }
        
        # Create import history record
        import_record = ImportHistory(
            import_date=datetime.now(),
            import_type="excel_manual",
            file_name=os.path.basename(excel_path),
            total_processed=len(df),
            user_id=1  # Assume admin user with ID 1
        )
        session.add(import_record)
        session.flush()  # Get the ID without committing
        
        # Process each row
        for _, row in df.iterrows():
            try:
                lottery_type = row['Game Name']
                draw_number = str(row['Draw Number'])
                draw_date = row['Draw Date']
                numbers_str = row['Winning Numbers (Numerical)']
                bonus_ball = parse_bonus_ball(row['Bonus Ball'])
                
                # Skip rows with missing critical data
                if pd.isna(lottery_type) or pd.isna(draw_number) or pd.isna(draw_date):
                    logger.warning(f"Skipping row with missing critical data: {row.to_dict()}")
                    stats["errors"] += 1
                    continue
                
                # Count statistics by lottery type
                if lottery_type not in stats["by_lottery_type"]:
                    stats["by_lottery_type"][lottery_type] = 0
                stats["by_lottery_type"][lottery_type] += 1
                
                # Parse numbers
                numbers = parse_numbers(numbers_str)
                numbers_json = json.dumps(numbers)
                
                # Check if this draw already exists
                existing_draw = session.query(LotteryResult).filter_by(
                    lottery_type=lottery_type,
                    draw_number=draw_number
                ).first()
                
                if existing_draw:
                    # Update existing record
                    existing_draw.draw_date = draw_date
                    existing_draw.numbers = numbers_json
                    existing_draw.bonus_numbers = str(bonus_ball)
                    logger.info(f"Updated {lottery_type} draw {draw_number}")
                    stats["updated"] += 1
                else:
                    # Create new record
                    new_draw = LotteryResult(
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=draw_date,
                        numbers=numbers_json,
                        bonus_numbers=str(bonus_ball),  # Convert to string as required
                        source_url="manually_imported"  # This field is required
                    )
                    session.add(new_draw)
                    logger.info(f"Added new {lottery_type} draw {draw_number}")
                    stats["added"] += 1
            
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                stats["errors"] += 1
        
        # Update import history record
        import_record.records_added = stats["added"]
        import_record.records_updated = stats["updated"]
        import_record.errors = stats["errors"]
        
        # Commit all changes
        session.commit()
        logger.info(f"Import completed: {stats}")
        
        return {
            "success": True,
            "stats": stats,
            "error": None
        }
    
    except Exception as e:
        logger.error(f"Error importing missing draws: {e}")
        # Try to rollback if session exists
        try:
            if 'session' in locals():
                session.rollback()
        except:
            pass
        
        return {
            "success": False,
            "stats": {},
            "error": str(e)
        }

if __name__ == "__main__":
    result = import_missing_draws("attached_assets/missing_draws.xlsx")
    print(result)