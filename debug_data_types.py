#!/usr/bin/env python3
"""
Debug script to identify exact data type issues in lottery analysis
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///lottery.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def diagnose_data_types():
    """Diagnose data type issues in lottery results"""
    session = Session()
    
    try:
        # Get a sample of lottery results to examine data types
        results = session.execute(text("""
            SELECT id, lottery_type, numbers, bonus_numbers, draw_number, draw_date
            FROM lottery_result 
            LIMIT 5
        """)).fetchall()
        
        print("=== LOTTERY DATA TYPE ANALYSIS ===")
        print(f"Found {len(results)} sample records")
        
        for result in results:
            print(f"\nRecord ID: {result.id}")
            print(f"Lottery Type: {result.lottery_type} (type: {type(result.lottery_type)})")
            print(f"Numbers: {result.numbers} (type: {type(result.numbers)})")
            print(f"Bonus Numbers: {result.bonus_numbers} (type: {type(result.bonus_numbers)})")
            print(f"Draw Number: {result.draw_number} (type: {type(result.draw_number)})")
            print(f"Draw Date: {result.draw_date} (type: {type(result.draw_date)})")
            
            # Try to parse numbers
            try:
                if isinstance(result.numbers, str):
                    parsed_numbers = json.loads(result.numbers)
                    print(f"Parsed Numbers: {parsed_numbers} (type: {type(parsed_numbers)})")
                    for i, num in enumerate(parsed_numbers):
                        print(f"  Number {i+1}: {num} (type: {type(num)})")
                else:
                    print(f"Numbers already parsed: {result.numbers}")
            except Exception as e:
                print(f"Error parsing numbers: {e}")
                
        # Check for any mixed data types that might cause comparison issues
        print("\n=== CHECKING FOR PROBLEMATIC DATA ===")
        mixed_types = session.execute(text("""
            SELECT DISTINCT typeof(draw_number) as draw_number_type,
                   typeof(numbers) as numbers_type
            FROM lottery_result
        """)).fetchall()
        
        for row in mixed_types:
            print(f"Draw Number Type: {row.draw_number_type}, Numbers Type: {row.numbers_type}")
            
    except Exception as e:
        print(f"Error during diagnosis: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    diagnose_data_types()