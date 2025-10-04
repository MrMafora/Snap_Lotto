#!/usr/bin/env python3
"""
Process existing screenshots and update database
"""

import sys
sys.path.append('.')

from ai_lottery_processor import CompleteLotteryProcessor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Process existing screenshots"""
    print("="*60)
    print("PROCESSING EXISTING SCREENSHOTS")
    print("="*60)
    
    try:
        processor = CompleteLotteryProcessor()
        result = processor.process_all_screenshots()
        
        print("\n" + "="*60)
        print("PROCESSING RESULTS")
        print("="*60)
        print(f"Total Processed: {result.get('total_processed', 0)}")
        print(f"Successful:      {result.get('total_success', 0)}")
        print(f"Failed:          {result.get('total_failed', 0)}")
        print(f"Database Records: {len(result.get('database_records', []))}")
        print("="*60)
        
        # Display successful extractions
        if result.get('database_records'):
            print("\n✅ NEW LOTTERY RESULTS ADDED:")
            for record in result.get('database_records', []):
                print(f"  - {record.get('lottery_type')} ({record.get('draw_date')})")
        
        if result.get('total_success', 0) > 0:
            print("\n✅ Database updated successfully!")
        else:
            print("\n⚠️  No new data was added to database")
            
    except Exception as e:
        logger.error(f"Error processing screenshots: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    main()
