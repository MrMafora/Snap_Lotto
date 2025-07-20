#!/usr/bin/env python3
"""
Test the improved screenshot capture system
"""

import os
from screenshot_capture import capture_lottery_screenshot
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_capture():
    """Test a single lottery capture with improved system"""
    
    print("🧪 Testing Improved Screenshot Capture")
    print("=" * 50)
    
    # Test LOTTO capture
    lottery_type = 'LOTTO'
    url = 'https://www.nationallottery.co.za/'
    
    print(f"📸 Testing {lottery_type} capture from homepage...")
    
    result = capture_lottery_screenshot(lottery_type, url)
    
    if result.get('success'):
        filepath = result.get('filepath')
        file_size = result.get('file_size', 0)
        
        print(f"✅ Capture successful!")
        print(f"📁 File: {filepath}")
        print(f"📊 Size: {file_size:,} bytes")
        
        # Verify file exists and has reasonable size
        if os.path.exists(filepath) and file_size > 50000:  # At least 50KB
            print("✅ File verification passed")
            return filepath
        else:
            print("❌ File verification failed")
            return None
    else:
        error = result.get('error', 'Unknown error')
        print(f"❌ Capture failed: {error}")
        return None

def analyze_captured_screenshot(filepath):
    """Analyze captured screenshot with AI"""
    if not filepath or not os.path.exists(filepath):
        print("❌ No valid screenshot to analyze")
        return
    
    print(f"\n🧠 Analyzing captured screenshot with AI...")
    
    # Use the existing AI extraction system
    from complete_ai_workflow_test import extract_with_gemini
    
    extracted_data = extract_with_gemini(filepath)
    
    if extracted_data:
        print("✅ AI extraction successful!")
        print(f"🎯 Lottery Type: {extracted_data.get('lottery_type')}")
        print(f"📅 Draw Date: {extracted_data.get('draw_date')}")
        print(f"🔢 Main Numbers: {extracted_data.get('main_numbers')}")
        print(f"💰 Next Jackpot: R{extracted_data.get('next_jackpot'):,}" if extracted_data.get('next_jackpot') else "💰 Next Jackpot: N/A")
        print(f"📊 Confidence: {extracted_data.get('confidence')}%")
        return extracted_data
    else:
        print("❌ AI extraction failed")
        return None

if __name__ == "__main__":
    # Test the improved capture system
    captured_file = test_single_capture()
    
    if captured_file:
        # Analyze with AI
        extracted_data = analyze_captured_screenshot(captured_file)
        
        if extracted_data:
            print("\n🎉 Complete workflow test successful!")
            print("✅ Screenshot capture working")
            print("✅ AI extraction working") 
            print("✅ End-to-end lottery scanner operational")
        else:
            print("\n⚠️ Capture working but AI extraction needs attention")
    else:
        print("\n❌ Screenshot capture system needs further improvement")