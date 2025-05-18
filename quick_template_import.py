import os
import pandas as pd
from flask import Flask
from sqlalchemy.orm import Session
from datetime import datetime

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

def batch_import_template(template_path, batch_size=10):
    """Import template data in smaller batches to avoid timeouts"""
    # Import the models to use
    from models import db, LotteryResult, ImportHistory, ImportedRecord
    
    app = create_app()
    db.init_app(app)
    
    # Template filename
    filename = os.path.basename(template_path)
    
    # Process within the application context
    with app.app_context():
        # Load template sheet names
        try:
            excel_file = pd.ExcelFile(template_path)
            sheet_names = excel_file.sheet_names
            
            # Skip the Instructions sheet if present
            if 'Instructions' in sheet_names:
                sheet_names.remove('Instructions')
                
            # Create import history record
            import_history = ImportHistory(
                file_name=filename,
                import_date=datetime.now(),
                import_type="template_quick",
                records_added=0,
                records_updated=0,
                total_processed=0,
                errors=0,
                user_id=1  # Admin user ID
            )
            db.session.add(import_history)
            db.session.commit()
            
            # Process each sheet
            stats = {
                'total': 0,
                'added': 0,
                'updated': 0,
                'errors': 0
            }
            
            for sheet_name in sheet_names:
                print(f"Processing sheet: {sheet_name}")
                
                # Read the sheet data
                df = pd.read_excel(template_path, sheet_name=sheet_name)
                
                # Skip empty sheets
                if df.empty:
                    print(f"Sheet {sheet_name} is empty, skipping.")
                    continue
                
                # Normalize the lottery type name
                lottery_type = sheet_name
                
                # Process rows in batches
                for i in range(0, len(df), batch_size):
                    batch_df = df.iloc[i:i+batch_size]
                    
                    batch_stats = process_batch(batch_df, lottery_type, import_history.id, filename, db)
                    
                    # Update stats
                    stats['total'] += batch_stats['total']
                    stats['added'] += batch_stats['added']
                    stats['updated'] += batch_stats['updated']
                    stats['errors'] += batch_stats['errors']
                    
                    # Update import history
                    import_history.total_processed = stats['total']
                    import_history.records_added = stats['added']
                    import_history.records_updated = stats['updated']
                    import_history.errors = stats['errors']
                    db.session.commit()
                    
                    print(f"Batch processed: {i}-{i+len(batch_df)} of {len(df)} rows in {sheet_name}")
            
            print(f"Import completed: Total: {stats['total']}, Added: {stats['added']}, Updated: {stats['updated']}, Errors: {stats['errors']}")
            return stats
            
        except Exception as e:
            print(f"Import failed: {str(e)}")
            if 'import_history' in locals():
                # Update import history with error details
                import_history.errors += 1
                db.session.commit()
            return {'error': str(e)}

def process_batch(batch_df, lottery_type, import_id, filename, db):
    """Process a batch of rows from the Excel file"""
    from models import LotteryResult, ImportedRecord
    
    batch_stats = {
        'total': 0,
        'added': 0,
        'updated': 0,
        'errors': 0
    }
    
    for _, row in batch_df.iterrows():
        batch_stats['total'] += 1
        
        try:
            # Extract the data from the row
            draw_date = row.get('Draw Date')
            draw_number = row.get('Draw Number')
            
            # Skip if missing essential data
            if pd.isna(draw_date) or pd.isna(draw_number):
                print(f"Skipping row with missing date or draw number")
                batch_stats['errors'] += 1
                continue
            
            # Convert draw number to string
            if draw_number and not isinstance(draw_number, str):
                draw_number = str(int(draw_number))
            
            # Get the numbers
            numbers = []
            for i in range(1, 7):  # Regular numbers 1-6
                num_col = f'Ball {i}'
                if num_col in row and not pd.isna(row[num_col]):
                    numbers.append(str(int(row[num_col])))
            
            # Check if we have the bonus ball
            bonus = None
            if 'Powerball' in lottery_type or 'Bonus Ball' in row:
                bonus_col = 'Powerball' if 'Powerball' in lottery_type else 'Bonus Ball'
                if bonus_col in row and not pd.isna(row[bonus_col]):
                    bonus = str(int(row[bonus_col]))
            
            # Format the numbers string
            numbers_str = ', '.join(numbers)
            if bonus:
                numbers_str += f" + {bonus}"
            
            # Create source URL for template import
            template_source_url = f"template://{filename}/{lottery_type}/{draw_number}"
            
            # Check if result already exists
            existing_result = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if existing_result:
                # Update existing record
                existing_result.draw_date = draw_date
                existing_result.numbers = numbers_str
                print(f"Updated record: {lottery_type} draw {draw_number}")
                batch_stats['updated'] += 1
                is_new = False
                result_id = existing_result.id
            else:
                # Create new record
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=draw_number,
                    draw_date=draw_date,
                    numbers=numbers_str,
                    source_url=template_source_url
                )
                db.session.add(new_result)
                db.session.flush()  # Ensure we have an ID
                print(f"Added record: {lottery_type} draw {draw_number}")
                batch_stats['added'] += 1
                is_new = True
                result_id = new_result.id
            
            # Create imported record entry
            imported_record = ImportedRecord(
                import_id=import_id,
                lottery_type=lottery_type,
                draw_number=draw_number,
                draw_date=draw_date,
                is_new=is_new,
                lottery_result_id=result_id
            )
            db.session.add(imported_record)
            
        except Exception as e:
            print(f"Error processing row: {str(e)}")
            batch_stats['errors'] += 1
    
    # Commit the batch
    db.session.commit()
    
    return batch_stats

if __name__ == "__main__":
    # Path to the template file
    template_path = "uploads/latest_template.xlsx"
    
    # Run the import with batch size of 5
    result = batch_import_template(template_path, batch_size=5)
    print("Import Result:", result)