#!/usr/bin/env python3
"""
Daily Automation Coordinator
Orchestrates the complete 4-step lottery data automation workflow
"""

import logging
from datetime import datetime
import step1_cleanup
import step2_capture
import step3_ai_process
import step4_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_complete_automation():
    """Run the complete 4-step automation workflow"""
    logger.info("=== DAILY AUTOMATION WORKFLOW STARTED ===")
    start_time = datetime.now()
    
    results = {
        'step1_cleanup': False,
        'step2_capture': False,
        'step3_ai_process': False,
        'step4_database': False,
        'overall_success': False
    }
    
    try:
        # Step 1: Cleanup
        logger.info("Starting Step 1: Cleanup")
        results['step1_cleanup'] = step1_cleanup.run_cleanup()
        
        if not results['step1_cleanup']:
            logger.warning("Step 1 failed, but continuing with workflow")
        
        # Step 2: Screenshot Capture
        logger.info("Starting Step 2: Screenshot Capture")
        results['step2_capture'] = step2_capture.run_capture()
        
        if not results['step2_capture']:
            logger.error("Step 2 failed - cannot continue without screenshots")
            return results
        
        # Step 3: AI Processing
        logger.info("Starting Step 3: AI Processing")
        results['step3_ai_process'] = step3_ai_process.run_ai_process()
        
        if not results['step3_ai_process']:
            logger.error("Step 3 failed - cannot continue without extracted data")
            return results
        
        # Step 4: Database Update
        logger.info("Starting Step 4: Database Update")
        results['step4_database'] = step4_database.run_database_update()
        
        # Determine overall success
        results['overall_success'] = (
            results['step2_capture'] and 
            results['step3_ai_process'] and 
            results['step4_database']
        )
        
    except Exception as e:
        logger.error(f"Automation workflow failed with exception: {str(e)}")
        results['overall_success'] = False
    
    # Log completion
    end_time = datetime.now()
    duration = end_time - start_time
    
    if results['overall_success']:
        logger.info(f"=== DAILY AUTOMATION COMPLETED SUCCESSFULLY in {duration} ===")
    else:
        logger.error(f"=== DAILY AUTOMATION FAILED after {duration} ===")
    
    logger.info(f"Results: {results}")
    return results

def run_individual_step(step_name):
    """Run an individual automation step"""
    logger.info(f"=== RUNNING INDIVIDUAL STEP: {step_name.upper()} ===")
    
    try:
        if step_name == 'cleanup':
            return step1_cleanup.run_cleanup()
        elif step_name == 'capture':
            return step2_capture.run_capture()
        elif step_name == 'ai_process':
            return step3_ai_process.run_ai_process()
        elif step_name == 'database':
            return step4_database.run_database_update()
        else:
            logger.error(f"Unknown step: {step_name}")
            return False
            
    except Exception as e:
        logger.error(f"Step {step_name} failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    run_complete_automation()