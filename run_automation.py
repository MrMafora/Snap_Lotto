#!/usr/bin/env python3
"""
Manually trigger the complete automated workflow
"""

import sys
sys.path.append('.')

from scheduler_fix import WorkerSafeLotteryScheduler

def main():
    """Run the complete automation workflow"""
    print("="*60)
    print("STARTING COMPLETE AUTOMATED WORKFLOW")
    print("="*60)
    print("\nThis workflow will:")
    print("  1. Clean up old screenshots")
    print("  2. Capture fresh screenshots from lottery website")
    print("  3. Process screenshots with Google Gemini AI")
    print("  4. Update database with new lottery results")
    print("  5. Validate existing predictions")
    print("  6. Generate fresh AI predictions")
    print("\n" + "="*60 + "\n")
    
    # Initialize and run the scheduler workflow
    scheduler = WorkerSafeLotteryScheduler()
    scheduler.run_automation_now()
    
    print("\n" + "="*60)
    print("WORKFLOW COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
