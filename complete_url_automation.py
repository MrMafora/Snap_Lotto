#!/usr/bin/env python3
"""
Complete URL-Based Lottery Automation System
Captures authentic lottery content directly from SA National Lottery URLs
"""

import os
import time
import logging
from datetime import datetime

# Import the individual steps
from step2_capture import run_screenshot_capture
from step3_extract import process_captured_content

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_complete_url_automation():
    """Run the complete URL-based lottery automation workflow"""
    logger.info("=== COMPLETE URL LOTTERY AUTOMATION STARTED ===")
    start_time = datetime.now()
    
    try:
        # Step 1: Capture authentic lottery content from URLs
        logger.info("Step 1: Capturing authentic lottery content from SA National Lottery URLs...")
        capture_results = run_screenshot_capture()
        
        successful_captures = len([r for r in capture_results if r and r['status'] == 'success'])
        logger.info(f"Captured content from {successful_captures} lottery URLs")
        
        if successful_captures == 0:
            logger.error("No lottery content was captured successfully")
            return {
                'status': 'failed',
                'message': 'No authentic lottery content captured',
                'capture_results': capture_results,
                'extraction_results': []
            }
        
        # Step 2: Extract lottery data from captured content
        logger.info("Step 2: Extracting lottery data from captured content...")
        extraction_results = process_captured_content()
        
        logger.info(f"Extracted lottery data from {len(extraction_results)} files")
        
        # Step 3: Summary of results
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=== COMPLETE URL LOTTERY AUTOMATION COMPLETED ===")
        logger.info(f"Total processing time: {duration.total_seconds():.2f} seconds")
        logger.info(f"Successfully processed {successful_captures} lottery URLs")
        
        return {
            'status': 'success',
            'message': f'Successfully processed {successful_captures} lottery URLs',
            'capture_results': capture_results,
            'extraction_results': extraction_results,
            'processing_time': duration.total_seconds(),
            'timestamp': end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in complete automation workflow: {str(e)}")
        return {
            'status': 'error',
            'message': f'Automation failed: {str(e)}',
            'capture_results': [],
            'extraction_results': []
        }

def display_automation_summary(results):
    """Display a summary of the automation results"""
    print("\n" + "="*60)
    print("SA NATIONAL LOTTERY URL AUTOMATION SUMMARY")
    print("="*60)
    
    if results['status'] == 'success':
        print(f"✓ Status: {results['message']}")
        print(f"✓ Processing Time: {results.get('processing_time', 0):.2f} seconds")
        print(f"✓ Timestamp: {results.get('timestamp', 'N/A')}")
        
        # Capture results
        capture_results = results.get('capture_results', [])
        successful_captures = len([r for r in capture_results if r and r['status'] == 'success'])
        print(f"\nURL CAPTURES: {successful_captures} successful")
        
        for result in capture_results:
            if result and result['status'] == 'success':
                print(f"  ✓ {result['lottery_type']}: {result['filename']}")
            elif result:
                print(f"  ✗ {result['lottery_type']}: {result['status']}")
        
        # Extraction results
        extraction_results = results.get('extraction_results', [])
        print(f"\nDATA EXTRACTION: {len(extraction_results)} files processed")
        
        for data in extraction_results:
            jackpot = data.get('jackpot_amount', 'N/A')
            draw_date = data.get('draw_date', 'N/A')
            print(f"  ✓ {data['lottery_type']}: {jackpot} | Next Draw: {draw_date}")
    
    else:
        print(f"✗ Status: {results['message']}")
    
    print("="*60)

if __name__ == "__main__":
    # Run the complete automation
    results = run_complete_url_automation()
    
    # Display summary
    display_automation_summary(results)
    
    # Save results to file
    import json
    output_file = f"automation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {output_file}")