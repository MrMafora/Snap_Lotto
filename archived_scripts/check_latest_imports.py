import sys
import os
import json
from datetime import datetime
from sqlalchemy.orm import joinedload

# Import app and database
try:
    from main import app, db
    from models import LotteryResult, ImportHistory, ImportedRecord
except ImportError:
    print("Could not import app or models. Make sure you're in the right directory.")
    sys.exit(1)

def check_latest_imports():
    """Check recently imported data by lottery type"""
    with app.app_context():
        # Get most recent import
        latest_import = ImportHistory.query.order_by(ImportHistory.import_date.desc()).first()
        
        if not latest_import:
            print("No import history found.")
            return
        
        print(f"\nLatest import: {latest_import.file_name} on {latest_import.import_date}")
        print(f"Total processed: {latest_import.total_processed}")
        print(f"Records added: {latest_import.records_added}")
        print(f"Records updated: {latest_import.records_updated}")
        print(f"Errors: {latest_import.errors}")
        
        # Get counts by lottery type
        lottery_types = db.session.query(
            LotteryResult.lottery_type, 
            db.func.count(LotteryResult.id)
        ).group_by(LotteryResult.lottery_type).all()
        
        print("\nRecords by lottery type:")
        for lottery_type, count in lottery_types:
            print(f"  {lottery_type}: {count} records")
        
        # Check imported records from latest import
        imported_records = ImportedRecord.query.filter_by(import_id=latest_import.id).all()
        
        import_counts = {}
        for record in imported_records:
            lottery_type = record.lottery_type
            if lottery_type not in import_counts:
                import_counts[lottery_type] = {
                    'new': 0,
                    'updated': 0,
                    'total': 0
                }
            
            import_counts[lottery_type]['total'] += 1
            if record.is_new:
                import_counts[lottery_type]['new'] += 1
            else:
                import_counts[lottery_type]['updated'] += 1
        
        print("\nLatest import by lottery type:")
        for lottery_type, counts in import_counts.items():
            print(f"  {lottery_type}: {counts['total']} records ({counts['new']} new, {counts['updated']} updated)")
        
        # Check PowerBall and Daily Lottery specifically
        print("\nChecking PowerBall data:")
        powerball_records = LotteryResult.query.filter(
            LotteryResult.lottery_type.in_(['Powerball', 'PowerBall', 'Powerball Plus', 'PowerBall PLUS'])
        ).order_by(LotteryResult.draw_number.desc()).limit(5).all()
        
        if powerball_records:
            for record in powerball_records:
                numbers = json.loads(record.numbers) if record.numbers else []
                bonus = json.loads(record.bonus_numbers) if record.bonus_numbers else []
                print(f"  {record.lottery_type} Draw {record.draw_number}: Numbers: {numbers}, Bonus: {bonus}")
        else:
            print("  No PowerBall records found.")
        
        print("\nChecking Daily Lottery data:")
        daily_records = LotteryResult.query.filter(
            LotteryResult.lottery_type.in_(['Daily Lottery', 'Daily Lotto'])
        ).order_by(LotteryResult.draw_number.desc()).limit(5).all()
        
        if daily_records:
            for record in daily_records:
                numbers = json.loads(record.numbers) if record.numbers else []
                print(f"  {record.lottery_type} Draw {record.draw_number}: Numbers: {numbers}")
        else:
            print("  No Daily Lottery records found.")

def run_import():
    """Run another import to ensure all data is imported"""
    try:
        from direct_excel_import import direct_excel_import
    except ImportError:
        print("Could not import direct_excel_import. Make sure script is available.")
        return
    
    excel_path = "attached_assets/lottery_data_template_20250426_012917.xlsx"
    print(f"\nRunning fresh import from: {excel_path}")
    
    with app.app_context():
        stats = direct_excel_import(excel_path, app)
        
        print("\nImport statistics:")
        print(f"Total processed: {stats['total_processed']}")
        print(f"New records: {stats['new_records']}")
        print(f"Updated records: {stats['updated_records']}")
        print(f"Errors: {stats['errors']}")
        
        print("\nBy lottery type:")
        for lottery_type, type_stats in stats['lottery_types'].items():
            print(f"  {lottery_type}: {type_stats['processed']} processed "
                 f"({type_stats['new']} new, {type_stats['updated']} updated, "
                 f"{type_stats['errors']} errors)")
    
if __name__ == "__main__":
    check_latest_imports()
    
    # Ask if user wants to run an import
    user_input = input("\nDo you want to run a fresh import? (y/n): ")
    if user_input.lower() == 'y':
        run_import()
        check_latest_imports()