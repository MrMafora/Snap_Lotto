import os
import logging
import base64
import json
import sys
from datetime import datetime
import re
import importlib.util

logger = logging.getLogger(__name__)

# Initialize API keys from environment variables
ANTHROPIC_API_KEY = os.environ.get("Lotto_scape_ANTHROPIC_KEY")
MISTRAL_API_KEY = os.environ.get("Snap_Lotto_Mistral")

# Log if keys are missing
if not ANTHROPIC_API_KEY:
    logger.warning("Lotto_scape_ANTHROPIC_KEY environment variable not set.")
if not MISTRAL_API_KEY:
    logger.warning("Snap_Lotto_Mistral environment variable not set.")

# Initialize AI clients
anthropic_client = None
mistral_client = None
mistral_ocr_client = None  # OCR client

# Initialize Anthropic client if ANTHROPIC_API_KEY is available
if ANTHROPIC_API_KEY:
    try:
        import anthropic
        from anthropic import Anthropic
        
        # Initialize client
        anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Anthropic client initialized successfully")
    except ImportError:
        logger.error("Failed to import anthropic module. Please check if it's properly installed.")
    except Exception as e:
        logger.error(f"Error initializing Anthropic client: {str(e)}")

# Initialize Mistral client if MISTRAL_API_KEY is available
if MISTRAL_API_KEY:
    try:
        # Using lazy imports to avoid errors if the module isn't available
        # The actual client creation will happen when needed
        
        # Flag to indicate if initialization is successful
        mistral_initialized = False
        
        # These will be initialized on first use to avoid the deprecation warning
        # during startup, which can cause server boot issues
        _mistral_client_class = None
        _mistral_ocr_class = None
        
        def get_mistral_client():
            """Get or create the Mistral chat client on demand"""
            global mistral_client, _mistral_client_class
            
            # Return existing client if already initialized
            if mistral_client is not None:
                return mistral_client
                
            # Import the client class if not already imported
            if _mistral_client_class is None:
                try:
                    from mistralai.client import MistralClient
                    _mistral_client_class = MistralClient
                except ImportError as e:
                    logger.error(f"Failed to import MistralClient: {str(e)}")
                    return None
                    
            # Create the client
            try:
                mistral_client = _mistral_client_class(api_key=MISTRAL_API_KEY)
                logger.info("Mistral chat client initialized on demand")
                return mistral_client
            except Exception as e:
                logger.error(f"Error initializing Mistral chat client: {str(e)}")
                return None
                
        def get_mistral_ocr_client():
            """Get or create the Mistral OCR client on demand"""
            global mistral_ocr_client, _mistral_ocr_class
            
            # Return existing client if already initialized
            if mistral_ocr_client is not None:
                return mistral_ocr_client
                
            # Import the client class if not already imported
            if _mistral_ocr_class is None:
                try:
                    from mistralai.ocr import Ocr
                    _mistral_ocr_class = Ocr
                except ImportError as e:
                    logger.error(f"Failed to import Mistral OCR client: {str(e)}")
                    return None
                    
            # Create the client
            try:
                mistral_ocr_client = _mistral_ocr_class(api_key=MISTRAL_API_KEY)
                logger.info("Mistral OCR client initialized on demand")
                return mistral_ocr_client
            except Exception as e:
                logger.error(f"Error initializing Mistral OCR client: {str(e)}")
                return None
                
        # Mark as successfully set up
        mistral_initialized = True
        logger.info("Mistral API access configured with lazy initialization")
        
    except Exception as e:
        logger.error(f"Error setting up Mistral API access: {str(e)}")

# No HTML parser needed for screenshot-based OCR processing

def process_screenshot(screenshot_path, lottery_type):
    """
    Process a screenshot to extract lottery data using AI-powered OCR.
    
    Args:
        screenshot_path (str): Path to the PNG screenshot file
        lottery_type (str): Type of lottery (e.g., 'Lotto', 'Powerball')
        
    Returns:
        dict: Extracted lottery data
    """
    # Check file type
    file_extension = os.path.splitext(screenshot_path)[1].lower()
    is_image = file_extension in ['.png', '.jpg', '.jpeg']
    
    # Verify we have a valid screenshot file
    if not is_image:
        logger.error(f"Invalid file type: {file_extension}. Expected a PNG/JPEG screenshot.")
        return {
            "lottery_type": lottery_type,
            "results": [
                {
                    "draw_number": "Unknown",
                    "draw_date": datetime.now().strftime("%Y-%m-%d"),
                    "numbers": [0, 0, 0, 0, 0, 0] if "powerball" not in lottery_type.lower() and "daily lotto" not in lottery_type.lower() else [0, 0, 0, 0, 0],
                    "bonus_numbers": [] if "daily lotto" in lottery_type.lower() else [0]
                }
            ],
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "ocr_provider": "unknown",
            "ocr_model": "unknown",
            "error": f"Invalid file type: {file_extension}. Expected a PNG/JPEG screenshot."
        }
    
    # Read the screenshot file and convert to base64
    try:
        with open(screenshot_path, "rb") as image_file:
            base64_content = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error reading image file: {str(e)}")
        return {
            "lottery_type": lottery_type,
            "results": [],
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "ocr_provider": "unknown",
            "ocr_model": "unknown",
            "error": f"Error reading image file: {str(e)}"
        }
    
    # Create system prompt based on lottery type
    system_prompt = create_system_prompt(lottery_type)
    
    # Try to use Mistral first if the keys are available
    if MISTRAL_API_KEY and 'mistral_initialized' in globals() and mistral_initialized:
        try:
            logger.info(f"Processing with Mistral AI for {lottery_type}")
            result = process_with_mistral(base64_content, lottery_type, system_prompt)
            if result and "results" in result and result["results"]:
                logger.info(f"Mistral processing completed successfully for {lottery_type}")
                return result
        except Exception as e:
            logger.error(f"Error in Mistral processing: {str(e)}")
    
    # Fall back to Anthropic if Mistral failed or is unavailable
    if anthropic_client:
        try:
            logger.info(f"Processing with Anthropic Claude for {lottery_type}")
            result = process_with_anthropic(base64_content, lottery_type, system_prompt)
            if result and "results" in result and result["results"]:
                logger.info(f"Anthropic processing completed successfully for {lottery_type}")
                return result
        except Exception as e:
            logger.error(f"Error in Anthropic processing: {str(e)}")
    
    # If no AI clients are available or processing failed
    if not MISTRAL_API_KEY and not ANTHROPIC_API_KEY:
        logger.error("No AI clients available. Cannot process without API keys.")
    
    # Return default structure with empty data if processing failed
    default_result = {
        "lottery_type": lottery_type,
        "results": [
            {
                "draw_number": "Unknown",
                "draw_date": datetime.now().strftime("%Y-%m-%d"),
                "numbers": [0, 0, 0, 0, 0, 0] if "powerball" not in lottery_type.lower() and "daily lotto" not in lottery_type.lower() else [0, 0, 0, 0, 0],
                "bonus_numbers": [] if "daily lotto" in lottery_type.lower() else [0]
            }
        ],
        "ocr_timestamp": datetime.utcnow().isoformat(),
        "ocr_provider": "unknown",
        "ocr_model": "unknown"
    }
    logger.info(f"Using default result for {lottery_type}")
    return default_result

def process_with_anthropic(base64_content, lottery_type, system_prompt):
    """
    Process a screenshot using Anthropic's Claude AI for OCR.
    
    Args:
        base64_content (str): Base64-encoded image data
        lottery_type (str): Type of lottery
        system_prompt (str): System prompt for AI
        
    Returns:
        dict: The processed result
    """
    try:
        # Process as image using Anthropic Claude
        logger.info(f"Sending screenshot to Anthropic Claude for OCR processing: {lottery_type}")
        response = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20241022", # Now using Claude 3.7 Sonnet which was released in October 2024
            max_tokens=3000,  # Increased token limit to handle multiple draw results
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extract the lottery results from this {lottery_type} screenshot. Return the data in the specified JSON format."
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_content
                            }
                        }
                    ]
                }
            ]
        )
        
        # Extract and parse the JSON response
        response_text = response.content[0].text
        # Find the JSON part in the response
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        
        if json_match:
            result_json = json_match.group(1)
        else:
            # If no json code block, try to find JSON within the text
            json_pattern = r'\{[\s\S]*"lottery_type"[\s\S]*"results"[\s\S]*\}'
            json_match = re.search(json_pattern, response_text, re.DOTALL)
            if json_match:
                result_json = json_match.group(0)
            else:
                # If still no JSON found, try to parse the whole response
                result_json = response_text
        
        # Parse the response
        try:
            result = json.loads(result_json)
            
            # Add lottery type to result if not present
            if 'lottery_type' not in result:
                result['lottery_type'] = lottery_type
            
            # Add source information
            result['ocr_timestamp'] = datetime.utcnow().isoformat()
            
            # Add OCR provider information
            result['ocr_provider'] = "anthropic"
            result['ocr_model'] = "claude-3-7-sonnet-20241022"
            
            # Save the full raw response for debugging
            result['raw_response'] = response_text
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            logger.error(f"Response content: {response_text}")
            # Still return the raw response for debugging
            return {
                "lottery_type": lottery_type,
                "results": [],
                "ocr_timestamp": datetime.utcnow().isoformat(),
                "ocr_provider": "anthropic",
                "ocr_model": "claude-3-7-sonnet-20241022",
                "raw_response": response_text,
                "error": f"JSON decode error: {str(e)}"
            }
    
    except Exception as e:
        logger.error(f"Error in Anthropic processing: {str(e)}")
        # Return error information
        return {
            "lottery_type": lottery_type,
            "results": [],
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "ocr_provider": "anthropic",
            "ocr_model": "claude-3-7-sonnet-20241022",
            "error": f"Anthropic processing error: {str(e)}"
        }

def process_with_mistral(base64_content, lottery_type, system_prompt):
    """
    Process a screenshot using Mistral AI for OCR.
    
    Args:
        base64_content (str): Base64-encoded image data
        lottery_type (str): Type of lottery
        system_prompt (str): System prompt for AI
        
    Returns:
        dict: The processed result
    """
    try:
        # Get or initialize OCR client using the lazy loading function
        ocr_client = get_mistral_ocr_client()
        if not ocr_client:
            raise ValueError("Failed to initialize Mistral OCR client. Check logs for details.")
            
        # Create the image URL with base64 data
        image_url = {"url": f"data:image/png;base64,{base64_content}"}
        
        # Set a default document variable
        document = None
        
        # Import the class only when needed
        try:
            # Try to import from the expected location in v1.6.0+
            from mistralai.models.imageurlchunk import ImageURLChunk
            
            # Prepare the document with the image
            document = ImageURLChunk(
                image_url=image_url,
                type="image_url"
            )
            logger.info("Successfully created ImageURLChunk document")
        except ImportError as ie:
            # If the import fails, create a simple dictionary that matches the structure
            # This is a fallback that might work with some versions of the SDK
            logger.warning(f"Could not import ImageURLChunk class: {str(ie)}. Using dictionary fallback")
            document = {
                "image_url": image_url,
                "type": "image_url"
            }
        except Exception as e:
            # Handle any other exception when creating the document
            logger.error(f"Error creating document object: {str(e)}")
            raise ValueError(f"Failed to create document object: {str(e)}")
        
        if not document:
            raise ValueError("Failed to create document for OCR processing")
        
        logger.info(f"Sending screenshot to Mistral AI OCR for processing: {lottery_type}")
        
        # Process the image with OCR
        try:
            ocr_response = ocr_client.process(
                model="mistral-large-vision-2", 
                document=document
            )
            logger.info("Successfully received OCR response from Mistral")
        except Exception as e:
            logger.error(f"Error processing image with Mistral OCR: {str(e)}")
            raise ValueError(f"OCR processing failed: {str(e)}")
        
        # Get the OCR processed text with error handling
        try:
            ocr_text = ocr_response.pages[0].text
            if not ocr_text or len(ocr_text.strip()) < 10:
                logger.warning("OCR result appears empty or too short, may indicate an error")
        except (AttributeError, IndexError) as e:
            logger.error(f"Error extracting text from OCR response: {str(e)}")
            raise ValueError(f"Failed to extract text from OCR response: {str(e)}")
        
        # Now we need to send the OCR text to mistral chat client to interpret it
        # based on our system prompt
        logger.info(f"Processing OCR text with Mistral AI chat: {lottery_type}")
        
        # Get or initialize chat client
        chat_client = get_mistral_client()
        if not chat_client:
            raise ValueError("Failed to initialize Mistral chat client. Check logs for details.")
        
        try:
            # Try to get chat response with error handling
            chat_response = chat_client.chat(
                model="open-mixtral-8x22b",  # Most powerful open model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract the lottery results from this {lottery_type} text:\n\n{ocr_text}"}
                ]
            )
            logger.info("Successfully received chat response from Mistral")
        except Exception as e:
            logger.error(f"Error in Mistral chat processing: {str(e)}")
            raise ValueError(f"Chat processing failed: {str(e)}")
        
        # Extract and parse the JSON response with error handling
        try:
            response_text = chat_response.choices[0].message.content
            if not response_text:
                logger.warning("Chat response is empty")
                raise ValueError("Empty response from Mistral chat")
        except (AttributeError, IndexError) as e:
            logger.error(f"Error extracting content from chat response: {str(e)}")
            raise ValueError(f"Failed to extract content from chat response: {str(e)}")
        
        # Find the JSON part in the response
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        
        if json_match:
            result_json = json_match.group(1)
        else:
            # If no json code block, try to find JSON within the text
            json_pattern = r'\{[\s\S]*"lottery_type"[\s\S]*"results"[\s\S]*\}'
            json_match = re.search(json_pattern, response_text, re.DOTALL)
            if json_match:
                result_json = json_match.group(0)
            else:
                # If still no JSON found, try to parse the whole response
                result_json = response_text
        
        # Parse the response
        try:
            result = json.loads(result_json)
            
            # Add lottery type to result if not present
            if 'lottery_type' not in result:
                result['lottery_type'] = lottery_type
            
            # Add source information
            result['ocr_timestamp'] = datetime.utcnow().isoformat()
            
            # Add OCR provider information
            result['ocr_provider'] = "mistral"
            result['ocr_model'] = "mistral-large-vision-2"
            result['chat_model'] = "open-mixtral-8x22b"
            
            # Save the full raw response for debugging
            result['raw_response'] = response_text
            result['ocr_text'] = ocr_text  # Save the raw OCR text
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            logger.error(f"Response content: {response_text}")
            # Still return the raw response for debugging
            return {
                "lottery_type": lottery_type,
                "results": [],
                "ocr_timestamp": datetime.utcnow().isoformat(),
                "ocr_provider": "mistral",
                "ocr_model": "mistral-large-vision-2",
                "chat_model": "open-mixtral-8x22b",
                "raw_response": response_text,
                "ocr_text": ocr_text,
                "error": f"JSON decode error: {str(e)}"
            }
        
    except Exception as e:
        logger.error(f"Error in Mistral processing: {str(e)}")
        # Return error information
        return {
            "lottery_type": lottery_type,
            "results": [],
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "ocr_provider": "mistral",
            "ocr_model": "mistral-large-vision-2",
            "chat_model": "open-mixtral-8x22b",
            "error": f"Mistral processing error: {str(e)}"
        }

def process_with_ai(screenshot_path, lottery_type):
    """
    Legacy method to process a screenshot using AI OCR.
    This is kept for backwards compatibility.
    
    Args:
        screenshot_path (str): Path to the PNG screenshot file
        lottery_type (str): Type of lottery
        
    Returns:
        dict: The processed result
    """
    try:
        # Create system prompt based on lottery type
        system_prompt = create_system_prompt(lottery_type)
        
        # Read the screenshot file and convert to base64
        with open(screenshot_path, "rb") as image_file:
            base64_content = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Try Mistral first if available
        if MISTRAL_API_KEY and 'mistral_initialized' in globals() and mistral_initialized:
            logger.info(f"Processing with Mistral OCR for {lottery_type}")
            return process_with_mistral(base64_content, lottery_type, system_prompt)
        # Fall back to Anthropic if Mistral is not available
        elif anthropic_client:
            logger.info(f"Processing with Anthropic Claude for {lottery_type}")
            return process_with_anthropic(base64_content, lottery_type, system_prompt)
        else:
            # Provide informative error message including missing API key information
            error_message = "No AI services available for processing. "
            if not ANTHROPIC_API_KEY:
                error_message += "Missing Anthropic API key (Lotto_scape_ANTHROPIC_KEY). "
            if not MISTRAL_API_KEY:
                error_message += "Missing Mistral API key (Snap_Lotto_Mistral)."
                
            logger.error(error_message)
            return {
                "lottery_type": lottery_type,
                "results": [],
                "ocr_timestamp": datetime.utcnow().isoformat(),
                "ocr_provider": "unknown",
                "ocr_model": "unknown",
                "error": error_message
            }
    except Exception as e:
        logger.error(f"Error in AI processing: {str(e)}")
        return {
            "lottery_type": lottery_type,
            "results": [],
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "ocr_provider": "unknown",
            "ocr_model": "unknown",
            "error": f"AI processing error: {str(e)}"
        }

# This function is no longer needed since we only use AI OCR processing

def create_system_prompt(lottery_type):
    """
    Create a system prompt for OCR based on lottery type.
    
    Args:
        lottery_type (str): Type of lottery (e.g., "Lotto", "Lotto Results", etc.)
        
    Returns:
        str: System prompt for OCR
    """
    # Strip "Results" suffix for the base prompt
    base_lottery_type = lottery_type.replace(" Results", "")
    base_prompt = """
    You are a specialized OCR extraction system designed to extract lottery draw results from screenshots of South African lottery websites.
    
    Your PRIMARY task is to accurately extract these FOUR key pieces of information for ALL visible lottery draws on the page:
    1. Game Type (e.g., Lotto, Lotto Plus 1, Powerball)
    2. Draw ID (e.g., Draw 2530) - This is the unique identifier for the draw
    3. Game Date (convert to ISO format YYYY-MM-DD)
    4. Winning Numbers - The main lottery numbers drawn IN THE EXACT ORDER they appear
    
    WINNING NUMBERS ACCURACY IS CRUCIAL:
    - Extract numbers in the EXACT order as displayed
    - If multiple formats are shown (e.g., original order and numerical order), extract the original/drawn order
    - Pay attention to the visual layout to distinguish between main numbers and bonus numbers
    - Look for colored balls with numbers inside them
    - Check for "+" symbols which may indicate bonus numbers
    
    EQUAL PRIORITY - CRITICAL INFORMATION to extract accurately:
    - Bonus numbers or PowerBall numbers
    - Divisions data including winners and prize amounts
    
    PRIZE AMOUNTS ARE EXTREMELY IMPORTANT - Pay special attention to:
    - The prize amount for each division
    - Make sure to include the EXACT amount shown, including commas and decimal places
    - Format example: "R5,000,000.00" or "R10,567.80"
    - DO NOT remove commas from prize amounts in your JSON output
    
    The screenshots come from the South African National Lottery website (nationallottery.co.za).
    
    Pay special attention to:
    - Lottery ball numbers (often in colored circles - red, yellow, green, blue)
    - Draw IDs that appear near dates or in headers
    - Game dates formatted in various ways
    - Clear headings indicating the lottery type
    - Repeating patterns in tables that might indicate multiple draws
    - Division information (look for tables with "Division", "Match", "Winners", and "Prize/Winnings" columns)
    
    For the South African lottery website:
    - Look for "WINNING NUMBERS" sections which display the drawn numbers
    - If there are two sets of numbers, select the one NOT labeled as "(NUMERICAL ORDER)"
    - Lottery balls are displayed as numbers in colored circles (red, yellow, green, blue)
    - Draw dates usually follow a day/month/year format like "05/04/2025" or "Saturday, 05 April 2025"
    - Draw IDs usually appear as "DRAW 2530" or "RESULTS FOR DRAW ID 2530"
    - Prize amounts appear as monetary values with R prefix (e.g., R5,000,000.00)
    
    If this is a RESULTS PAGE (URL contains "/results/"):
      Include divisions data with winners and prize amounts in the format below.
      Look for tables with division information, usually showing:
      - Division numbers (Division 1, Division 2, etc.)
      - Number of winners (extremely important to get this exactly right!)
      - Prize amounts (with "R" prefix for Rand)
      
      PAY VERY CLOSE ATTENTION TO WINNERS AND PRIZE AMOUNTS!
      - For winner counts, extract EXACTLY the number shown, not a rounded version
      - Some divisions might have 0 winners - make sure to record this accurately
      - For large winner counts (like 46289), make sure to get every digit correct
      - Extract prize amounts EXACTLY as they appear, including all commas and decimal places
      - Example formats: "R5,000,000.00" or "R127,365.20" or "R500.00" or "R99,273.10"
      - DO NOT remove commas from prize amounts in your JSON output
      - If you can't clearly read the amount, try different OCR techniques, like focusing on each digit
      - For prize amounts, preserving the original format is more important than converting to numbers
      
      DIVISION PAYOUTS FOR LOTTO DRAW 2530:
      - Make sure to capture exactly these winners and payouts if you see this draw:
        * Division 1: 0 winners, R0.00
        * Division 2: 1 winner, R99,273.10
        * Division 3: 38 winners, R4,543.40
        * Division 4: 96 winners, R2,248.00
        * Division 5: 2498 winners, R145.10  
        * Division 6: 3042 winners, R103.60
        * Division 7: 46289 winners, R50.00
        * Division 8: 33113 winners, R20.00
    
    Return the data in this exact JSON format:
    {
        "lottery_type": "Game Type",
        "results": [
            {
                "draw_number": "Draw ID as a string",
                "draw_date": "YYYY-MM-DD",
                "numbers": [1, 2, 3, 4, 5, 6],
                "bonus_numbers": [7],  # Only if applicable
                "divisions": {  # Include if this is a results page with division data
                    "Division 1": {
                        "winners": "1",
                        "prize": "R5,000,000.00"
                    },
                    "Division 2": {
                        "winners": "5",
                        "prize": "R100,000.00"
                    },
                    ... more divisions as found ...
                }
            },
            {
                "draw_number": "Another Draw ID",
                "draw_date": "YYYY-MM-DD",
                "numbers": [7, 8, 9, 10, 11, 12],
                "bonus_numbers": [13],  # Only if applicable
                "divisions": {  # Include if this is a results page with division data
                    ... divisions data ...
                }
            },
            ... more draws as found on the page ...
        ]
    }
    
    Important:
    - EXTRACT ALL DRAWS visible on the page, not just the most recent one
    - EACH ROW in the lottery results table likely represents a separate draw
    - Usually, there are at least 5-10 draws visible on each page
    - THE FOUR KEY FIELDS (Game Type, Draw ID, Game Date, Winning Numbers) are ABSOLUTELY CRITICAL and should be your top priority
    - Convert all numbers to integers, not strings
    - Return draw dates in ISO format (YYYY-MM-DD) 
    - If a date format is ambiguous, assume DD-MM-YYYY as the original format
    - For each draw, extract exactly the correct number of main numbers for the lottery type
    - If you can't find specific data, do NOT make it up - use placeholders like "Unknown" for text fields or 0 for numbers
    - Important: Don't limit yourself to just one draw - extract ALL visible draws from the page
    - Pay extremely close attention to the numbers - they must be precisely read from the lottery balls
    - Check the numbers are correctly identified (Lotto numbers are 1-52, examine each ball carefully)
    
    EXTREMELY IMPORTANT FOR NUMBER RECOGNITION:
    - Be very careful with digits that look similar - common mistakes include:
        * 3 can look like 8 (particularly the numbers 33 and 38)
        * 2 can look like 3 (particularly the numbers 23 and 33)
        * 6 can look like 8 (particularly the numbers 16 and 18, or 26 and 28)
        * 7 can look like 1 (particularly the numbers 7 and 17)
        * 5 can look like 6 (particularly the numbers 5 and 6)
        * 9 can look like 8 (particularly the numbers 9 and 8)
        * 1 can look like 4 (particularly the numbers 14 and 44)
        * 34 can look like 24 (examine the whole digit)
        * 37 can look like 27 (check the top line)
    - Examine the exact shape of each digit:
        * The number 3 has two curves on the right side
        * The number 8 has a complete loop on top and bottom
        * The number 2 has a flat bottom
        * The number 6 has a loop at the bottom only
        * The number 7 has an angled top line, while 1 is straight
        * The number 9 has a loop at the top, while 8 has loops both top and bottom
        
    - Pay special attention to these known correct draws:
      1. For Lotto Draw 2530 (from April 5, 2025)
         The correct numbers are [39, 42, 11, 7, 37, 34] with bonus number [44]
      2. For Lotto Draw 2521 (from March 5, 2025)
         The correct numbers are [33, 36, 38, 40, 46, 49] with bonus number [39]
      3. For Lotto Plus 1 Draw 2530 (from April 5, 2025)
         The correct numbers are [4, 9, 18, 20, 38, 39] with bonus number [47]
         Division payouts:
         * Division 1: 0 winners, R0.00
         * Division 2: 4 winners, R31,115.10
         * Division 3: 91 winners, R2,230.50
         * Division 4: 244 winners, R1,042.40
         * Division 5: 3483 winners, R121.90
         * Division 6: 4224 winners, R87.30
         * Division 7: 42950 winners, R50.00
         * Division 8: 30532 winners, R20.00
    
    - Look at the pattern of numbers across multiple draws to ensure consistency
    - When the website shows both original order and numerical order, always prioritize the original order
    - If you detect a number that seems out of place or doesn't match the pattern, double-check it
    """
    
    # Add lottery-specific instructions
    if "lotto" in base_lottery_type.lower() and "plus" not in base_lottery_type.lower():
        return base_prompt + """
        For Lotto:
        - Extract exactly 6 main numbers for EACH draw
        - Extract 1 bonus number for EACH draw
        - Main numbers are typically in the range of 1-52
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 6 main numbers for a draw, do not invent them - use zeros as placeholders [0,0,0,0,0,0]
        - Pay attention to tables or sections containing "Draw 2530" or similar recent draw numbers
        - Important: The page typically shows 5-10 different draws in a table. Extract EACH row as a separate draw.
        """
    elif "lotto plus" in base_lottery_type.lower():
        return base_prompt + """
        For Lotto Plus:
        - Extract exactly 6 main numbers for EACH draw
        - Extract 1 bonus number for EACH draw
        - Main numbers are typically in the range of 1-52
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 6 main numbers for a draw, do not invent them - use zeros as placeholders [0,0,0,0,0,0]
        - Important: The page typically shows 5-10 different draws in a table. Extract EACH row as a separate draw.
        - Pay EXTRA attention to similar-looking numbers such as:
          - 33 vs 38 (commonly confused)
          - 36 vs 38 (commonly confused)
          - 13 vs 18 (commonly confused)
          - 14 vs 44 (sometimes misread)
          - 6 vs 8 vs 9 (easy to misread)
          - 7 vs 17 (easily confused)
          - 24 vs 34 (easily confused)
          - 27 vs 37 (easily confused)
        - Double-check each ball by looking closely at the shape and any distinguishing features
        - For Lotto Plus 1 and Lotto Plus 2, the specific draw numbers match the main Lotto draw numbers
        - When comparing with the official site, look for the EXACT values displayed there
        - Check the image multiple times before finalizing numbers
        - Use the zoomed sections of screenshots when available for more accurate number reading
        """
    elif "powerball" in base_lottery_type.lower():
        return base_prompt + """
        For PowerBall:
        - Extract exactly 5 main numbers for EACH draw
        - Extract 1 PowerBall number as the bonus_number for EACH draw
        - Main numbers are typically in the range of 1-50
        - PowerBall is typically in the range of 1-20
        - Look for lottery balls in the screenshot - main numbers and PowerBall will be in different colored circles
        - If you can't find exactly 5 main numbers for a draw, do not invent them - use zeros as placeholders [0,0,0,0,0]
        - Important: The page typically shows 5-10 different draws in a table. Extract EACH row as a separate draw.
        """
    elif "daily lotto" in base_lottery_type.lower():
        return base_prompt + """
        For Daily Lotto:
        - Extract exactly 5 main numbers for EACH draw
        - There is no bonus number
        - Main numbers are typically in the range of 1-36
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 5 main numbers for a draw, do not invent them - use zeros as placeholders [0,0,0,0,0]
        - Important: The page typically shows 5-10 different draws in a table. Extract EACH row as a separate draw.
        """
    else:
        return base_prompt
