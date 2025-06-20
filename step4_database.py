#!/usr/bin/env python3
"""
Step 4: Database Update Module for Daily Automation
Saves extracted lottery data to the PostgreSQL database
"""

import os
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import LotteryResult
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Set up database connection"""
    try:
        database_url = Config.SQLALCHEMY_DATABASE_URI
        if not database_url:
            logger.error("Database URL not found in configuration")
            return None, None
            
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("Database connection established")
        return engine, session
    except Exception as e:
        logger.error(f"Failed to setup database: {str(e)}")
        return None, None

def normalize_lottery_type(lottery_type):
    """Normalize lottery type names to match database expectations"""
    type_mapping = {
        'lotto': 'LOTTO',
        'lotto plus 1': 'LOTTO PLUS 1',
        'lotto plus 2': 'LOTTO PLUS 2', 
        'powerball': 'PowerBall',
        'powerball plus': 'POWERBALL PLUS',
        'daily lotto': 'DAILY LOTTO'
    }
    
    normalized = lottery_type.lower().strip()
    return type_mapping.get(normalized, lottery_type)

def save_lottery_result(session, data):
    """Save a single lottery result to database"""
    try:
        # Normalize the lottery type
        lottery_type = normalize_lottery_type(data.get('lottery_type', ''))
        
        # Parse draw date
        draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
        
        # Check if this result already exists
        existing = session.query(LotteryResult).filter_by(
            lottery_type=lottery_type,
            draw_number=data['draw_number']
        ).first()
        
        if existing:
            logger.info(f"Result already exists: {lottery_type} Draw {data['draw_number']}")
            return False
            
        # Create new lottery result with expanded data
        result = LotteryResult()
        result.lottery_type = lottery_type
        result.draw_number = data['draw_number']
        result.draw_date = draw_date
        result.main_numbers = json.dumps(data['main_numbers'])
        result.bonus_numbers = json.dumps(data.get('bonus_numbers', []))
        
        # Section 2 - Prize divisions
        result.prize_divisions = data.get('prize_divisions')
        result.total_prize_pool = data.get('total_prize_pool')
        result.rollover_amount = data.get('rollover_amount')
        
        # Section 3 - More Info fields (different for each lottery type)
        result.next_draw_date = data.get('next_draw_date')
        result.estimated_jackpot = data.get('estimated_jackpot')
        result.rollover_number = data.get('rollover_number')
        result.total_pool_size = data.get('total_pool_size')
        result.total_sales = data.get('total_sales')
        result.draw_machine = data.get('draw_machine')
        result.additional_info = data.get('additional_info')
        
        # Legacy fields for compatibility
        result.next_jackpot = data.get('next_jackpot')
        result.divisions = data.get('divisions')
        
        session.add(result)
        session.commit()
        
        logger.info(f"Saved: {lottery_type} Draw {data['draw_number']} ({draw_date})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save lottery result: {str(e)}")
        session.rollback()
        return False

def load_extracted_data():
    """Load the extracted data from temporary file"""
    try:
        data_file = os.path.join(os.getcwd(), 'temp_extracted_data.json')
        if not os.path.exists(data_file):
            logger.warning("No extracted data file found")
            return []
            
        with open(data_file, 'r') as f:
            data = json.load(f)
            
        logger.info(f"Loaded {len(data)} records from extracted data file")
        return data
        
    except Exception as e:
        logger.error(f"Failed to load extracted data: {str(e)}")
        return []

def cleanup_temp_files():
    """Clean up temporary data files"""
    try:
        data_file = os.path.join(os.getcwd(), 'temp_extracted_data.json')
        if os.path.exists(data_file):
            os.remove(data_file)
            logger.info("Cleaned up temporary data file")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp files: {str(e)}")

def update_database():
    """Update database with extracted lottery data"""
    logger.info("=== STEP 4: DATABASE UPDATE STARTED ===")
    
    # Setup database connection
    engine, session = setup_database()
    if not session:
        logger.error("Failed to connect to database")
        return False
    
    # Load extracted data
    extracted_data = load_extracted_data()
    if not extracted_data:
        logger.error("No data to save to database")
        session.close()
        return False
    
    saved_count = 0
    
    try:
        for data in extracted_data:
            if save_lottery_result(session, data):
                saved_count += 1
                
    except Exception as e:
        logger.error(f"Error during database update: {str(e)}")
    finally:
        session.close()
        cleanup_temp_files()
    
    success = saved_count > 0
    
    if success:
        logger.info(f"=== STEP 4: DATABASE UPDATE COMPLETED - {saved_count} new records saved ===")
    else:
        logger.error("=== STEP 4: DATABASE UPDATE FAILED - No new records saved ===")
        
    return success

def run_database_update():
    """Run the database update process"""
    return update_database()

if __name__ == "__main__":
    run_database_update()