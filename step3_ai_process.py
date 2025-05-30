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
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """CRITICAL: Perform DEEP ANALYSIS for 100% accurate lottery data extraction from this South African National Lottery results image.

REQUIREMENTS FOR ABSOLUTE ACCURACY:
1. EXAMINE EVERY NUMBER carefully - double-check each digit
2. VERIFY lottery type from page headers and navigation elements
3. CONFIRM draw number and date from official sources on page
4. EXTRACT ALL division data with exact winner counts and prize amounts
5. CROSS-REFERENCE all data points for consistency

EXPECTED LOTTERY TYPES:
- Lotto (6 main numbers + 1 bonus)
- Lotto Plus 1 (6 main numbers + 1 bonus) 
- Lotto Plus 2 (6 main numbers + 1 bonus)
- PowerBall (5 main numbers + 1 PowerBall)
- PowerBall Plus (5 main numbers + 1 PowerBall)
- Daily Lotto (5 numbers only)

REQUIRED JSON FORMAT:
{
  "lottery_type": "exact name from page",
  "draw_number": number,
  "draw_date": "YYYY-MM-DD",
  "winning_numbers": [array of main numbers],
  "bonus_ball": number or null,
  "powerball": number or null,
  "divisions": [
    {
      "division": "DIV 1",
      "winners": number,
      "prize_amount": "R amount"
    }
  ],
  "rollover_amount": "R amount or null",
  "total_pool_size": "R amount or null"
}

VERIFY EACH NUMBER TWICE before responding. Accuracy is critical."""
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
                
                # Validate the extracted data for accuracy
                try:
                    import json
                    extracted_data = json.loads(response)
                    
                    # Validation checks for data integrity
                    validation_errors = []
                    
                    # Check lottery type format
                    if 'lottery_type' not in extracted_data:
                        validation_errors.append("Missing lottery_type")
                    
                    # Check winning numbers format and range
                    if 'winning_numbers' in extracted_data:
                        numbers = extracted_data['winning_numbers']
                        if not isinstance(numbers, list):
                            validation_errors.append("Winning numbers must be a list")
                        else:
                            # Validate number ranges based on lottery type
                            lottery_type = extracted_data.get('lottery_type', '').lower()
                            if 'lotto' in lottery_type and len(numbers) != 6:
                                validation_errors.append(f"Lotto should have 6 numbers, found {len(numbers)}")
                            elif 'powerball' in lottery_type and len(numbers) != 5:
                                validation_errors.append(f"PowerBall should have 5 numbers, found {len(numbers)}")
                            elif 'daily' in lottery_type and len(numbers) != 5:
                                validation_errors.append(f"Daily Lotto should have 5 numbers, found {len(numbers)}")
                            
                            # Check number ranges (1-52 for most SA lotteries)
                            for num in numbers:
                                if not isinstance(num, int) or num < 1 or num > 52:
                                    validation_errors.append(f"Invalid number {num} - must be 1-52")
                    
                    # Check draw number
                    if 'draw_number' in extracted_data:
                        draw_num = extracted_data['draw_number']
                        if not isinstance(draw_num, int) or draw_num <= 0:
                            validation_errors.append("Draw number must be positive integer")
                    
                    # Log validation results
                    if validation_errors:
                        logger.warning(f"Validation errors for {image_file}: {validation_errors}")
                    else:
                        logger.info(f"✓ Data validation passed for {image_file}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response for {image_file}")
                except Exception as e:
                    logger.error(f"Validation error for {image_file}: {e}")
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {image_file}: {e}")
        
        logger.info(f"AI processing completed: {processed_count}/{len(png_files)} images processed")
        return processed_count > 0, processed_count
        
    except Exception as e:
        logger.error(f"AI processing failed: {e}")
        return False, 0