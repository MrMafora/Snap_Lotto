from main import app
import screenshot_manager
from models import ScheduleConfig, Screenshot

def test_single_update():
    """Test the _update_single_screenshot_record function"""
    with app.app_context():
        # Get one config for testing
        config = ScheduleConfig.query.first()
        print(f"Testing with config: {config.id}, {config.lottery_type}")
        
        # Get current screenshot state
        screenshot = Screenshot.query.filter_by(lottery_type=config.lottery_type).first()
        if screenshot:
            print(f"Current screenshot timestamp: {screenshot.timestamp}")
        else:
            print("No screenshot record exists for this config")
        
        # Test update function
        success = screenshot_manager._update_single_screenshot_record(config.url, config.lottery_type, app)
        print(f"Update result: {'Success' if success else 'Failed'}")
        
        # Check updated state
        updated = Screenshot.query.filter_by(lottery_type=config.lottery_type).first()
        if updated:
            print(f"Updated screenshot timestamp: {updated.timestamp}")
        else:
            print("Still no screenshot record")
        
        return success

def test_retake_logic():
    """Test the retry logic in retake_all_screenshots"""
    with app.app_context():
        # Create a list of configs with one valid and one invalid URL
        configs = ScheduleConfig.query.filter_by(active=True).limit(2).all()
        if len(configs) < 2:
            print("Need at least 2 configs for this test")
            return False
        
        # Use a valid URL for the first config
        configs[0].url = "https://www.google.com"
        
        # Use an invalid URL for the second config to force failure
        configs[1].url = "https://invalid.example.com/nonexistent"
        
        print(f"Testing with: {configs[0].lottery_type} (valid) and {configs[1].lottery_type} (invalid)")
        
        # First attempt - should succeed for first, fail for second
        for config in configs:
            success = screenshot_manager._take_screenshot_worker(config.url, config.lottery_type)
            print(f"{config.lottery_type}: {'Success' if success else 'Failed as expected'}")

if __name__ == "__main__":
    print("\n=== Testing _update_single_screenshot_record fallback ===")
    test_single_update()
    
    print("\n=== Testing partial failure handling ===") 
    test_retake_logic()