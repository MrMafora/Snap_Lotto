"""
Integration script to connect improved_excel_import.py with the main application.
This allows seamless importing from Excel files with better error handling and
column detection.
"""
import os
import sys
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_flask_context():
    """
    Set up Flask application context for database operations.
    
    Returns:
        Tuple containing (app, db) objects
    """
    try:
        # First, try importing from a module that defines the Flask app
        from main import app, db
        logger.info("Using main.py application context")
        return app, db
    except ImportError:
        # If that doesn't work, try a fallback
        try:
            from flask import Flask
            from flask_sqlalchemy import SQLAlchemy
            from sqlalchemy.orm import DeclarativeBase
            
            class Base(DeclarativeBase):
                pass
                
            db = SQLAlchemy(model_class=Base)
            app = Flask(__name__)
            
            # Configure database from environment
            app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///lottery.db")
            app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
                "pool_recycle": 300,
                "pool_pre_ping": True,
            }
            
            db.init_app(app)
            logger.info("Created new application context")
            return app, db
        except Exception as e:
            logger.error(f"Error setting up Flask context: {str(e)}")
            raise

def import_to_database(records: List[Dict[str, Any]], app, db) -> Tuple[int, int, List[str]]:
    """
    Import records to the database using the provided Flask app context.
    
    Args:
        records: List of standardized lottery data records
        app: Flask application
        db: SQLAlchemy database object
        
    Returns:
        Tuple of (success_count, error_count, error_messages)
    """
    from models import LotteryResult, Screenshot
    
    success_count = 0
    error_count = 0
    error_messages = []
    
    with app.app_context():
        # Track import in the database
        from models import ImportHistory, ImportedRecord
        
        # Create a new import history record
        import_history = ImportHistory(
            import_date=datetime.now(),
            file_name="Excel Import",
            status="in_progress",
            record_count=len(records),
            user_id=None  # Will be set if user information is available
        )
        db.session.add(import_history)
        db.session.commit()
        
        try:
            # Process each record
            for record in records:
                try:
                    # Normalize lottery type
                    lottery_type = normalize_lottery_type(record.get('game_name', ''))
                    
                    # Check if this draw already exists
                    existing = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=record.get('draw_number')
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.draw_date = datetime.strptime(record.get('draw_date'), '%Y-%m-%d') if record.get('draw_date') else None
                        
                        # Update winning numbers if provided
                        if record.get('winning_numbers'):
                            if isinstance(record['winning_numbers'], list):
                                existing.ball_1 = record['winning_numbers'][0] if len(record['winning_numbers']) > 0 else None
                                existing.ball_2 = record['winning_numbers'][1] if len(record['winning_numbers']) > 1 else None
                                existing.ball_3 = record['winning_numbers'][2] if len(record['winning_numbers']) > 2 else None
                                existing.ball_4 = record['winning_numbers'][3] if len(record['winning_numbers']) > 3 else None
                                existing.ball_5 = record['winning_numbers'][4] if len(record['winning_numbers']) > 4 else None
                                existing.ball_6 = record['winning_numbers'][5] if len(record['winning_numbers']) > 5 else None
                                
                                # Handle PowerBall which has 5 main balls and a PowerBall
                                if 'PowerBall' in lottery_type and len(record['winning_numbers']) >= 5:
                                    existing.bonus_ball = record.get('bonus_ball')
                                    existing.ball_6 = None  # PowerBall doesn't have a 6th ball
                                else:
                                    existing.bonus_ball = record.get('bonus_ball')
                        
                        # Update division information if provided
                        if 'div_winners' in record and 'div_winnings' in record:
                            existing.division_1_winners = record.get('div_winners')
                            existing.division_1_prize = str(record.get('div_winnings', '')).replace('R', '').replace(',', '')
                            
                        db.session.commit()
                        logger.info(f"Updated existing record: {lottery_type} Draw #{record.get('draw_number')}")
                    else:
                        # Create new record
                        new_record = LotteryResult(
                            lottery_type=lottery_type,
                            draw_number=record.get('draw_number'),
                            draw_date=datetime.strptime(record.get('draw_date'), '%Y-%m-%d') if record.get('draw_date') else None
                        )
                        
                        # Set winning numbers if provided
                        if record.get('winning_numbers'):
                            if isinstance(record['winning_numbers'], list):
                                new_record.ball_1 = record['winning_numbers'][0] if len(record['winning_numbers']) > 0 else None
                                new_record.ball_2 = record['winning_numbers'][1] if len(record['winning_numbers']) > 1 else None
                                new_record.ball_3 = record['winning_numbers'][2] if len(record['winning_numbers']) > 2 else None
                                new_record.ball_4 = record['winning_numbers'][3] if len(record['winning_numbers']) > 3 else None
                                new_record.ball_5 = record['winning_numbers'][4] if len(record['winning_numbers']) > 4 else None
                                new_record.ball_6 = record['winning_numbers'][5] if len(record['winning_numbers']) > 5 else None
                                
                                # Handle PowerBall which has 5 main balls and a PowerBall
                                if 'PowerBall' in lottery_type and len(record['winning_numbers']) >= 5:
                                    new_record.bonus_ball = record.get('bonus_ball')
                                    new_record.ball_6 = None  # PowerBall doesn't have a 6th ball
                                else:
                                    new_record.bonus_ball = record.get('bonus_ball')
                        
                        # Set division information if provided
                        if 'div_winners' in record and 'div_winnings' in record:
                            new_record.division_1_winners = record.get('div_winners')
                            try:
                                new_record.division_1_prize = str(record.get('div_winnings', '')).replace('R', '').replace(',', '')
                            except Exception as e:
                                logger.warning(f"Error processing division prize: {str(e)}")
                            
                        db.session.add(new_record)
                        db.session.commit()
                        logger.info(f"Created new record: {lottery_type} Draw #{record.get('draw_number')}")
                    
                    # Track imported record
                    imported_record = ImportedRecord(
                        import_id=import_history.id,
                        lottery_type=lottery_type,
                        draw_number=record.get('draw_number'),
                        status="success"
                    )
                    db.session.add(imported_record)
                    db.session.commit()
                    
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    error_message = f"Error importing {record.get('game_name')} Draw #{record.get('draw_number')}: {str(e)}"
                    error_messages.append(error_message)
                    logger.error(error_message)
                    
                    # Track failed record
                    try:
                        imported_record = ImportedRecord(
                            import_id=import_history.id,
                            lottery_type=normalize_lottery_type(record.get('game_name', '')),
                            draw_number=record.get('draw_number'),
                            status="error",
                            error_message=str(e)
                        )
                        db.session.add(imported_record)
                        db.session.commit()
                    except Exception as inner_error:
                        logger.error(f"Error tracking failed import: {str(inner_error)}")
                        
            # Update import history status
            import_history.status = "completed" if error_count == 0 else "completed_with_errors"
            import_history.success_count = success_count
            import_history.error_count = error_count
            import_history.completion_date = datetime.now()
            db.session.commit()
            
        except Exception as e:
            error_message = f"Fatal error during import: {str(e)}"
            error_messages.append(error_message)
            logger.error(error_message)
            traceback.print_exc()
            
            # Mark import as failed
            import_history.status = "failed"
            import_history.error_message = error_message
            import_history.completion_date = datetime.now()
            db.session.commit()
    
    return success_count, error_count, error_messages

def normalize_lottery_type(game_name: str) -> str:
    """
    Normalize lottery type to the standard format used in the application.
    
    Args:
        game_name: Original game name from Excel file
        
    Returns:
        Normalized lottery type
    """
    if game_name is None:
        return "Unknown"
        
    # Handle special case for "Lottery 2536" format (where draw number is included in the name)
    # Extract just the lottery type without the draw number
    import re
    match = re.match(r'(lottery|lotto)\s+\d+', str(game_name).strip().lower())
    if match:
        logger.info(f"Found lottery name with embedded draw number: {game_name}, extracting 'Lottery'")
        return 'Lottery'
    
    game_name = str(game_name).strip().lower()
    
    if 'lotto plus 1' in game_name or 'lotto+1' in game_name:
        return 'Lottery Plus 1'  # Use "Lottery" instead of "Lotto"
    elif 'lotto plus 2' in game_name or 'lotto+2' in game_name:
        return 'Lottery Plus 2'  # Use "Lottery" instead of "Lotto"
    elif 'powerball plus' in game_name or 'powerball+' in game_name:
        return 'Powerball Plus'
    elif 'powerball' in game_name:
        return 'Powerball'
    elif 'daily lotto' in game_name or 'daily lottery' in game_name:
        return 'Daily Lottery'  # Use "Lottery" instead of "Lotto"
    elif 'lotto' in game_name or 'lottery' in game_name:
        return 'Lottery'
    else:
        logger.warning(f"Unknown lottery type format: {game_name}")
        return game_name.title()  # Fallback - capitalize each word

def run_import(file_path: str, sheet_name: Optional[str] = None) -> Tuple[int, int, List[str]]:
    """
    Run the import process for an Excel file.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Optional specific sheet name to import
        
    Returns:
        Tuple of (success_count, error_count, error_messages)
    """
    try:
        # Import improved Excel functions
        from improved_excel_import import import_excel_file
        
        # Extract records from Excel
        logger.info(f"Extracting data from {file_path}")
        records = import_excel_file(file_path, sheet_name)
        
        if not records:
            logger.warning("No valid records found in the Excel file")
            return 0, 1, ["No valid records found in the Excel file"]
            
        logger.info(f"Found {len(records)} records to import")
        
        # Set up Flask context for database operations
        app, db = setup_flask_context()
        
        # Import records to database
        logger.info("Importing records to database")
        success_count, error_count, error_messages = import_to_database(records, app, db)
        
        logger.info(f"Import completed: {success_count} successes, {error_count} errors")
        return success_count, error_count, error_messages
        
    except Exception as e:
        logger.error(f"Error in import process: {str(e)}")
        traceback.print_exc()
        return 0, 1, [f"Fatal error: {str(e)}"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import lottery data from Excel file')
    parser.add_argument('file_path', help='Path to the Excel file')
    parser.add_argument('--sheet', help='Optional specific sheet to import', default=None)
    
    args = parser.parse_args()
    
    success_count, error_count, error_messages = run_import(args.file_path, args.sheet)
    
    if error_count > 0:
        print(f"Import completed with {error_count} errors:")
        for msg in error_messages:
            print(f"  - {msg}")
    else:
        print(f"Import completed successfully! {success_count} records imported.")
    
    sys.exit(0 if error_count == 0 else 1)