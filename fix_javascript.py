"""
Fix JavaScript in Python script

This script fixes JavaScript comments in Python multiline strings by replacing 
// comments with /* comments */ to make them compatible with Python syntax.
"""

import re
import sys

def fix_javascript_in_python(input_file, output_file):
    """
    Fix JavaScript comments in Python multiline strings
    Args:
        input_file (str): Path to input Python file
        output_file (str): Path to output Python file
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace JavaScript comments in multiline strings
        # First find all triple-quoted strings
        multiline_strings = re.findall(r'""".*?"""', content, re.DOTALL)
        
        fixed_content = content
        for string in multiline_strings:
            # Replace // comments with /* comments */
            fixed_string = re.sub(r'//\s*(.*?)$', r'/* \1 */', string, flags=re.MULTILINE)
            
            # Replace the original string with the fixed one
            fixed_content = fixed_content.replace(string, fixed_string)
        
        # Find all try blocks without except or finally
        # This is a simplified approach and may not catch all cases
        try_blocks = re.findall(r'try:\s*([^except|finally]+?)(?=except|finally|\n\S)', fixed_content, re.DOTALL)
        
        for block in try_blocks:
            if block.strip() and not re.search(r'except|finally', block):
                # Add a simple except block if missing
                fixed_block = block + "\n        except Exception as e:\n            print(f\"Error: {str(e)}\")\n"
                fixed_content = fixed_content.replace(block, fixed_block)
        
        # Write the fixed content to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        return True
    except Exception as e:
        print(f"Error fixing JavaScript in Python: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_javascript.py input_file output_file")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = fix_javascript_in_python(input_file, output_file)
    if success:
        print(f"Successfully fixed JavaScript in {input_file} and saved to {output_file}")
    else:
        print(f"Failed to fix JavaScript in {input_file}")
        sys.exit(1)