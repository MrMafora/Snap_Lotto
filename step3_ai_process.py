"""
Step 3: AI Processing
Extract lottery data from screenshots using Anthropic Claude
"""
import os
import base64
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

def process_screenshots_with_ai():
    """Process screenshots with Claude AI to extract lottery data"""
    try:
        # Check for Anthropic API key
        api_key = os.environ.get('ANTHROPIC_API_SNAP_LOTTERY')
        if not api_key:
            logger.error("Anthropic API key not found in environment")
            return False, 0
        
        client = Anthropic(api_key=api_key)
        
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            logger.warning("Screenshots directory not found")
            return False, 0
        
        png_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
        if not png_files:
            logger.warning("No PNG files found to process")
            return False, 0
        
        processed_count = 0
        
        for image_file in png_files:
            try:
                image_path = os.path.join(screenshot_dir, image_file)
                logger.info(f"Processing image: {image_file}")
                
                # Read and encode image
                with open(image_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                # Send to Claude for analysis
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract lottery numbers, draw date, and lottery type from this South African lottery results image. Return data in JSON format."
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data
                                }
                            }
                        ]
                    }]
                )
                
                response = message.content[0].text
                logger.info(f"AI response for {image_file}: {response[:200]}...")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {image_file}: {e}")
        
        logger.info(f"AI processing completed: {processed_count}/{len(png_files)} images processed")
        return processed_count > 0, processed_count
        
    except Exception as e:
        logger.error(f"AI processing failed: {e}")
        return False, 0