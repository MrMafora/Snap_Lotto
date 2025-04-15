import logging
import os
import sys
import json
import base64
from pathlib import Path
import io
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample OCR results for testing
sample_ocr_results = {
    "lottery_type": "Lotto",
    "results": [
        {
            "draw_number": "2530",
            "draw_date": "2025-04-05",
            "numbers": [39, 42, 11, 7, 37, 34],
            "bonus_numbers": [44],
            "divisions": {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00"
                },
                "Division 2": {
                    "winners": "1",
                    "prize": "R99,273.10"
                },
                "Division 3": {
                    "winners": "38",
                    "prize": "R4,543.40"
                },
                "Division 4": {
                    "winners": "96",
                    "prize": "R2,248.00"
                },
                "Division 5": {
                    "winners": "2498",
                    "prize": "R145.10"
                },
                "Division 6": {
                    "winners": "3042",
                    "prize": "R103.60"
                },
                "Division 7": {
                    "winners": "46289",
                    "prize": "R50.00"
                },
                "Division 8": {
                    "winners": "33113",
                    "prize": "R20.00"
                }
            }
        }
    ]
}

# Create a test image file with simple division data
def create_test_image():
    """
    Create a sample test image with lottery information
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a blank image with a white background
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Attempt to use a default font
    try:
        font = ImageFont.truetype("Arial", 18)
    except IOError:
        font = ImageFont.load_default()
    
    # Add lottery data to the image
    draw.text((50, 50), "LOTTO RESULTS FOR DRAW ID 2530", fill='black', font=font)
    draw.text((50, 100), "LOTTO WINNING NUMBERS: 39, 42, 11, 7, 37, 34 + 44", fill='black', font=font)
    draw.text((50, 150), "DRAW DATE: 2025-04-05", fill='black', font=font)
    
    # Add divisions table
    y_pos = 200
    draw.text((50, y_pos), "DIVISIONS | WINNERS | PRIZE", fill='black', font=font)
    y_pos += 30
    
    divisions = [
        ("DIV 1", "0", "R0.00"),
        ("DIV 2", "1", "R99,273.10"),
        ("DIV 3", "38", "R4,543.40"),
        ("DIV 4", "96", "R2,248.00"),
        ("DIV 5", "2498", "R145.10"),
        ("DIV 6", "3042", "R103.60"),
        ("DIV 7", "46289", "R50.00"),
        ("DIV 8", "33113", "R20.00")
    ]
    
    for div, winners, prize in divisions:
        draw.text((50, y_pos), f"{div}    |    {winners}    |    {prize}", fill='black', font=font)
        y_pos += 30
    
    # Save the image to a temporary file
    img_path = "test_lottery_image.png"
    img.save(img_path)
    return img_path

# Test the division extraction from OCR results
def test_division_extraction():
    # Get divisions data from our OCR sample
    lottery_type = "Lotto"
    
    # Extract divisions data
    divisions_data = sample_ocr_results["results"][0]["divisions"]
    
    # Print the extracted data
    logger.info(f"OCR-extracted divisions data: {divisions_data}")
    
    # Check if we extracted the correct divisions
    expected_divisions = 8
    extracted_divisions = len(divisions_data)
    
    logger.info(f"Expected {expected_divisions} divisions, extracted {extracted_divisions}")
    
    # Check the first division
    if "Division 1" in divisions_data:
        div1 = divisions_data["Division 1"]
        logger.info(f"Division 1 data: {div1}")
        logger.info(f"Winners: {div1.get('winners')}, Prize: {div1.get('prize')}")
    else:
        logger.warning("Division 1 not found in extracted data")
    
    # Log all divisions
    for div_name, div_data in divisions_data.items():
        logger.info(f"{div_name}: Winners: {div_data.get('winners')}, Prize: {div_data.get('prize')}")
    
    # Verify we have commas in the prize amounts
    has_commas = False
    for _, div_data in divisions_data.items():
        prize = div_data.get('prize', '')
        if ',' in prize:
            has_commas = True
            logger.info(f"Found comma in prize: {prize}")
            break
    
    logger.info(f"Prize amounts have commas: {has_commas}")
    
    # Optionally create a test image file that could be used for OCR testing
    # img_path = create_test_image()
    # logger.info(f"Created test image at {img_path}")

if __name__ == "__main__":
    test_division_extraction()