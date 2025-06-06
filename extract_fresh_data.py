#!/usr/bin/env python3
"""
Extract fresh lottery data using Google Gemini 2.5 Pro
"""

import os
import sys
from datetime import datetime
from gemini_lottery_extractor import GeminiLotteryExtractor
from models import db, LotteryResult
from main import app

def main():
    """Extract lottery data from provided images"""
    
    with app.app_context():
        extractor = GeminiLotteryExtractor()
        
        # Process the latest lottery images
        image_files = [
            'attached_assets/20250606_171929_lotto.png',
            'attached_assets/20250606_171942_lotto_plus_1_results.png', 
            'attached_assets/20250606_171954_lotto_plus_2_results.png',
            'attached_assets/20250606_172007_powerball.png',
            'attached_assets/20250606_172018_powerball_plus.png',
            'attached_assets/20250606_172030_daily_lotto.png'
        ]
        
        successful_extractions = 0
        
        for image_path in image_files:
            if os.path.exists(image_path):
                try:
                    print(f'Processing {os.path.basename(image_path)}...')
                    extracted_data = extractor.extract_lottery_data(image_path)
                    
                    if extracted_data and 'lottery_type' in extracted_data:
                        # Check if record already exists
                        existing = LotteryResult.query.filter_by(
                            lottery_type=extracted_data['lottery_type'],
                            draw_number=extracted_data['draw_number']
                        ).first()
                        
                        if existing:
                            print(f"Skipping {extracted_data['lottery_type']} Draw {extracted_data['draw_number']} - already exists")
                            continue
                        
                        success = extractor.save_to_database(extracted_data)
                        if success:
                            successful_extractions += 1
                            print(f"Successfully extracted {extracted_data['lottery_type']} Draw {extracted_data['draw_number']}")
                        else:
                            print(f"Failed to save data for {image_path}")
                    else:
                        print(f"No valid data extracted from {image_path}")
                        
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
            else:
                print(f"File not found: {image_path}")
        
        print(f"\nCompleted: {successful_extractions}/{len(image_files)} successful extractions")
        
        # Show recent results
        recent = LotteryResult.query.order_by(LotteryResult.created_at.desc()).limit(6).all()
        if recent:
            print("\nRecent lottery results:")
            for result in recent:
                print(f"- {result.lottery_type} Draw {result.draw_number}: {result.numbers}")

if __name__ == "__main__":
    main()