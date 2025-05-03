"""
Verify the PendingExtraction model in the database
"""
import logging
import sys
from main import app
from models import PendingExtraction, db

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger("verify_extraction")

def check_pending_extraction_model():
    """Check if the PendingExtraction model is properly defined"""
    logger.info("Starting verification of PendingExtraction model")
    
    try:
        from sqlalchemy import inspect
        
        with app.app_context():
            logger.info("App context created")
            
            # Get the inspector
            inspector = inspect(db.engine)
            logger.info(f"Obtained inspector for database: {db.engine.url}")
            
            # Check if the table exists
            if 'pending_extraction' in inspector.get_table_names():
                logger.info("pending_extraction table exists in database")
                
                # Get columns
                columns = inspector.get_columns('pending_extraction')
                logger.info(f"Found {len(columns)} columns in pending_extraction table")
                
                for column in columns:
                    logger.info(f"Column: {column['name']}, Type: {column['type']}")
                
                return True
            else:
                logger.error("pending_extraction table does not exist in database")
                return False
                
    except Exception as e:
        logger.error(f"Error verifying PendingExtraction model: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = check_pending_extraction_model()
    logger.info(f"Verification result: {result}")