"""
Check and display screenshot database entries
"""
import os
import sys
from flask import Flask
from config import Config
from models import db, Screenshot

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    screenshots = Screenshot.query.all()
    print(f"Found {len(screenshots)} screenshot records")
    
    txt_files = 0
    png_files = 0
    missing_files = 0
    
    # Count different types
    for s in screenshots:
        if s.path:
            if s.path.endswith('.txt'):
                txt_files += 1
            elif s.path.endswith('.png'):
                png_files += 1
                
            if not os.path.exists(s.path):
                missing_files += 1
                
    print(f"PNG files: {png_files}")
    print(f"TXT files: {txt_files}")
    print(f"Missing files: {missing_files}")
    
    # Show all records
    print("\nAll screenshot records:")
    for s in screenshots:
        exists = "EXISTS" if s.path and os.path.exists(s.path) else "MISSING"
        print(f"ID {s.id}: {s.lottery_type} - {s.path} - {exists}")
    
    # Check if there are any .png files in the screenshots directory that aren't in the database
    print("\nChecking for PNG files not in database...")
    db_paths = [s.path for s in screenshots if s.path]
    
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    png_files_in_dir = [os.path.join(screenshot_dir, f) for f in os.listdir(screenshot_dir) 
                       if f.endswith('.png') and os.path.isfile(os.path.join(screenshot_dir, f))]
    
    not_in_db = [f for f in png_files_in_dir if f not in db_paths]
    if not_in_db:
        print(f"Found {len(not_in_db)} PNG files not in database:")
        for f in not_in_db:
            print(f"  {f}")
    else:
        print("All PNG files are in the database.")