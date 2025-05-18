#!/usr/bin/env python3
"""
Test script to import data from the test Excel file
"""
from flask import Flask
from models import db, ImportHistory, LotteryResult
from import_excel import process_excel_file
import os

# Create a simple Flask app for database context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def import_test_data():
    """Import data from the test Excel file"""
    with app.app_context():
        # Count records before import
        before_count = LotteryResult.query.count()
        
        # Import the test data
        filename = 'lottery_test_data.xlsx'
        result = process_excel_file(filename)
        
        # Count records after import
        after_count = LotteryResult.query.count()
        
        # Get the most recent import history
        recent_import = ImportHistory.query.order_by(ImportHistory.import_date.desc()).first()
        
        print(f"Before import: {before_count} records")
        print(f"After import: {after_count} records")
        print(f"New records added: {after_count - before_count}")
        print(f"Import result: {result}")
        
        if recent_import:
            print(f"Recent import: {recent_import.file_name}, processed {recent_import.records_processed} records")
        
        return result

if __name__ == "__main__":
    import_test_data()