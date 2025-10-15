#!/usr/bin/env python3
"""
Production Data Import Script
Run this script in your PRODUCTION environment to import lottery results
"""

import os
import psycopg2
import json
from datetime import datetime

# Data to import (from development database)
LOTTERY_DATA = [
    # LOTTO results
    {"lottery_type": "LOTTO", "draw_number": 2584, "draw_date": "2025-10-11", "main_numbers": "[23, 24, 27, 33, 36, 58]", "bonus_numbers": "[18]", "next_draw_date": "2025-10-15", "prize_divisions": '[{"amount": "R0.00", "winners": 0, "division": "Div 1", "description": "SIX CORRECT NUMBERS"}, {"amount": "R0.00", "winners": 0, "division": "Div 2", "description": "FIVE CORRECT NUMBERS + BONUS BALL"}, {"amount": "R7,133.50", "winners": 20, "division": "Div 3", "description": "FIVE CORRECT NUMBERS"}, {"amount": "R2,432.50", "winners": 51, "division": "Div 4", "description": "FOUR CORRECT NUMBERS + BONUS BALL"}, {"amount": "R286.30", "winners": 1083, "division": "Div 5", "description": "FOUR CORRECT NUMBERS"}, {"amount": "R142.80", "winners": 1738, "division": "Div 6", "description": "THREE CORRECT NUMBERS + BONUS BALL"}, {"amount": "R51.30", "winners": 25366, "division": "Div 7", "description": "THREE CORRECT NUMBERS"}, {"amount": "R6.90", "winners": 260726, "division": "Div 8", "description": "AS PER THE GAME RULES AT THE TIME OF DRAW"}]'},
    
    # LOTTO PLUS 1 results
    {"lottery_type": "LOTTO PLUS 1", "draw_number": 2584, "draw_date": "2025-10-11", "main_numbers": "[8, 9, 13, 37, 50, 56]", "bonus_numbers": "[2]", "next_draw_date": "2025-10-15", "prize_divisions": '[{"amount": "R0.00", "winners": 0, "division": "Div 1", "description": "SIX CORRECT NUMBERS"}, {"amount": "R26,018.80", "winners": 1, "division": "Div 2", "description": "FIVE CORRECT NUMBERS + BONUS BALL"}, {"amount": "R3,113.40", "winners": 13, "division": "Div 3", "description": "FIVE CORRECT NUMBERS"}, {"amount": "R1,562.70", "winners": 37, "division": "Div 4", "description": "FOUR CORRECT NUMBERS + BONUS BALL"}, {"amount": "R154.90", "winners": 933, "division": "Div 5", "description": "FOUR CORRECT NUMBERS"}, {"amount": "R86.50", "winners": 1338, "division": "Div 6", "description": "THREE CORRECT NUMBERS + BONUS BALL"}, {"amount": "R28.60", "winners": 21199, "division": "Div 7", "description": "THREE CORRECT NUMBERS"}, {"amount": "R4.80", "winners": 225977, "division": "Div 8", "description": "AS PER THE GAME RULES AT THE TIME OF DRAW"}]'},
    
    # LOTTO PLUS 2 results
    {"lottery_type": "LOTTO PLUS 2", "draw_number": 2584, "draw_date": "2025-10-11", "main_numbers": "[11, 33, 40, 50, 52, 56]", "bonus_numbers": "[58]", "next_draw_date": "2025-10-15", "prize_divisions": '[{"amount": "R0.00", "winners": 0, "division": "Div 1", "description": "SIX CORRECT NUMBERS"}, {"amount": "R0.00", "winners": 0, "division": "Div 2", "description": "FIVE CORRECT NUMBERS + BONUS BALL"}, {"amount": "R5,241.90", "winners": 12, "division": "Div 3", "description": "FIVE CORRECT NUMBERS"}, {"amount": "R1,367.40", "winners": 40, "division": "Div 4", "description": "FOUR CORRECT NUMBERS + BONUS BALL"}, {"amount": "R156.50", "winners": 874, "division": "Div 5", "description": "FOUR CORRECT NUMBERS"}, {"amount": "R79.00", "winners": 1385, "division": "Div 6", "description": "THREE CORRECT NUMBERS + BONUS BALL"}, {"amount": "R27.60", "winners": 20777, "division": "Div 7", "description": "THREE CORRECT NUMBERS"}, {"amount": "R4.90", "winners": 206664, "division": "Div 8", "description": "AS PER THE GAME RULES AT THE TIME OF DRAW"}]'},
    
    # POWERBALL results
    {"lottery_type": "POWERBALL", "draw_number": 1658, "draw_date": "2025-10-11", "main_numbers": "[6, 10, 40, 44, 50]", "bonus_numbers": "[11]", "next_draw_date": "2025-10-14", "prize_divisions": '[{"amount": "R0.00", "winners": 0, "division": "Div 1", "description": "FIVE CORRECT NUMBERS + POWERBALL"}, {"amount": "R0.00", "winners": 0, "division": "Div 2", "description": "FIVE CORRECT NUMBERS"}, {"amount": "R19,062.50", "winners": 8, "division": "Div 3", "description": "FOUR CORRECT NUMBERS + POWERBALL"}, {"amount": "R2,382.30", "winners"": 64, "division": "Div 4", "description": "FOUR CORRECT NUMBERS"}, {"amount": "R447.30", "winners": 332, "division": "Div 5", "description": "THREE CORRECT NUMBERS + POWERBALL"}, {"amount": "R112.40", "winners": 1323, "division": "Div 6", "description": "THREE CORRECT NUMBERS"}, {"amount": "R74.40", "winners": 2002, "division": "Div 7", "description": "TWO CORRECT NUMBERS + POWERBALL"}, {"amount": "R35.40", "winners": 7438, "division": "Div 8", "description": "ONE CORRECT NUMBER + POWERBALL"}, {"amount": "R20.00", "winners": 12979, "division": "Div 9", "description": "POWERBALL"}]'},
    
    # POWERBALL PLUS results
    {"lottery_type": "POWERBALL PLUS", "draw_number": 1658, "draw_date": "2025-10-10", "main_numbers": "[3, 22, 27, 43, 50]", "bonus_numbers": "[7]", "next_draw_date": "2025-10-14", "prize_divisions": '[{"amount": "R0.00", "winners": 0, "division": "Div 1", "description": "FIVE CORRECT NUMBERS + POWERBALL"}, {"amount": "R0.00", "winners": 0, "division": "Div 2", "description": "FIVE CORRECT NUMBERS"}, {"amount": "R10,540.10", "winners": 13, "division": "Div 3", "description": "FOUR CORRECT NUMBERS + POWERBALL"}, {"amount": "R1,421.30", "winners": 96, "division": "Div 4", "description": "FOUR CORRECT NUMBERS"}, {"amount": "R267.30", "winners": 512, "division": "Div 5", "description": "THREE CORRECT NUMBERS + POWERBALL"}, {"amount": "R62.80", "winners": 2176, "division": "Div 6", "description": "THREE CORRECT NUMBERS"}, {"amount": "R43.40", "winners": 3144, "division": "Div 7", "description": "TWO CORRECT NUMBERS + POWERBALL"}, {"amount": "R19.80", "winners": 11634, "division": "Div 8", "description": "ONE CORRECT NUMBER + POWERBALL"}, {"amount": "R12.00", "winners": 20277, "division": "Div 9", "description": "POWERBALL"}]'},
    
    # DAILY LOTTO results
    {"lottery_type": "DAILY LOTTO", "draw_number": 2404, "draw_date": "2025-10-13", "main_numbers": "[4, 10, 21, 24, 32]", "bonus_numbers": None, "next_draw_date": "2025-10-14", "prize_divisions": '[{"amount": "R176,974.80", "winners": 2, "division": "Div 1", "description": "FIVE CORRECT NUMBERS"}, {"amount": "R300.90", "winners": 271, "division": "Div 2", "description": "FOUR CORRECT NUMBERS"}, {"amount": "R20.40", "winners": 8005, "division": "Div 3", "description": "THREE CORRECT NUMBERS"}, {"amount": "R5.10", "winners": 77799, "division": "Div 4", "description": "TWO CORRECT NUMBERS"}]'},
    {"lottery_type": "DAILY LOTTO", "draw_number": 2403, "draw_date": "2025-10-12", "main_numbers": "[7, 12, 16, 26, 33]", "bonus_numbers": None, "next_draw_date": "2025-10-13", "prize_divisions": '[{"amount": "R91,419.20", "winners": 3, "division": "Div 1", "description": "FIVE CORRECT NUMBERS"}, {"amount": "R292.50", "winners": 216, "division": "Div 2", "description": "FOUR CORRECT NUMBERS"}, {"amount": "R19.50", "winners": 6478, "division": "Div 3", "description": "THREE CORRECT NUMBERS"}, {"amount": "R5.00", "winners": 61938, "division": "Div 4", "description": "TWO CORRECT NUMBERS"}]'},
    {"lottery_type": "DAILY LOTTO", "draw_number": 2402, "draw_date": "2025-10-11", "main_numbers": "[1, 11, 14, 16, 34]", "bonus_numbers": None, "next_draw_date": "2025-10-12", "prize_divisions": '[{"amount": "R392,450.60", "winners": 1, "division": "Div 1", "description": "FIVE CORRECT NUMBERS"}, {"amount": "R316.00", "winners": 286, "division": "Div 2", "description": "FOUR CORRECT NUMBERS"}, {"amount": "R20.00", "winners": 9068, "division": "Div 3", "description": "THREE CORRECT NUMBERS"}, {"amount": "R5.00", "winners": 88722, "division": "Div 4", "description": "TWO CORRECT NUMBERS"}]'},
]

def import_data_to_production():
    """Import lottery data into production database"""
    try:
        # Connect to production database using DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not found!")
            print("Make sure you're running this in the production environment.")
            return False
        
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("=" * 60)
        print("🚀 PRODUCTION DATA IMPORT STARTED")
        print("=" * 60)
        print(f"Connected to production database: {database_url[:50]}...")
        
        imported_count = 0
        skipped_count = 0
        
        for data in LOTTERY_DATA:
            # Check if this draw already exists
            cur.execute("""
                SELECT id FROM lottery_results 
                WHERE lottery_type = %s AND draw_number = %s
            """, (data['lottery_type'], data['draw_number']))
            
            existing = cur.fetchone()
            
            if existing:
                print(f"⏭️  SKIPPED: {data['lottery_type']} Draw {data['draw_number']} (already exists)")
                skipped_count += 1
                continue
            
            # Insert the data
            cur.execute("""
                INSERT INTO lottery_results 
                (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, next_draw_date, prize_divisions, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                data['lottery_type'],
                data['draw_number'],
                data['draw_date'],
                data['main_numbers'],
                data['bonus_numbers'],
                data.get('next_draw_date'),
                data.get('prize_divisions')
            ))
            
            print(f"✅ IMPORTED: {data['lottery_type']} Draw {data['draw_number']} ({data['draw_date']})")
            imported_count += 1
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ IMPORT COMPLETE!")
        print(f"   • Imported: {imported_count} records")
        print(f"   • Skipped: {skipped_count} records (already existed)")
        print("=" * 60)
        
        # Verify the import
        cur.execute("SELECT COUNT(*) FROM lottery_results")
        total_count = cur.fetchone()[0]
        print(f"\n📊 Total lottery results in production database: {total_count}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ IMPORT FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔐 Production Data Import Tool")
    print("This script will import lottery results into your PRODUCTION database.\n")
    
    # Safety check
    response = input("Are you sure you want to import data to PRODUCTION? (yes/no): ")
    if response.lower() != 'yes':
        print("Import cancelled.")
        exit(0)
    
    success = import_data_to_production()
    
    if success:
        print("\n✅ All lottery data has been imported successfully!")
        print("🌐 Visit https://snaplotto.replit.app/ to see the results!")
    else:
        print("\n❌ Import failed. Please check the errors above.")
