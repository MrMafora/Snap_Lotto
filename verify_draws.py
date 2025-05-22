"""
Script to verify lottery draws from the database
This allows us to check specific draws by lottery type and draw number
"""

import sys
import json
from flask import Flask
from sqlalchemy import create_engine, text
import os
from datetime import datetime

# Create a minimal Flask app to use the database
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

def get_draw_by_id(lottery_type, draw_number):
    """
    Get lottery draw details by type and number
    
    Args:
        lottery_type (str): Type of lottery (e.g. 'Lottery', 'Powerball')
        draw_number (str): Draw number/ID
        
    Returns:
        dict: Information about the draw
    """
    try:
        # Connect to the database
        engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
        with engine.connect() as connection:
            # Query for the specific draw
            query = text("""
                SELECT id, lottery_type, draw_number, draw_date, 
                       numbers, bonus_numbers, divisions, source_url, 
                       created_at, updated_at
                FROM lottery_result
                WHERE lottery_type = :lottery_type
                AND draw_number = :draw_number
            """)
            
            result = connection.execute(query, {"lottery_type": lottery_type, "draw_number": draw_number})
            
            # Process the result
            rows = []
            for row in result:
                # Convert to dict
                draw_data = {
                    "id": row.id,
                    "lottery_type": row.lottery_type,
                    "draw_number": row.draw_number,
                    "draw_date": row.draw_date.isoformat() if row.draw_date else None,
                    "numbers": row.numbers,
                    "bonus_numbers": row.bonus_numbers,
                    "divisions": row.divisions,
                    "source_url": row.source_url,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
                rows.append(draw_data)
            
            return rows
    except Exception as e:
        return {"error": str(e)}

def list_draw_numbers(lottery_type, limit=10):
    """
    List most recent draw numbers for a lottery type
    
    Args:
        lottery_type (str): Type of lottery
        limit (int): Maximum number of draws to return
        
    Returns:
        list: List of draw numbers
    """
    try:
        engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
        with engine.connect() as connection:
            query = text("""
                SELECT draw_number, draw_date
                FROM lottery_result
                WHERE lottery_type = :lottery_type
                ORDER BY draw_date DESC
                LIMIT :limit
            """)
            
            result = connection.execute(query, {"lottery_type": lottery_type, "limit": limit})
            
            draws = []
            for row in result:
                draws.append({
                    "draw_number": row.draw_number,
                    "draw_date": row.draw_date.isoformat() if row.draw_date else None,
                })
            
            return draws
    except Exception as e:
        return {"error": str(e)}

def list_lottery_types():
    """
    List all lottery types in the database
    
    Returns:
        list: Unique lottery types
    """
    try:
        engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
        with engine.connect() as connection:
            query = text("""
                SELECT DISTINCT lottery_type
                FROM lottery_result
                ORDER BY lottery_type
            """)
            
            result = connection.execute(query)
            
            lottery_types = [row[0] for row in result]
            return lottery_types
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Available lottery types:")
        lottery_types = list_lottery_types()
        for lt in lottery_types:
            print(f"- {lt}")
        
        print("\nUsage:")
        print("python verify_draws.py [lottery_type]")
        print("python verify_draws.py [lottery_type] [draw_number]")
        sys.exit(1)
    
    # List draw numbers for a lottery type
    if len(sys.argv) == 2:
        lottery_type = sys.argv[1]
        draws = list_draw_numbers(lottery_type)
        
        print(f"Recent draws for {lottery_type}:")
        for draw in draws:
            print(f"Draw #{draw['draw_number']} - Date: {draw['draw_date']}")
    
    # Get specific draw details
    if len(sys.argv) == 3:
        lottery_type = sys.argv[1]
        draw_number = sys.argv[2]
        
        draw_info = get_draw_by_id(lottery_type, draw_number)
        
        if not draw_info:
            print(f"No draw found for {lottery_type} with draw number {draw_number}")
        else:
            print(json.dumps(draw_info, indent=2))