import pandas as pd
import sys
import traceback
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_daily_lottery():
    """Update Daily Lottery data to have consistent lottery type"""
    from main import app, db
    from models import LotteryResult, ImportedRecord
    
    with app.app_context():
        try:
            # Standardize Daily Lottery name format
            daily_lotto_records = LotteryResult.query.filter_by(lottery_type='Daily Lotto').all()
            daily_lottery_records = LotteryResult.query.filter_by(lottery_type='Daily Lottery').all()
            
            logger.info(f"Found {len(daily_lotto_records)} Daily Lotto records")
            logger.info(f"Found {len(daily_lottery_records)} Daily Lottery records")
            
            # First, check for duplicates
            draw_numbers = {}
            for record in daily_lotto_records:
                draw_num = record.draw_number
                if draw_num.startswith('Draw '):
                    draw_num = draw_num.replace('Draw ', '')
                
                if draw_num not in draw_numbers:
                    draw_numbers[draw_num] = []
                draw_numbers[draw_num].append({
                    'id': record.id,
                    'type': 'Daily Lotto'
                })
                
            for record in daily_lottery_records:
                draw_num = record.draw_number
                if draw_num.startswith('Draw '):
                    draw_num = draw_num.replace('Draw ', '')
                
                if draw_num not in draw_numbers:
                    draw_numbers[draw_num] = []
                draw_numbers[draw_num].append({
                    'id': record.id,
                    'type': 'Daily Lottery'
                })
            
            # Process duplicates
            duplicates = 0
            duplicate_removals = 0
            for draw_num, records in draw_numbers.items():
                if len(records) > 1:
                    duplicates += 1
                    
                    # Keep Daily Lottery version if available, otherwise keep the first one
                    keep_id = None
                    for record in records:
                        if record['type'] == 'Daily Lottery':
                            keep_id = record['id']
                            break
                    
                    if not keep_id:
                        keep_id = records[0]['id']
                    
                    # Delete others
                    for record in records:
                        if record['id'] != keep_id:
                            # First delete associated imported records
                            ImportedRecord.query.filter_by(lottery_result_id=record['id']).delete()
                            # Then delete the lottery result
                            LotteryResult.query.filter_by(id=record['id']).delete()
                            duplicate_removals += 1
            
            db.session.commit()
            logger.info(f"Found {duplicates} duplicate draw numbers, removed {duplicate_removals} duplicate records")
            
            # Update remaining records
            daily_lotto_records = LotteryResult.query.filter_by(lottery_type='Daily Lotto').all()
            
            updated_count = 0
            fixed_draw_numbers = 0
            
            for record in daily_lotto_records:
                # Fix lottery type
                record.lottery_type = 'Daily Lottery'
                updated_count += 1
                
                # Fix draw number format if needed
                if record.draw_number.startswith('Draw '):
                    record.draw_number = record.draw_number.replace('Draw ', '')
                    fixed_draw_numbers += 1
            
            db.session.commit()
            logger.info(f"Updated {updated_count} records to Daily Lottery")
            logger.info(f"Fixed {fixed_draw_numbers} draw numbers with 'Draw ' prefix")
            
            # Check remaining Daily Lottery records for prefix issues
            daily_records = LotteryResult.query.filter_by(lottery_type='Daily Lottery').all()
            prefix_fixes = 0
            
            for record in daily_records:
                if record.draw_number.startswith('Draw '):
                    record.draw_number = record.draw_number.replace('Draw ', '')
                    prefix_fixes += 1
            
            if prefix_fixes > 0:
                db.session.commit()
                logger.info(f"Fixed additional {prefix_fixes} draw numbers with 'Draw ' prefix")
            
            # Get current count
            final_count = LotteryResult.query.filter_by(lottery_type='Daily Lottery').count()
            logger.info(f"Now have {final_count} Daily Lottery records in total")
            
            return {
                'daily_lotto_count_before': len(daily_lotto_records),
                'daily_lottery_count_before': len(daily_lottery_records),
                'duplicates_found': duplicates,
                'duplicates_removed': duplicate_removals,
                'records_updated': updated_count,
                'draw_numbers_fixed': fixed_draw_numbers + prefix_fixes,
                'final_daily_lottery_count': final_count
            }
            
        except Exception as e:
            logger.error(f"Error standardizing Daily Lottery data: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'error': str(e)
            }

if __name__ == "__main__":
    stats = process_daily_lottery()
    
    # Print summary
    print("\n=== DAILY LOTTERY UPDATE SUMMARY ===")
    for key, value in stats.items():
        print(f"{key}: {value}")