#!/usr/bin/env python3
"""
Script to update Lottery Plus 2 draw #2537 with real numbers.
Currently this draw has placeholder numbers that need to be replaced.
"""

from main import app
from models import LotteryResult, db, ImportHistory, ImportedRecord
from datetime import datetime
import json
import argparse

def update_lottery_plus_2(draw_number, numbers, bonus):
    """
    Update Lottery Plus 2 draw with real numbers.
    
    Args:
        draw_number (str): The draw number to update
        numbers (list): List of 6 winning numbers
        bonus (int): The bonus number
        
    Returns:
        bool: Success status
    """
    with app.app_context():
        # Create import history record
        import_history = ImportHistory(
            import_date=datetime.utcnow(),
            import_type='manual-update',
            file_name='lottery-plus-2-update',
            records_added=0,
            records_updated=0,
            total_processed=0,
            errors=0
        )
        db.session.add(import_history)
        db.session.commit()
        import_history_id = import_history.id
        
        # Find the record
        result = LotteryResult.query.filter_by(
            lottery_type='Lottery Plus 2',
            draw_number=draw_number
        ).first()
        
        if not result:
            print(f"Error: Lottery Plus 2 Draw #{draw_number} not found in database")
            return False
        
        # Get old values for comparison
        old_numbers = json.loads(result.numbers) if result.numbers else []
        old_bonus = json.loads(result.bonus_numbers)[0] if result.bonus_numbers else None
        
        # Update with real numbers
        result.numbers = json.dumps(numbers)
        result.bonus_numbers = json.dumps([bonus])
        result.source_url = 'manually-updated'
        
        # Create imported record
        imported_record = ImportedRecord(
            import_id=import_history_id,
            lottery_type='Lottery Plus 2',
            draw_number=draw_number,
            draw_date=result.draw_date,
            is_new=False,
            lottery_result_id=result.id
        )
        db.session.add(imported_record)
        
        # Update import history
        import_history.records_updated = 1
        import_history.total_processed = 1
        db.session.commit()
        
        print(f"Updated Lottery Plus 2 Draw #{draw_number}:")
        print(f"- Old numbers: {old_numbers}, bonus: {old_bonus}")
        print(f"- New numbers: {numbers}, bonus: {bonus}")
        
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update Lottery Plus 2 draw with real numbers')
    parser.add_argument('draw_number', type=str, help='Draw number to update (e.g., 2537)')
    parser.add_argument('numbers', type=str, help='Six winning numbers separated by spaces (e.g., "1 5 10 15 20 25")')
    parser.add_argument('bonus', type=int, help='Bonus number (e.g., 30)')
    
    args = parser.parse_args()
    
    # Parse the numbers
    try:
        winning_numbers = [int(num) for num in args.numbers.split()]
        if len(winning_numbers) != 6:
            print(f"Error: Expected 6 winning numbers, got {len(winning_numbers)}")
            exit(1)
    except ValueError:
        print("Error: Numbers must be integers")
        exit(1)
    
    # Update the record
    success = update_lottery_plus_2(args.draw_number, winning_numbers, args.bonus)
    
    if success:
        print("Update completed successfully!")
    else:
        print("Update failed.")