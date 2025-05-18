#!/usr/bin/env python3
"""
This script updates the lottery_analysis.py file to properly handle number formats.

The main issue is that the analysis code is trying to compare strings with integers
using the >= operator, which causes the error:
'>=' not supported between instances of 'str' and 'int'
"""

import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fix_analysis')

def fix_analysis_file():
    """
    Fix the lottery_analysis.py file to properly handle number conversions.
    """
    file_path = 'lottery_analysis.py'
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Fix the patterns that convert string numbers to integers
    # Pattern 1: Fix the comparison in the all_types_df analysis
    pattern1 = r'if 0 <= (int\(num\)) <= max_number:\s*combined_frequency\[int\(num\)\] \+= 1'
    replacement1 = '''try:
                            num_int = int(num) if isinstance(num, str) else num
                            if 0 <= num_int <= max_number:
                                combined_frequency[num_int] += 1
                        except (ValueError, TypeError):
                            # Skip invalid number formats
                            continue'''
    
    # Pattern 2: Fix the per-lottery type analysis
    pattern2 = r'if 0 <= (int\(num\)) <= max_number:\s*frequency\[int\(num\)\] \+= 1'
    replacement2 = '''try:
                            num_int = int(num) if isinstance(num, str) else num
                            if 0 <= num_int <= max_number:
                                frequency[num_int] += 1
                        except (ValueError, TypeError):
                            # Skip invalid number formats
                            continue'''
    
    # Apply the replacements
    content = re.sub(pattern1, replacement1, content)
    content = re.sub(pattern2, replacement2, content)
    
    # Fix other similar patterns
    pattern3 = r'for num in all_numbers:\s*if (0 <= int\(num\) <= max_number):'
    replacement3 = '''for num in all_numbers:
                try:
                    num_int = int(num) if isinstance(num, str) else num
                    if 0 <= num_int <= max_number:'''
    
    # Add a closing "except" block for pattern3
    pattern4 = r'frequency\[int\(num\)\] \+= 1\s*(\n\s*)'
    replacement4 = '''frequency[num_int] += 1
                except (ValueError, TypeError):
                    # Skip invalid number formats
                    continue\\1'''
    
    content = re.sub(pattern3, replacement3, content)
    content = re.sub(pattern4, replacement4, content)
    
    # Write the updated content
    with open(file_path, 'w') as file:
        file.write(content)
    
    logger.info(f"Successfully updated {file_path}")
    return True

if __name__ == "__main__":
    fix_analysis_file()