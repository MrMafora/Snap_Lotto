#!/usr/bin/env python3
"""
Process a single lottery image and update the database
"""
import os
import sys
from automated_data_extractor import LotteryDataExtractor

def main():
    """Process the specific Lotto Plus 2 image"""
    
    # Initialize the extractor
    extractor = LotteryDataExtractor()
    
    # Process the specific image
    image_path = "attached_assets/20250530_030508_lotto_plus_2_results.png"
    
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return
    
    print(f"Processing image: {image_path}")
    
    try:
        # Extract data using AI
        result = extractor.process_single_image_safe(image_path)
        
        if result:
            print("✓ Successfully processed and saved to database")
            print(f"Data extracted: {result}")
        else:
            print("✗ Failed to process image")
            
    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()