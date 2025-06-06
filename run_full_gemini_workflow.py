#!/usr/bin/env python3
"""
Complete Gemini workflow with advanced comprehensive extraction
"""

import os
import sys
import logging
from gemini_automation_controller import GeminiAutomationController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Execute the complete Gemini automation workflow with comprehensive extraction"""
    logger.info("=== STARTING COMPLETE GEMINI WORKFLOW ===")
    
    try:
        # Initialize the Gemini automation controller
        controller = GeminiAutomationController()
        
        # Run the complete 4-step workflow
        success = controller.run_complete_workflow()
        
        if success:
            logger.info("✅ Complete Gemini workflow executed successfully")
            return True
        else:
            logger.error("❌ Gemini workflow failed")
            return False
            
    except Exception as e:
        logger.error(f"Error in Gemini workflow: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)