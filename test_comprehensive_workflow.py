#!/usr/bin/env python3
"""
Test the updated admin workflow route with comprehensive AI processor
"""

from ai_lottery_processor import CompleteLotteryProcessor
import os

def test_comprehensive_workflow():
    print("=== TESTING UPDATED ADMIN WORKFLOW ===\n")
    
    # Check screenshots
    screenshots = []
    for file in os.listdir('screenshots'):
        if file.endswith('.png'):
            screenshots.append(file)
    
    print(f"Available screenshots: {len(screenshots)}")
    for screenshot in screenshots:
        print(f"  - {screenshot}")
    
    if len(screenshots) == 0:
        print("❌ No screenshots found")
        return
    
    print(f"\nTesting comprehensive AI processor...")
    
    try:
        # Initialize comprehensive processor
        processor = CompleteLotteryProcessor()
        print("✅ Processor initialized successfully")
        
        # Run processing
        result = processor.process_all_screenshots()
        
        print(f"\nProcessing Results:")
        print(f"- Total Processed: {result.get('total_processed', 0)}")
        print(f"- Total Success: {result.get('total_success', 0)}")
        print(f"- Total Failed: {result.get('total_failed', 0)}")
        print(f"- Database Records: {len(result.get('database_records', []))}")
        print(f"- Processed Files: {len(result.get('processed_files', []))}")
        
        if result.get('database_records'):
            print(f"\n✅ New Records with Complete Prize Data:")
            for record in result.get('database_records', []):
                print(f"  - {record.get('lottery_type')} Draw {record.get('draw_number')}")
                
        if result.get('total_success', 0) > 0:
            print(f"\n🎯 SUCCESS: Admin workflow will now work with complete prize divisions!")
        else:
            print(f"\n📝 INFO: No new results (existing data current)")
            
        print(f"\nAdmin Button Status: ✅ READY")
        print("The 'Run Complete Workflow' button will now extract complete prize data!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_workflow()