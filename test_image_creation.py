"""
Test script to verify image creation and saving functionality

This script creates a simple test image to verify that PIL is working correctly
and that images can be saved properly in the environment
"""

import os
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_image(filename="test_image.png", width=800, height=600):
    """Create a simple test image to verify PIL is working"""
    try:
        # Ensure directory exists
        os.makedirs('screenshots', exist_ok=True)
        filepath = os.path.join('screenshots', filename)
        
        # Create a new image with a white background
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Add some shapes and text to verify drawing capabilities
        # Draw a blue rectangle at the top
        draw.rectangle(
            ((0, 0), (width, 60)),
            fill=(0, 51, 102)
        )
        
        # Draw some text
        draw.text(
            (20, 20), 
            "Test Image", 
            fill=(255, 255, 255)
        )
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text(
            (20, 80), 
            f"Generated: {timestamp}", 
            fill=(0, 0, 0)
        )
        
        # Add a red circle
        draw.ellipse(
            [(width // 2 - 50, height // 2 - 50), 
             (width // 2 + 50, height // 2 + 50)], 
            fill=(255, 0, 0)
        )
        
        # Save the image
        image.save(filepath)
        logger.info(f"Test image created successfully: {filepath}")
        
        # Verify the image exists and has content
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            logger.info(f"Image size: {size} bytes")
            if size > 0:
                return True, filepath, size
            else:
                logger.error(f"Image file is empty: {filepath}")
                return False, filepath, 0
        else:
            logger.error(f"Image file was not created: {filepath}")
            return False, filepath, 0
            
    except Exception as e:
        logger.error(f"Error creating test image: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, 0

if __name__ == "__main__":
    success, filepath, size = create_test_image()
    
    if success:
        print(f"✅ Test image created successfully: {filepath} ({size} bytes)")
    else:
        print(f"❌ Failed to create test image: {filepath}")