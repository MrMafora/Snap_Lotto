"""
Check pending extractions in the database
"""
from main import app
from models import PendingExtraction
import json

with app.app_context():
    # Get pending extractions
    pending = PendingExtraction.query.filter_by(reviewed=False).all()
    
    print(f"Found {len(pending)} pending extractions")
    
    for p in pending:
        print(f"\nID: {p.id}")
        print(f"Lottery Type: {p.lottery_type}")
        print(f"Draw Number: {p.draw_number}")
        print(f"Reviewed: {p.reviewed}")
        print(f"Approved: {p.approved}")
        print(f"Extraction Date: {p.extraction_date}")
        
        # Parse and print a summary of the data
        try:
            data = json.loads(p.raw_data)
            print(f"Data Summary:")
            print(f"  Lottery Type: {data.get('lottery_type', 'Unknown')}")
            
            draw_data = data.get('draw_data', [])
            for draw in draw_data:
                print(f"  Draw Number: {draw.get('draw_number', 'Unknown')}")
                print(f"  Draw Date: {draw.get('draw_date', 'Unknown')}")
                print(f"  Winning Numbers: {', '.join(str(n) for n in draw.get('winning_numbers', []))}")
                print(f"  Bonus Ball: {draw.get('bonus_ball', 'None')}")
                
        except Exception as e:
            print(f"Error parsing data: {str(e)}")