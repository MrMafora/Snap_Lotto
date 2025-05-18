import os
import pandas as pd
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

def import_template_data(template_path):
    # Import the models to use
    from models import db, LotteryResult, ImportHistory, ImportedRecord
    
    app = create_app()
    db.init_app(app)
    
    # Process within the application context
    with app.app_context():
        import_start_time = datetime.now()
        filename = os.path.basename(template_path)
        
        # Create import history record
        import_history = ImportHistory(
            file_name=filename,
            import_date=import_start_time,
            import_type="template",
            records_added=0,
            records_updated=0,
            total_processed=0,
            errors=0,
            user_id=1  # Admin user ID
        )
        db.session.add(import_history)
        db.session.commit()
        
        print(f"Starting import from template: {filename}")
        
        # Track statistics
        total_records = 0
        success_count = 0
        error_count = 0
        sheet_results = {}
        
        # Process each sheet (lottery type)
        try:
            excel_file = pd.ExcelFile(template_path)
            sheet_names = excel_file.sheet_names
            
            # Skip the Instructions sheet if present
            if 'Instructions' in sheet_names:
                sheet_names.remove('Instructions')
            
            for sheet_name in sheet_names:
                print(f"Processing sheet: {sheet_name}")
                
                # Read the sheet data
                sheet_data = pd.read_excel(template_path, sheet_name=sheet_name)
                
                # Skip empty sheets
                if sheet_data.empty:
                    print(f"Sheet {sheet_name} is empty, skipping.")
                    continue
                
                # Normalize the lottery type name
                lottery_type = sheet_name
                
                # Process each row in the sheet
                for index, row in sheet_data.iterrows():
                    total_records += 1
                    
                    try:
                        # Extract the data from the row
                        draw_date = row.get('Draw Date')
                        draw_number = row.get('Draw Number')
                        
                        # Convert draw number to string if it's not already
                        if draw_number and not isinstance(draw_number, str):
                            draw_number = str(int(draw_number))
                        
                        # Skip if date or draw number is missing
                        if pd.isna(draw_date) or pd.isna(draw_number):
                            print(f"Skipping row {index} with missing date or draw number")
                            error_count += 1
                            continue
                        
                        # Get the numbers
                        numbers = []
                        for i in range(1, 7):  # Regular numbers 1-6
                            num_col = f'Ball {i}'
                            if num_col in row and not pd.isna(row[num_col]):
                                numbers.append(str(int(row[num_col])))
                        
                        # Check if we have the bonus ball (Powerball games)
                        bonus = None
                        if 'Powerball' in lottery_type or 'Bonus Ball' in row:
                            bonus_col = 'Powerball' if 'Powerball' in lottery_type else 'Bonus Ball'
                            if bonus_col in row and not pd.isna(row[bonus_col]):
                                bonus = str(int(row[bonus_col]))
                        
                        # Format the numbers string
                        numbers_str = ', '.join(numbers)
                        if bonus:
                            numbers_str += f" + {bonus}"
                        
                        # Check if the result already exists
                        existing_result = LotteryResult.query.filter_by(
                            lottery_type=lottery_type,
                            draw_number=draw_number
                        ).first()
                        
                        if existing_result:
                            # Update existing record
                            existing_result.draw_date = draw_date
                            existing_result.numbers = numbers_str
                            print(f"Updated existing record for {lottery_type} draw {draw_number}")
                        else:
                            # Create new record
                            new_result = LotteryResult(
                                lottery_type=lottery_type,
                                draw_number=draw_number,
                                draw_date=draw_date,
                                numbers=numbers_str
                            )
                            db.session.add(new_result)
                            print(f"Added new record for {lottery_type} draw {draw_number}")
                        
                        # Create imported record entry
                        imported_record = ImportedRecord(
                            import_id=import_history.id,
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            status="success",
                            error_message=""
                        )
                        db.session.add(imported_record)
                        
                        success_count += 1
                        
                    except Exception as e:
                        print(f"Error processing row {index}: {str(e)}")
                        error_count += 1
                        
                        # Create error record
                        imported_record = ImportedRecord(
                            import_id=import_history.id,
                            lottery_type=lottery_type,
                            draw_number=str(row.get('Draw Number', 'Unknown')),
                            draw_date=row.get('Draw Date', None),
                            status="error",
                            error_message=str(e)
                        )
                        db.session.add(imported_record)
                
                # Commit after each sheet
                db.session.commit()
                sheet_results[sheet_name] = {
                    'processed': total_records,
                    'success': success_count,
                    'errors': error_count
                }
            
            # Update import history
            import_history.total_processed = total_records
            import_history.records_added = success_count
            import_history.errors = error_count
            db.session.commit()
            
            print(f"Import completed successfully. Total: {total_records}, Success: {success_count}, Errors: {error_count}")
            return {
                'status': 'success',
                'total': total_records,
                'success': success_count,
                'errors': error_count,
                'sheet_results': sheet_results
            }
            
        except Exception as e:
            # Update import history with error
            import_history.errors = total_records
            db.session.commit()
            
            print(f"Import failed: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

if __name__ == "__main__":
    # Path to the template file
    template_path = "uploads/latest_template.xlsx"
    
    # Run the import
    result = import_template_data(template_path)
    print("Import Result:", result)