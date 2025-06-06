#!/usr/bin/env python3
"""
Test single lottery extraction with Google Gemini 2.5 Pro
"""

import os
from gemini_lottery_extractor import GeminiLotteryExtractor
from models import db, LotteryResult
from main import app

def main():
    """Test extraction from one image"""
    
    with app.app_context():
        extractor = GeminiLotteryExtractor()
        
        # Test with LOTTO image first
        image_path = 'attached_assets/20250606_171929_lotto.png'
        
        if os.path.exists(image_path):
            try:
                print(f'Testing extraction from {os.path.basename(image_path)}...')
                extracted_data = extractor.extract_lottery_data(image_path)
                
                if extracted_data and 'lottery_type' in extracted_data:
                    print(f"Extracted: {extracted_data['lottery_type']} Draw {extracted_data['draw_number']}")
                    print(f"Numbers: {extracted_data['main_numbers']} + {extracted_data.get('bonus_numbers', [])}")
                    
                    # Save to database
                    success = extractor.save_to_database(extracted_data)
                    if success:
                        print("Successfully saved to database")
                        return True
                    else:
                        print("Failed to save to database")
                        return False
                else:
                    print("No valid data extracted")
                    return False
                    
            except Exception as e:
                print(f"Error: {e}")
                return False
        else:
            print(f"File not found: {image_path}")
            return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)