"""
Test single image processing with Claude Opus 4
Direct test bypassing the automation workflow
"""
import os
from automated_data_extractor import LotteryDataExtractor
from main import app

def test_authentic_image_processing():
    """Test processing authentic lottery images directly"""
    
    # Re-add test images if they were removed
    os.makedirs('screenshots', exist_ok=True)
    
    # Copy authentic images back if needed
    test_files = [
        ('attached_assets/20250528_220633_daily-lotto.png', 'screenshots/daily_lotto_test.png'),
        ('attached_assets/20250528_184552_lotto-plus-1-history.png', 'screenshots/lotto_plus_1_test.png')
    ]
    
    for src, dst in test_files:
        if os.path.exists(src) and not os.path.exists(dst):
            import shutil
            shutil.copy2(src, dst)
            print(f"Added test image: {dst}")
    
    # Test processing with app context
    with app.app_context():
        extractor = LotteryDataExtractor()
        
        # Check available test images
        screenshot_files = [f for f in os.listdir('screenshots') if f.endswith('.png')]
        print(f"Found {len(screenshot_files)} test images")
        
        if not screenshot_files:
            print("No test images available")
            return False
        
        successful_extractions = 0
        
        for image_file in screenshot_files:
            image_path = os.path.join('screenshots', image_file)
            print(f"\nProcessing: {image_file}")
            
            try:
                # Process single image safely
                success = extractor.process_single_image_safe(image_path)
                if success:
                    successful_extractions += 1
                    print(f"Successfully processed {image_file}")
                else:
                    print(f"Failed to process {image_file}")
                    
            except Exception as e:
                print(f"Error with {image_file}: {str(e)[:100]}")
        
        print(f"\nResults: {successful_extractions}/{len(screenshot_files)} images processed successfully")
        return successful_extractions > 0

if __name__ == "__main__":
    test_authentic_image_processing()