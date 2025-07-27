#!/usr/bin/env python3
"""
Manual extraction of Saturday lottery results from captured screenshots
This will extract ALL 6 lottery types for complete Saturday data
"""

import sys
import os
import json
import psycopg2
from datetime import datetime

# Add current directory to Python path
sys.path.append('.')

from ai_lottery_processor import CompleteLotteryProcessor

def main():
    print("🎯 EXTRACTING COMPLETE SATURDAY LOTTERY RESULTS")
    print("=" * 60)
    
    # Initialize AI processor
    processor = CompleteLotteryProcessor()
    
    # Screenshot files from Saturday automation
    screenshots = [
        ('screenshots/20250727_201610_lotto.png', 'LOTTO'),
        ('screenshots/20250727_201610_lotto_plus_1.png', 'LOTTO PLUS 1'),
        ('screenshots/20250727_201610_lotto_plus_2.png', 'LOTTO PLUS 2'),
        ('screenshots/20250727_201610_powerball.png', 'POWERBALL'),
        ('screenshots/20250727_201610_powerball_plus.png', 'POWERBALL PLUS'),
        ('screenshots/20250727_201610_daily_lotto.png', 'DAILY LOTTO')
    ]
    
    # Connect to database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    new_results = []
    
    for screenshot_path, lottery_type in screenshots:
        if not os.path.exists(screenshot_path):
            print(f"❌ Screenshot not found: {screenshot_path}")
            continue
            
        print(f"🔍 Processing {lottery_type}: {screenshot_path}")
        
        try:
            # Process with AI
            result = processor.process_single_image(screenshot_path, lottery_type)
            
            if result:
                data = result
                draw_number = data.get('draw_id', '')
                draw_date = data.get('draw_date', '')
                winning_numbers = data.get('winning_numbers', [])
                bonus_numbers = data.get('bonus_numbers', [])
                confidence = data.get('extraction_confidence', 0)
                
                # Check if newer than database
                cur.execute('''
                    SELECT draw_date FROM lottery_results 
                    WHERE lottery_type = %s 
                    ORDER BY draw_date DESC LIMIT 1
                ''', (lottery_type,))
                
                latest_db_date = cur.fetchone()
                latest_db_date = latest_db_date[0] if latest_db_date else None
                
                # Only insert if data is newer or different
                if draw_date and (not latest_db_date or draw_date > str(latest_db_date)):
                    # Check if already exists
                    cur.execute('''
                        SELECT COUNT(*) FROM lottery_results 
                        WHERE lottery_type = %s AND draw_number = %s AND draw_date = %s
                    ''', (lottery_type, draw_number, draw_date))
                    
                    if cur.fetchone()[0] == 0:
                        # Insert new result
                        cur.execute('''
                            INSERT INTO lottery_results 
                            (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                        ''', (
                            lottery_type,
                            draw_number,
                            draw_date,
                            json.dumps(winning_numbers),
                            json.dumps(bonus_numbers) if bonus_numbers else None
                        ))
                        
                        new_results.append({
                            'lottery_type': lottery_type,
                            'draw_number': draw_number,
                            'draw_date': draw_date,
                            'numbers': winning_numbers,
                            'bonus': bonus_numbers,
                            'confidence': confidence
                        })
                        
                        bonus_str = f" + {bonus_numbers}" if bonus_numbers else ""
                        print(f"✅ INSERTED: {lottery_type} Draw {draw_number} ({draw_date})")
                        print(f"   Numbers: {winning_numbers}{bonus_str} - {confidence}% confidence")
                    else:
                        print(f"ℹ️  SKIPPED: {lottery_type} Draw {draw_number} already exists")
                else:
                    print(f"ℹ️  SKIPPED: {lottery_type} - no newer data than {latest_db_date}")
                    
            else:
                print(f"❌ FAILED: {lottery_type} - could not extract data")
                
        except Exception as e:
            print(f"❌ ERROR processing {lottery_type}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print(f"🎯 EXTRACTION COMPLETE - {len(new_results)} new results added")
    
    if new_results:
        print("\n📊 NEW SATURDAY RESULTS:")
        for result in new_results:
            bonus_str = f" + {result['bonus']}" if result['bonus'] else ""
            print(f"   {result['lottery_type']} Draw {result['draw_number']}: {result['numbers']}{bonus_str}")
    
    return new_results

if __name__ == "__main__":
    main()