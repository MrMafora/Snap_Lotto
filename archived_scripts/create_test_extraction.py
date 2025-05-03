"""
Create a test pending extraction record to verify database schema
"""
import logging
import sys
from main import app
from models import PendingExtraction, db
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger("test_extraction")

test_data = {
    "lottery_type": "Daily Lotto",
    "source_url": "https://www.nationallottery.co.za/daily-lotto-history",
    "extraction_timestamp": datetime.now().isoformat(),
    "draw_data": [
        {
            "draw_number": "2500",
            "draw_date": "2025-05-03",
            "winning_numbers": ["01", "15", "27", "33", "36"],
            "bonus_ball": None
        }
    ]
}

def create_test_extraction():
    """Create a test extraction record"""
    logger.info("Starting test extraction creation")
    
    try:
        with app.app_context():
            logger.info("App context created")
            
            # Convert to JSON
            json_data = json.dumps(test_data)
            logger.info(f"JSON data prepared: {json_data[:50]}...")
            
            # Create a new pending extraction
            logger.info("Creating PendingExtraction object")
            pending = PendingExtraction(
                lottery_type=test_data.get('lottery_type', 'Unknown'),
                draw_number=test_data['draw_data'][0]['draw_number'],
                raw_data=json_data,
                reviewed=False,
                approved=None,
                extraction_date=datetime.now()
            )
            
            logger.info("Adding to session")
            db.session.add(pending)
            
            logger.info("Committing to database")
            db.session.commit()
            
            logger.info(f"Successfully created test extraction with ID: {pending.id}")
            return pending.id
            
    except Exception as e:
        logger.error(f"Error creating test extraction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    extraction_id = create_test_extraction()
    logger.info(f"Created extraction with ID: {extraction_id}")