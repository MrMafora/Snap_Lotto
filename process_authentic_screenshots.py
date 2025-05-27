#!/usr/bin/env python3
"""
Process authentic South African lottery screenshots and populate database
Uses Anthropic AI to extract real lottery data from official sources
"""

import os
import sys
from automated_data_extractor import LotteryDataExtractor
from main import app

def process_authentic_lottery_screenshots():
    """Process the 12 authentic lottery screenshots from screenshots folder"""
    
    with app.app_context():
        print('🚀 Processing your 12 authentic South African lottery screenshots...')
        print('Using Anthropic AI to extract real lottery data from official sources\n')
        
        extractor = LotteryDataExtractor()
        
        # Get the actual screenshot paths from the screenshots folder
        screenshot_dir = 'screenshots'
        if not os.path.exists(screenshot_dir):
            print('❌ Screenshots folder not found')
            return
        
        image_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
        print(f'Found {len(image_files)} authentic lottery screenshots to process\n')
        
        results = []
        for i, img_file in enumerate(image_files, 1):
            img_path = os.path.join(screenshot_dir, img_file)
            print(f'📸 Processing authentic screenshot {i}/{len(image_files)}: {img_file}...')
            
            try:
                result = extractor.extract_lottery_data(img_path)
                if result:
                    # Save to database
                    success = extractor.save_to_database(result)
                    if success:
                        print(f'✅ Successfully extracted and saved: {result.get("lottery_type", "Unknown")}')
                        if result.get('main_numbers'):
                            print(f'   Numbers: {result.get("main_numbers", [])}')
                            if result.get('bonus_number'):
                                print(f'   Bonus: {result.get("bonus_number")}')
                        results.append(result)
                    else:
                        print(f'⚠️  Extracted data but failed to save to database')
                else:
                    print(f'❌ Could not extract lottery data from {img_file}')
            except Exception as e:
                print(f'❌ Error processing {img_file}: {str(e)[:100]}')
            
            print()  # Add spacing between results
        
        print(f'🎯 Successfully processed and saved {len(results)} authentic lottery results!')
        print('Your database now contains real South African lottery data!')
        print('\nYou can now:')
        print('- View results at /results')
        print('- Check analytics at /visualizations') 
        print('- Test ticket scanner with real data')

if __name__ == '__main__':
    process_authentic_lottery_screenshots()