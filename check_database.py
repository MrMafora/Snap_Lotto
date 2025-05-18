"""
Simple script to directly check the lottery database
"""

import os
from sqlalchemy import create_engine, text

# Database connection from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def print_lottery_types():
    """Print all unique lottery types in the database"""
    query = text("SELECT DISTINCT lottery_type FROM lottery_result ORDER BY lottery_type")
    
    with engine.connect() as conn:
        result = conn.execute(query)
        types = [row[0] for row in result]
        
        print("Available lottery types:")
        for lt in types:
            print(f"- {lt}")

def print_draw_info(lottery_type, draw_number=None):
    """Print information about a specific draw or recent draws"""
    
    if draw_number:
        # Get specific draw
        query = text("""
            SELECT id, lottery_type, draw_number, draw_date, 
                   numbers, bonus_numbers, divisions, source_url
            FROM lottery_result
            WHERE lottery_type = :lottery_type
            AND draw_number = :draw_number
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"lottery_type": lottery_type, "draw_number": draw_number})
            rows = list(result)
            
            if not rows:
                print(f"No draw found for {lottery_type} with draw number {draw_number}")
                return
            
            for row in rows:
                print(f"\nDraw Information for {lottery_type} #{draw_number}:")
                print(f"Draw Date: {row.draw_date}")
                print(f"Numbers: {row.numbers}")
                print(f"Bonus Numbers: {row.bonus_numbers}")
                
                if row.divisions:
                    print("\nDivision Information:")
                    try:
                        if isinstance(row.divisions, dict):
                            for div, info in row.divisions.items():
                                print(f"  Division {div}: {info}")
                        else:
                            print(f"  Raw divisions data: {row.divisions}")
                    except:
                        print(f"  Raw divisions data: {row.divisions}")
                
                print(f"\nSource URL: {row.source_url}")
    else:
        # Get recent draws
        query = text("""
            SELECT draw_number, draw_date
            FROM lottery_result
            WHERE lottery_type = :lottery_type
            ORDER BY draw_date DESC
            LIMIT 10
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"lottery_type": lottery_type})
            rows = list(result)
            
            if not rows:
                print(f"No draws found for {lottery_type}")
                return
            
            print(f"\nRecent draws for {lottery_type}:")
            for row in rows:
                print(f"Draw #{row.draw_number} - Date: {row.draw_date}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        print_lottery_types()
        print("\nUsage:")
        print("  python check_database.py [lottery_type]")
        print("  python check_database.py [lottery_type] [draw_number]")
    elif len(sys.argv) == 2:
        lottery_type = sys.argv[1]
        print_draw_info(lottery_type)
    elif len(sys.argv) == 3:
        lottery_type = sys.argv[1]
        draw_number = sys.argv[2]
        print_draw_info(lottery_type, draw_number)