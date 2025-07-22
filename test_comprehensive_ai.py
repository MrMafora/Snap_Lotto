#!/usr/bin/env python3
"""
Test the comprehensive AI processor to verify it extracts complete prize division data
"""

from ai_lottery_processor import LotteryProcessor
import json

def test_comprehensive_processor():
    print("=== TESTING COMPREHENSIVE AI PROCESSOR ===\n")
    
    # Initialize the processor
    processor = LotteryProcessor()
    
    # Run comprehensive processing
    result = processor.process_all_screenshots()
    
    print("Processing Results:")
    print(f"- Total Processed: {result.get('total_processed', 0)}")
    print(f"- Total Success: {result.get('total_success', 0)}")
    print(f"- Total Failed: {result.get('total_failed', 0)}")
    print(f"- Database Records: {len(result.get('database_records', []))}")
    
    if result.get('database_records'):
        print(f"\nNew Records Created:")
        for record in result['database_records'][:3]:  # Show first 3
            print(f"- ID {record['record_id']}: {record['lottery_type']} Draw {record['draw_number']}")
            if 'prize_divisions' in record:
                print(f"  Prize Divisions: {len(record.get('prize_divisions', []))} divisions")
            if 'financial_data' in record:
                financial = record['financial_data']
                print(f"  Next Jackpot: {financial.get('next_jackpot', 'N/A')}")
                print(f"  Total Sales: {financial.get('total_sales', 'N/A')}")
    
    print(f"\nProcessor Status: {'✅ SUCCESS' if result.get('total_success', 0) > 0 else '❌ NO NEW RESULTS'}")
    
    return result

if __name__ == "__main__":
    result = test_comprehensive_processor()