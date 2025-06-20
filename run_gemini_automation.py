#!/usr/bin/env python3
"""
Execute Gemini automation workflow to capture latest lottery results
"""
import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_gemini_automation():
    """Execute the complete Gemini automation workflow"""
    try:
        logger.info("Initiating Gemini automation workflow for latest lottery data...")
        
        # Import the Gemini automation controller
        from gemini_automation_controller import GeminiAutomationController
        
        # Create controller and run complete workflow
        controller = GeminiAutomationController()
        results = controller.run_complete_workflow()
        
        if results and results.get('overall_success'):
            logger.info("SUCCESS: Gemini automation completed successfully!")
            logger.info("Fresh lottery data has been extracted and saved to database.")
            
            # Log individual step results
            for step, success in results.items():
                if step != 'overall_success':
                    status = "SUCCESS" if success else "FAILED"
                    logger.info(f"  {step}: {status}")
                    
            return True
        else:
            error_steps = [step for step, success in results.items() if not success and step != 'overall_success']
            logger.warning(f"Automation completed with issues in: {', '.join(error_steps)}")
            return False
            
    except ImportError as e:
        logger.error(f"Failed to import Gemini automation controller: {e}")
        return False
    except Exception as e:
        logger.error(f"Gemini automation failed: {e}")
        return False

if __name__ == "__main__":
    success = run_gemini_automation()
    sys.exit(0 if success else 1)