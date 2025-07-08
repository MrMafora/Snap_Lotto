#!/usr/bin/env python3
"""
Simple test to verify the complete workflow automation works
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from daily_automation import run_complete_automation

print("Testing complete workflow automation...")
print("=" * 50)

# Run the workflow
results = run_complete_automation()

print("\nWorkflow Results:")
print("=" * 50)
for step, success in results.items():
    status = "✓ SUCCESS" if success else "✗ FAILED"
    print(f"{step}: {status}")

print("\nOverall Success:", results.get('overall_success', False))

if results.get('overall_success'):
    print("\n✓ Complete workflow automation is working!")
else:
    print("\n✗ Workflow had issues. Check the logs above.")