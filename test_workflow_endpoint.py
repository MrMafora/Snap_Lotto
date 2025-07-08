#!/usr/bin/env python3
"""
Test script to verify the complete workflow works without web interface
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from daily_automation import run_complete_automation

if __name__ == "__main__":
    print("Testing complete workflow directly...")
    try:
        results = run_complete_automation()
        print(f"\nWorkflow completed!")
        print(f"Overall success: {results['overall_success']}")
        print(f"\nStep results:")
        for step, result in results['steps'].items():
            print(f"  {step}: {'✓' if result['success'] else '✗'} - {result['message']}")
    except Exception as e:
        print(f"Error running workflow: {str(e)}")
        import traceback
        traceback.print_exc()