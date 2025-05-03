"""
Run extraction just for Daily Lotto
"""
import logging
import sys
from enhanced_extraction import process_lottery_type

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger("daily_lotto_extraction")

if __name__ == "__main__":
    logger.info("Running extraction for Daily Lotto")
    result = process_lottery_type("Daily Lotto")
    logger.info(f"Extraction result: {result}")