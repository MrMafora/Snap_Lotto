#!/usr/bin/env python3
"""
Script to inspect HTML files for specific lottery ball elements
"""
import sys
import os
from bs4 import BeautifulSoup
import re
import json

def inspect_ball_elements(html_file):
    try:
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        print(f"Analyzing HTML file: {html_file}")
        
        # Look for ball elements with IDs
        ball_elements = soup.find_all(class_='ball')
        print(f"Found {len(ball_elements)} elements with class 'ball'")
        
        for i, ball in enumerate(ball_elements[:20]):
            ball_id = ball.get('id', 'no-id')
            ball_text = ball.get_text().strip()
            
            # Look for number inside the ball (might be inside a span)
            ball_number = None
            for span in ball.find_all('span'):
                span_text = span.get_text().strip()
                if span_text and span_text.isdigit():
                    ball_number = span_text
            
            # If no number text found, try data attributes
            if not ball_number:
                for attr_name, attr_value in ball.attrs.items():
                    if attr_name.startswith('data-') and attr_value.isdigit():
                        ball_number = attr_value
            
            # Print ball info
            print(f"Ball {i+1}: ID={ball_id}, Text='{ball_text}', Number={ball_number}")
            print(f"  HTML: {ball}")
            
            # Print parent container
            parent = ball.parent
            if parent:
                parent_class = parent.get('class', ['no-class'])
                print(f"  Parent: {parent.name}, Class={parent_class}")
                
                # If parent is a UL, count all siblings
                if parent.name == 'ul':
                    sibling_balls = parent.find_all(class_='ball')
                    sibling_numbers = []
                    
                    for sib in sibling_balls:
                        sib_text = sib.get_text().strip()
                        if sib_text and sib_text.isdigit():
                            sibling_numbers.append(sib_text)
                        else:
                            # Try to find number inside
                            for span in sib.find_all('span'):
                                span_text = span.get_text().strip()
                                if span_text and span_text.isdigit():
                                    sibling_numbers.append(span_text)
                    
                    print(f"  Total balls in container: {len(sibling_balls)}")
                    print(f"  Numbers found: {sibling_numbers}")
        
        # Look for innerHeaderBlock elements (which seemed to contain balls)
        header_blocks = soup.find_all(class_='innerHeaderBlock')
        print(f"\nFound {len(header_blocks)} elements with class 'innerHeaderBlock'")
        
        for i, block in enumerate(header_blocks):
            print(f"Header Block {i+1}:")
            print(f"  HTML: {block}")
            
            # Look for any numbers inside
            ball_elements = block.find_all(class_='ball')
            print(f"  Contains {len(ball_elements)} ball elements")
            
            # Extract any text that looks like numbers
            number_texts = []
            for elem in block.find_all(text=True):
                text = elem.strip()
                if text and text.isdigit():
                    number_texts.append(text)
            
            print(f"  Number texts found: {number_texts}")
            
            # Look for specific text patterns
            draw_pattern = re.compile(r'draw.*?(\d+)', re.IGNORECASE)
            date_pattern = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', re.IGNORECASE)
            
            draw_number = None
            draw_date = None
            
            for text in block.stripped_strings:
                draw_match = draw_pattern.search(text)
                if draw_match:
                    draw_number = draw_match.group(1)
                
                date_match = date_pattern.search(text)
                if date_match:
                    draw_date = date_match.group(1)
            
            print(f"  Draw Number: {draw_number}")
            print(f"  Draw Date: {draw_date}")

        # Try a brute-force method to find all elements containing the word "ball" or "ball1" anywhere
        print("\nBrute force search for 'ball' elements:")
        
        for tag in soup.find_all():
            # Check tag attributes for 'ball'
            ball_related = False
            for attr, value in tag.attrs.items():
                if isinstance(value, str) and ('ball' in value.lower()):
                    ball_related = True
                    break
                elif isinstance(value, list) and any('ball' in str(v).lower() for v in value):
                    ball_related = True
                    break
            
            if ball_related:
                print(f"Tag: {tag.name}, Attrs: {tag.attrs}")
                
                # Look for numbers inside
                number_texts = []
                for elem in tag.find_all(text=True):
                    text = elem.strip()
                    if text and text.isdigit() and 1 <= int(text) <= 52:  # Valid lottery number range
                        number_texts.append(text)
                
                if number_texts:
                    print(f"  Number texts found: {number_texts}")
                    print(f"  HTML: {tag}")

        # Look for tables containing lottery data
        results_tables = soup.find_all('table')
        if results_tables:
            print(f"\nFound {len(results_tables)} tables:")
            
            for idx, table in enumerate(results_tables):
                digit_cells = []
                for cell in table.find_all(['td', 'th']):
                    cell_text = cell.get_text().strip()
                    if cell_text.isdigit() and 1 <= int(cell_text) <= 52:
                        digit_cells.append(cell_text)
                
                if digit_cells:
                    print(f"Table {idx+1} contains {len(digit_cells)} cells with lottery numbers:")
                    print(f"  Numbers: {digit_cells}")
                    print(f"  HTML: {table}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_html.py <html_file>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    if not os.path.exists(html_file):
        print(f"Error: File '{html_file}' not found")
        sys.exit(1)
    
    inspect_ball_elements(html_file)

if __name__ == "__main__":
    main()