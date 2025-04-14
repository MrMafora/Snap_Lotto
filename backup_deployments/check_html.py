#!/usr/bin/env python3
"""
Utility script to examine the HTML structure of lottery websites and identify patterns
to extract lottery numbers.
"""
import sys
import os
import json
from bs4 import BeautifulSoup, Tag
import re

def extract_html_structure(html_file):
    """
    Analyze the HTML structure to find lottery numbers and draw information.
    
    Args:
        html_file (str): Path to the HTML file
    """
    try:
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find draw number
        print("\n=== LOOKING FOR DRAW NUMBER ===")
        draw_pattern = re.compile(r'Draw\s+\d+', re.IGNORECASE)
        draw_elements = soup.find_all(string=draw_pattern)
        if draw_elements:
            print(f"Found {len(draw_elements)} elements with 'Draw N' pattern:")
            for i, elem in enumerate(draw_elements[:5]):  # Show first 5
                print(f"  {i+1}. {elem.strip()}")
                # Show parent element info
                parent = elem.parent
                if parent:
                    print(f"     Parent tag: {parent.name}")
                    print(f"     Parent classes: {parent.get('class', [])}")
                    print(f"     Parent ID: {parent.get('id', 'No ID')}")
        else:
            print("No elements with 'Draw N' pattern found")
            
            # Try to find any element with "draw" in it
            draw_elements = soup.find_all(string=re.compile(r'draw', re.IGNORECASE))
            if draw_elements:
                print(f"Found {len(draw_elements)} elements with 'draw' in text:")
                for i, elem in enumerate(draw_elements[:5]):
                    print(f"  {i+1}. {elem.strip()}")
        
        # Find numbers/balls
        print("\n=== LOOKING FOR LOTTERY BALLS/NUMBERS ===")
        
        # Strategy 1: Look for elements with ball-related class names
        ball_elements = soup.find_all(['span', 'div'], class_=lambda c: c and any(term in str(c).lower() for term in ['ball', 'number', 'circle', 'result']))
        
        if ball_elements:
            print(f"Found {len(ball_elements)} elements with ball-related classes:")
            for i, elem in enumerate(ball_elements[:10]):  # Show first 10
                number_text = elem.get_text().strip()
                print(f"  {i+1}. Text: '{number_text}', Tag: {elem.name}, Class: {elem.get('class', [])}")
                # Show parent element info
                parent = elem.parent
                if parent:
                    print(f"     Parent: {parent.name}, Classes: {parent.get('class', [])}")
        else:
            print("No elements with ball-related classes found")
            
        # Specific search for lottery numbers
        print("\n=== LOOKING FOR SPECIFIC LOTTERY NUMBER ELEMENTS ===")
        
        # Look for elements that might contain lottery balls
        ball_containers = []
        
        # Specific selectors that might contain lottery balls based on common patterns
        selectors = [
            '.drawn-balls', '.lotto-balls', '.ball-container', '.lottery-balls',
            '.lotto-results', '.winning-numbers', '.result-balls',
            '.ball', '.number-ball', '.lottery-ball', '.drawn-number',
            '.innerHeaderBlock'  # This was identified in the previous search
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                ball_containers.extend(elements)
                print(f"Found {len(elements)} elements with selector '{selector}'")
                for elem in elements[:3]:  # Show first 3
                    print(f"  Text: '{elem.get_text().strip()}'")
                    print(f"  HTML: {elem}")
        
        if not ball_containers:
            print("No specific lottery ball containers found")
            
        # Look for elements containing both 'lotto' and 'winning' or 'numbers'
        lotto_result_blocks = soup.find_all(lambda tag: tag.name in ['div', 'section', 'article'] and 
                                          re.search(r'lotto.*winning|winning.*lotto|lotto.*numbers|numbers.*lotto', 
                                                  tag.get_text().lower(), re.DOTALL))
        
        if lotto_result_blocks:
            print(f"\nFound {len(lotto_result_blocks)} elements containing both 'lotto' and 'winning/numbers':")
            for i, block in enumerate(lotto_result_blocks[:3]):
                print(f"  Block {i+1} ({block.name}):")
                print(f"  Classes: {block.get('class', [])}")
                
                # Look for digit-only text elements within this block
                digits_only = [elem.get_text().strip() for elem in block.find_all(text=lambda t: t and t.strip().isdigit())]
                if digits_only:
                    print(f"  Digit-only elements found: {digits_only[:15]}")
                    
                # Look for spans or divs with very short text that might be numbers
                short_texts = [elem.get_text().strip() for elem in block.find_all(['span', 'div']) 
                              if elem.get_text().strip() and len(elem.get_text().strip()) <= 2]
                if short_texts:
                    print(f"  Short text elements found: {short_texts[:15]}")
        else:
            print("\nNo elements containing both 'lotto' and 'winning/numbers' found")
        
        # Strategy 2: Look for tables with result-related text
        print("\n=== LOOKING FOR TABLES WITH RESULTS ===")
        tables = soup.find_all('table')
        results_tables = []
        
        for idx, table in enumerate(tables):
            # Check if this might be a results table
            table_text = table.get_text().lower()
            if any(term in table_text for term in ['draw', 'ball', 'number', 'result']):
                results_tables.append((idx, table))
        
        if results_tables:
            print(f"Found {len(results_tables)} potential result tables:")
            for idx, (table_idx, table) in enumerate(results_tables[:3]):  # Show first 3
                print(f"  Table {table_idx+1}:")
                print(f"  Classes: {table.get('class', [])}")
                
                # Print table rows
                rows = table.find_all('tr')
                print(f"  Has {len(rows)} rows")
                
                # Show first few rows
                for row_idx, row in enumerate(rows[:3]):
                    cells = row.find_all(['td', 'th'])
                    cell_texts = [cell.get_text().strip() for cell in cells]
                    print(f"    Row {row_idx+1}: {cell_texts}")
        else:
            print("No tables with result-related content found")
        
        # Strategy 3: Look for sequences of numbers
        print("\n=== LOOKING FOR SEQUENCES OF NUMBERS ===")
        # Look for paragraphs with series of numbers
        paragraphs = soup.find_all('p')
        
        found_number_sequences = False
        for idx, p in enumerate(paragraphs[:20]):  # Check first 20 paragraphs
            text = p.get_text()
            # Look for sequences of numbers that might be lottery results
            number_matches = re.findall(r'\b([1-9]|[1-4][0-9]|5[0-2])\b', text)
            if len(number_matches) >= 5:  # At least 5 numbers to be a potential result
                found_number_sequences = True
                print(f"  Paragraph {idx+1} with {len(number_matches)} numbers:")
                print(f"    Numbers: {number_matches}")
                print(f"    Text: {text[:100]}...")  # First 100 chars
        
        if not found_number_sequences:
            print("No paragraphs with number sequences found")
        
        # Strategy 4: Look for elements with attributes that might contain ball numbers
        print("\n=== LOOKING FOR ELEMENTS WITH NUMBER ATTRIBUTES ===")
        interesting_elements = []
        
        # Look for elements with data attributes
        for elem in soup.find_all(lambda tag: any(attr.startswith('data-') for attr in tag.attrs.keys())):
            for attr_name, attr_value in elem.attrs.items():
                if attr_name.startswith('data-') and (
                    'ball' in attr_name.lower() or 
                    'number' in attr_name.lower() or 
                    'result' in attr_name.lower()
                ):
                    interesting_elements.append((elem, attr_name, attr_value))
        
        if interesting_elements:
            print(f"Found {len(interesting_elements)} elements with interesting data attributes:")
            for i, (elem, attr_name, attr_value) in enumerate(interesting_elements[:10]):
                print(f"  {i+1}. {elem.name}, {attr_name}='{attr_value}'")
                print(f"     Text: '{elem.get_text().strip()}'")
        else:
            print("No elements with interesting data attributes found")
        
        # Additional Strategy: Look for scripts with embedded data
        print("\n=== LOOKING FOR SCRIPTS WITH EMBEDDED DATA ===")
        scripts = soup.find_all('script')
        lottery_data_scripts = []
        
        for idx, script in enumerate(scripts):
            script_text = script.string if script.string else ""
            if script_text and any(term in script_text.lower() for term in ['draw', 'lotto', 'ball', 'result']):
                lottery_data_scripts.append((idx, script_text))
        
        if lottery_data_scripts:
            print(f"Found {len(lottery_data_scripts)} scripts with potential lottery data:")
            for i, (script_idx, script_text) in enumerate(lottery_data_scripts[:3]):
                preview = script_text[:200].replace('\n', ' ').strip()
                print(f"  Script {script_idx+1}: {preview}...")
                
                # Look for arrays or objects in the script
                array_pattern = r'\[[^\]]*\d+[^\]]*\]'
                arrays = re.findall(array_pattern, script_text)
                if arrays:
                    print(f"    Found {len(arrays)} potential arrays in script:")
                    for j, array in enumerate(arrays[:3]):
                        print(f"      Array {j+1}: {array}")
                
                # Look for structured objects
                obj_pattern = r'\{[^{}]*"draw"[^{}]*\}'
                objects = re.findall(obj_pattern, script_text)
                if objects:
                    print(f"    Found {len(objects)} potential objects with 'draw' in script:")
                    for j, obj in enumerate(objects[:3]):
                        print(f"      Object {j+1}: {obj[:100]}...")
        else:
            print("No scripts with potential lottery data found")
    
    except Exception as e:
        print(f"Error analyzing HTML file: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_html.py <html_file>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    if not os.path.exists(html_file):
        print(f"Error: File '{html_file}' not found")
        sys.exit(1)
    
    print(f"Analyzing HTML file: {html_file}")
    extract_html_structure(html_file)

if __name__ == "__main__":
    main()