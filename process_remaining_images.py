#!/usr/bin/env python3
"""
Process remaining June 6, 2025 lottery images one by one
"""

import os
import sys
import logging
import time
from gemini_lottery_extractor import GeminiLotteryExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Process remaining lottery images individually"""
    logger.info("=== PROCESSING REMAINING JUNE 6 LOTTERY IMAGES ===")
    
    # Initialize Gemini extractor
    extractor = GeminiLotteryExtractor()
    
    # Remaining images to process
    remaining_images = [
        "attached_assets/20250606_171942_lotto_plus_1_results.png", 
        "attached_assets/20250606_171954_lotto_plus_2_results.png",
        "attached_assets/20250606_172007_powerball.png",
        "attached_assets/20250606_172018_powerball_plus.png",
        "attached_assets/20250606_172030_daily_lotto.png"
    ]
    
    for i, image_path in enumerate(remaining_images, 1):
        if os.path.exists(image_path):
            logger.info(f"Processing {i}/{len(remaining_images)}: {os.path.basename(image_path)}")
            try:
                success = extractor.process_single_image(image_path)
                if success:
                    logger.info(f"✅ Successfully processed {os.path.basename(image_path)}")
                else:
                    logger.error(f"❌ Failed to process {os.path.basename(image_path)}")
                
                # Add delay between API calls to avoid rate limits
                if i < len(remaining_images):
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error processing {image_path}: {e}")
        else:
            logger.warning(f"Image not found: {image_path}")
    
    logger.info("=== PROCESSING COMPLETE ===")

if __name__ == "__main__":
    main()