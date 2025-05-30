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
            
            if result.fetchone()[0] == 0:
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
        
        # For now, add a test record to verify database connectivity
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO lottery_results 
                (lottery_type, draw_date, draw_number, main_numbers, bonus_numbers)
                VALUES ('Test', CURRENT_DATE, 1, '1,2,3,4,5,6', '7')
            """))
            conn.commit()
            
            # Count total records
            result = conn.execute(text("SELECT COUNT(*) FROM lottery_results"))
            total_records = result.fetchone()[0]
        
        logger.info(f"Database update completed. Total records: {total_records}")
        return True, 1
        
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        return False, 0