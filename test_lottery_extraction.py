#!/usr/bin/env python3
"""
Quick test script to extract lottery data from sample images
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path
sys.path.append('.')

from automated_data_extractor import LotteryDataExtractor
from models import db, LotteryResult
from main import app

def test_lottery_extraction():
    """Test lottery data extraction with sample images"""
    
    with app.app_context():
        extractor = LotteryDataExtractor()
        
        # Test with the Lotto Plus 2 sample image
        sample_image = './attached_assets/20250530_030508_lotto_plus_2_results.png'
        
        if not os.path.exists(sample_image):
            print("Sample lottery image not found")
            return
            
        print(f"Processing lottery image: {sample_image}")
        
        try:
            # Extract lottery data
            result = extractor.extract_lottery_data(sample_image)
            
            if result and 'lottery_type' in result:
                print(f"Successfully extracted data for: {result['lottery_type']}")
                print(f"Draw number: {result.get('draw_number', 'N/A')}")
                print(f"Main numbers: {result.get('main_numbers', 'N/A')}")
                
                # Save to database
                saved = extractor.save_to_database(result)
                if saved:
                    print("✅ Data saved to database successfully")
                    
                    # Verify it's in the database
                    count = LotteryResult.query.count()
                    print(f"Total lottery records in database: {count}")
                else:
                    print("❌ Failed to save to database")
            else:
                print("❌ Failed to extract lottery data")
                print(f"Result: {result}")
                
        except Exception as e:
            print(f"Error during extraction: {e}")

if __name__ == "__main__":
    test_lottery_extraction()