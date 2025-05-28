#!/usr/bin/env python3
"""
Quick test script to verify automation functionality works
"""
import os
import sys
sys.path.append(os.getcwd())

from main import app
from daily_automation import DailyLotteryAutomation

def test_cleanup():
    """Test the cleanup old screenshots functionality"""
    print("Testing Clear Old Screenshots functionality...")
    
    with app.app_context():
        automation = DailyLotteryAutomation(app)
        
        try:
            success, count = automation.cleanup_old_screenshots()
            if success:
                print(f"✅ SUCCESS: Cleared {count} old screenshot files")
            else:
                print(f"❌ FAILED: Could not clear screenshots (count: {count})")
            return success
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False

def test_capture():
    """Test the screenshot capture functionality"""
    print("\nTesting Capture Screenshots functionality...")
    
    with app.app_context():
        automation = DailyLotteryAutomation(app)
        
        try:
            success, count = automation.capture_fresh_screenshots()
            if success:
                print(f"✅ SUCCESS: Captured {count} fresh screenshots")
            else:
                print(f"❌ FAILED: Could not capture screenshots (count: {count})")
            return success
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False

if __name__ == "__main__":
    print("=== AUTOMATION FUNCTIONALITY TEST ===\n")
    
    # Test cleanup
    cleanup_success = test_cleanup()
    
    # Test capture if cleanup worked
    if cleanup_success:
        capture_success = test_capture()
    else:
        print("⚠️  Skipping capture test due to cleanup failure")
        capture_success = False
    
    print(f"\n=== RESULTS ===")
    print(f"Clear Old Screenshots: {'✅ PASS' if cleanup_success else '❌ FAIL'}")
    print(f"Capture Screenshots: {'✅ PASS' if capture_success else '❌ FAIL'}")
    
    if cleanup_success and capture_success:
        print("\n🎉 All automation functions are working correctly!")
        print("The issue is just with the admin authentication in the web interface.")
    else:
        print("\n⚠️  Some automation functions need attention.")