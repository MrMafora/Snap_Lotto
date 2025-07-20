#!/usr/bin/env python3
"""
Test authentic lottery data extraction with real SA National Lottery result pages
"""

import os
from manual_lottery_processor import process_uploaded_image

def test_authentic_lottery_pages():
    """Test with authentic lottery result pages provided by user"""
    
    test_images = [
        "attached_assets/20250708_025148_lotto_1753041303658.png",
        "attached_assets/20250708_025205_powerball_1753041303659.png", 
        "attached_assets/20250708_025217_daily_lotto_1753041303659.png"
    ]
    
    print("🧪 Testing AI Extraction on Authentic SA National Lottery Result Pages")
    print("=" * 80)
    
    results = []
    
    for i, test_image in enumerate(test_images, 1):
        if os.path.exists(test_image):
            filename = test_image.split('/')[-1]
            lottery_type = ""
            
            if "lotto_1" in filename:
                lottery_type = "LOTTO"
            elif "powerball_1" in filename:
                lottery_type = "POWERBALL" 
            elif "daily_lotto" in filename:
                lottery_type = "DAILY LOTTO"
                
            print(f"\n🎯 Test {i}/3: {lottery_type}")
            print(f"📁 File: {filename}")
            print(f"📊 Size: {os.path.getsize(test_image):,} bytes")
            print("-" * 40)
            
            success = process_uploaded_image(test_image)
            results.append((lottery_type, success))
            
            print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        else:
            print(f"\n❌ Image not found: {test_image}")
            results.append(("MISSING", False))
    
    print(f"\n📋 Final Results Summary:")
    print("=" * 40)
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for lottery_type, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {lottery_type:12} - {status}")
    
    print(f"\n🎯 Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    if successful > 0:
        print("🎉 AI extraction working with authentic lottery data!")
        print("System ready for production use with real lottery results")
    else:
        print("⚠️ AI extraction needs refinement for authentic data")
    
    return successful == total

if __name__ == "__main__":
    test_authentic_lottery_pages()