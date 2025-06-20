#!/usr/bin/env python3
"""
Test the enhanced lottery extraction with all three sections
"""
import os
import json
import logging
from step3_ai_process import setup_gemini, extract_lottery_data_from_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_extraction():
    """Test enhanced extraction on available screenshots"""
    logger.info("Testing enhanced lottery extraction with 3 sections")
    
    model = setup_gemini()
    if not model:
        logger.error("Failed to setup Gemini model")
        return False
    
    # Test on available screenshots
    screenshot_dir = 'screenshots'
    if not os.path.exists(screenshot_dir):
        logger.error("Screenshots directory not found")
        return False
    
    test_files = [
        '20250620_190405_lotto.png',
        '20250620_190128_lotto_plus_1.png',
        '20250620_190139_powerball.png'
    ]
    
    results = []
    
    for filename in test_files:
        filepath = os.path.join(screenshot_dir, filename)
        if os.path.exists(filepath):
            logger.info(f"Testing extraction on: {filename}")
            
            result = extract_lottery_data_from_image(model, filepath)
            if result:
                try:
                    data = json.loads(result)
                    
                    print(f"\n=== {filename} ===")
                    print("SECTION 1 - Basic Results:")
                    print(f"  Type: {data.get('lottery_type', 'N/A')}")
                    print(f"  Date: {data.get('draw_date', 'N/A')}")
                    print(f"  Draw: {data.get('draw_number', 'N/A')}")
                    print(f"  Numbers: {data.get('main_numbers', [])}")
                    print(f"  Bonus: {data.get('bonus_numbers', [])}")
                    
                    print("\nSECTION 2 - Prize Divisions:")
                    divisions = data.get('prize_divisions', [])
                    if divisions:
                        for div in divisions:
                            print(f"  {div.get('division', 'N/A')}: {div.get('winners', 0)} winners @ {div.get('prize_amount', 'N/A')}")
                    else:
                        print("  No prize division data extracted")
                    print(f"  Total Pool: {data.get('total_prize_pool', 'N/A')}")
                    print(f"  Rollover: {data.get('rollover_amount', 'N/A')}")
                    
                    print("\nSECTION 3 - Additional Information:")
                    print(f"  Next Draw: {data.get('next_draw_date', 'N/A')}")
                    print(f"  Est. Jackpot: {data.get('estimated_jackpot', 'N/A')}")
                    print(f"  Extra Info: {data.get('additional_info', 'N/A')}")
                    
                    results.append(data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed for {filename}: {e}")
                    print(f"Raw response: {result[:300]}...")
            else:
                logger.warning(f"No result for {filename}")
    
    # Save test results
    if results:
        with open('enhanced_extraction_test.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved {len(results)} test results to enhanced_extraction_test.json")
    
    return len(results) > 0

if __name__ == "__main__":
    success = test_enhanced_extraction()
    print(f"\nTest completed: {'SUCCESS' if success else 'FAILED'}")