#!/usr/bin/env python3
"""
Process June 6, 2025 lottery images using Google Gemini 2.5 Pro
Extract comprehensive lottery data with prize divisions
"""

import os
import sys
import logging
from gemini_lottery_extractor import GeminiLotteryExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Process all June 6, 2025 lottery images"""
    logger.info("=== PROCESSING JUNE 6, 2025 LOTTERY IMAGES ===")
    
    # Initialize Gemini extractor
    extractor = GeminiLotteryExtractor()
    
    # June 6, 2025 lottery images
    june_6_images = [
        "attached_assets/20250606_171929_lotto.png",
        "attached_assets/20250606_171942_lotto_plus_1_results.png", 
        "attached_assets/20250606_171954_lotto_plus_2_results.png",
        "attached_assets/20250606_172007_powerball.png",
        "attached_assets/20250606_172018_powerball_plus.png",
        "attached_assets/20250606_172030_daily_lotto.png"
    ]
    
    success_count = 0
    
    for image_path in june_6_images:
        if os.path.exists(image_path):
            logger.info(f"Processing: {image_path}")
            try:
                success = extractor.process_single_image(image_path)
                if success:
                    success_count += 1
                    logger.info(f"✅ Successfully processed {image_path}")
                else:
                    logger.error(f"❌ Failed to process {image_path}")
            except Exception as e:
                logger.error(f"Error processing {image_path}: {e}")
        else:
            logger.warning(f"Image not found: {image_path}")
    
    logger.info(f"=== PROCESSING COMPLETE ===")
    logger.info(f"Successfully processed {success_count}/{len(june_6_images)} images")
    
    return success_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)