import os
import re
from datetime import datetime
from flask import Flask
from sqlalchemy.orm import Session

# Create a minimal Flask app with database configuration
def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    return app

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    if not date_str or date_str == 'Data N/A':
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print(f"Could not parse date: {date_str}")
            return None

def parse_text_data(text_content):
    """Parse the pasted text content to extract lottery data"""
    # Split the content by game types
    game_sections = []
    current_section = []
    
    # Skip header lines by looking for the line that starts with "Game Name"
    lines = text_content.strip().split('\n')
    data_started = False
    
    for line in lines:
        if not data_started and line.startswith("Game Name"):
            data_started = True
            current_section.append(line)
        elif data_started:
            current_section.append(line)
    
    # Process only the data lines
    if current_section:
        # Extract the tab-separated header columns
        headers = current_section[0].split('\t')
        
        # Process each data row
        data_rows = []
        for i in range(1, len(current_section)):
            row_values = current_section[i].split('\t')
            
            # Make sure the row has enough values
            if len(row_values) >= 3:  # At minimum we need game name, draw number, date
                row_data = {}
                for j in range(min(len(headers), len(row_values))):
                    row_data[headers[j]] = row_values[j]
                
                data_rows.append(row_data)
        
        return headers, data_rows
    
    return None, []

def import_data_to_db(text_content):
    """Import the parsed text data into the database"""
    # Import the models to use
    from models import db, LotteryResult, ImportHistory, ImportedRecord
    
    app = create_app()
    db.init_app(app)
    
    with app.app_context():
        import_start_time = datetime.now()
        
        # Create import history record
        import_history = ImportHistory(
            file_name="text_data_import.txt",
            import_date=import_start_time,
            import_type="text",
            records_added=0,
            records_updated=0,
            total_processed=0,
            errors=0,
            user_id=1  # Admin user ID
        )
        db.session.add(import_history)
        db.session.commit()
        
        print(f"Starting import from text data")
        
        # Parse the text content
        headers, data_rows = parse_text_data(text_content)
        
        if not headers:
            print("Error: Could not parse headers from the text content")
            import_history.errors = 1
            db.session.commit()
            return {"status": "error", "message": "Could not parse headers"}
        
        # Track statistics
        total_records = len(data_rows)
        success_count = 0
        error_count = 0
        
        # Process each row of data
        for row in data_rows:
            try:
                # Extract the basic data
                lottery_type = row.get('Game Name')
                draw_number = row.get('Draw Number')
                draw_date_str = row.get('Draw Date')
                
                # Skip if missing essential data
                if not lottery_type or not draw_number or not draw_date_str:
                    print(f"Skipping row with missing data: {row}")
                    error_count += 1
                    continue
                
                # Parse the date
                draw_date = parse_date(draw_date_str)
                if not draw_date:
                    print(f"Skipping row with invalid date: {draw_date_str}")
                    error_count += 1
                    continue
                
                # Get the winning numbers
                numbers_str = row.get('Winning Numbers (Numerical)')
                bonus_ball = row.get('Bonus Ball')
                
                if numbers_str and bonus_ball and bonus_ball != 'Data N/A':
                    full_numbers = f"{numbers_str} + {bonus_ball}"
                else:
                    full_numbers = numbers_str
                
                # Check if this result already exists
                existing_result = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=draw_number
                ).first()
                
                if existing_result:
                    # Update the existing record
                    existing_result.draw_date = draw_date
                    existing_result.numbers = full_numbers
                    
                    # Update additional fields if available
                    for field in ['Div 1 Winners', 'Div 1 Winnings', 'Div 2 Winners', 'Div 2 Winnings',
                                 'Div 3 Winners', 'Div 3 Winnings', 'Total Pool Size', 'Rollover Amount']:
                        if field in row and row[field] not in ['Data N/A', '']:
                            setattr(existing_result, field.lower().replace(' ', '_'), row[field])
                    
                    print(f"Updated existing record for {lottery_type} draw {draw_number}")
                    
                    # Create import record
                    imported_record = ImportedRecord(
                        import_id=import_history.id,
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=draw_date,
                        lottery_result_id=existing_result.id,
                        is_new=False
                    )
                    db.session.add(imported_record)
                    import_history.records_updated += 1
                    
                else:
                    # Create a new record
                    new_result = LotteryResult(
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=draw_date,
                        numbers=full_numbers
                    )
                    
                    # Set additional fields if available
                    for field in ['Div 1 Winners', 'Div 1 Winnings', 'Div 2 Winners', 'Div 2 Winnings',
                                 'Div 3 Winners', 'Div 3 Winnings', 'Total Pool Size', 'Rollover Amount']:
                        if field in row and row[field] not in ['Data N/A', '']:
                            setattr(new_result, field.lower().replace(' ', '_'), row[field])
                    
                    db.session.add(new_result)
                    db.session.flush()  # Flush to get the ID
                    
                    # Create import record
                    imported_record = ImportedRecord(
                        import_id=import_history.id,
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=draw_date,
                        lottery_result_id=new_result.id,
                        is_new=True
                    )
                    db.session.add(imported_record)
                    import_history.records_added += 1
                    
                    print(f"Added new record for {lottery_type} draw {draw_number}")
                
                success_count += 1
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                error_count += 1
                import_history.errors += 1
        
        # Update import history
        import_history.total_processed = total_records
        db.session.commit()
        
        print(f"Import completed. Total: {total_records}, Success: {success_count}, Errors: {error_count}")
        return {
            "status": "success",
            "total": total_records,
            "success": success_count,
            "errors": error_count
        }

if __name__ == "__main__":
    # Read the text file
    with open("lottery_data.txt", "r") as f:
        text_content = f.read()
    
    # Import the data
    result = import_data_to_db(text_content)
    print("Import Result:", result)