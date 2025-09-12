#!/usr/bin/env python3
"""
Update missing prize division data for recent records using comprehensive AI processor
"""

from ai_lottery_processor import CompleteLotteryProcessor
import psycopg2
import json
import os

def update_missing_prize_data():
    """Update records that are missing prize division data"""
    
    # Check which records need prize division data
    db_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Find records missing prize divisions (NULL or empty array)
    cur.execute("""
        SELECT id, lottery_type, draw_number, draw_date 
        FROM lottery_results 
        WHERE id >= 114 
        AND (prize_divisions IS NULL OR prize_divisions = '[]' OR prize_divisions = 'null')
        ORDER BY id;
    """)
    
    missing_records = cur.fetchall()
    conn.close()
    
    print(f"Found {len(missing_records)} records missing prize division data:")
    for record in missing_records:
        print(f"  - ID {record[0]}: {record[1]} Draw {record[2]} ({record[3]})")
    
    if len(missing_records) == 0:
        print("✅ All recent records have prize division data")
        return
    
    # Run comprehensive processor to get complete data
    print(f"\nRunning comprehensive AI processor to extract complete prize data...")
    
    try:
        processor = CompleteLotteryProcessor()
        result = processor.process_all_screenshots()
        
        print(f"Processing results:")
        print(f"- Total processed: {result.get('total_processed', 0)}")
        print(f"- Total success: {result.get('total_success', 0)}")
        print(f"- Database records: {len(result.get('database_records', []))}")
        
        if result.get('total_success', 0) > 0:
            print(f"✅ Successfully updated lottery data with complete prize divisions")
            
            # Show some examples of the new data
            for record_data in result.get('database_records', [])[:2]:
                if isinstance(record_data, dict):
                    lottery_type = record_data.get('lottery_type', 'Unknown')
                    draw_number = record_data.get('draw_number', 'Unknown')
                    prize_count = len(record_data.get('prize_divisions', []))
                    print(f"  - {lottery_type} Draw {draw_number}: {prize_count} prize divisions")
        else:
            print("ℹ️ No new results - existing data is current")
            
    except Exception as e:
        print(f"❌ Error running processor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_missing_prize_data()