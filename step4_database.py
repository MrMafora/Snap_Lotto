"""
Step 4: Database Update
Save processed lottery data to PostgreSQL database
"""
import os
import json
import logging
from sqlalchemy import create_engine, text
from datetime import datetime

logger = logging.getLogger(__name__)

def update_database():
    """Update database with processed lottery results"""
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL not found in environment")
            return False, 0
        
        # Create database connection
        engine = create_engine(database_url)
        
        # Check if lottery_results table exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'lottery_results'
            """))
            
            table_count = result.fetchone()
            if not table_count or table_count[0] == 0:
                logger.info("Creating lottery_results table")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS lottery_results (
                        id SERIAL PRIMARY KEY,
                        lottery_type VARCHAR(50) NOT NULL,
                        draw_date DATE NOT NULL,
                        draw_number INTEGER,
                        main_numbers TEXT,
                        bonus_numbers TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
        
        # Process actual lottery data from AI extraction
        extracted_data_file = os.path.join(os.getcwd(), 'extracted_lottery_data.json')
        new_records = 0
        
        if os.path.exists(extracted_data_file):
            logger.info("Found extracted lottery data file, processing...")
            
            with open(extracted_data_file, 'r') as f:
                lottery_data = json.load(f)
            
            with engine.connect() as conn:
                for result_data in lottery_data:
                    # Check if record already exists
                    existing_result = conn.execute(text("""
                        SELECT COUNT(*) FROM lottery_results 
                        WHERE lottery_type = :lottery_type 
                        AND draw_number = :draw_number
                    """), {
                        'lottery_type': result_data.get('lottery_type'),
                        'draw_number': result_data.get('draw_number')
                    }).fetchone()
                    
                    existing = existing_result[0] if existing_result else 0
                    
                    if existing == 0:
                        # Insert new record
                        conn.execute(text("""
                            INSERT INTO lottery_results 
                            (lottery_type, draw_date, draw_number, main_numbers, bonus_numbers)
                            VALUES (:lottery_type, :draw_date, :draw_number, :main_numbers, :bonus_numbers)
                        """), {
                            'lottery_type': result_data.get('lottery_type'),
                            'draw_date': result_data.get('draw_date'),
                            'draw_number': result_data.get('draw_number'),
                            'main_numbers': ','.join(map(str, result_data.get('main_numbers', []))),
                            'bonus_numbers': ','.join(map(str, result_data.get('bonus_numbers', [])))
                        })
                        new_records += 1
                        logger.info(f"Added new lottery result: {result_data.get('lottery_type')} Draw {result_data.get('draw_number')}")
                
                conn.commit()
            
            # Move processed file
            processed_file = extracted_data_file.replace('.json', f'_processed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            os.rename(extracted_data_file, processed_file)
            logger.info(f"Moved processed data to {processed_file}")
        
        else:
            logger.info("No extracted lottery data file found")
        
        # Count total records
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM lottery_results"))
            total_count = result.fetchone()
            total_records = total_count[0] if total_count else 0
        
        logger.info(f"Database update completed. Total records: {total_records}, New records added: {new_records}")
        return True, new_records
        
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        return False, 0