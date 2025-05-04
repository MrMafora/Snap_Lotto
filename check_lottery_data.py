import pandas as pd
import sys
import os
from datetime import datetime

def check_excel_file(file_path):
    """Analyze Excel file and report its contents"""
    print(f"Checking file: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    print(f"File size: {os.path.getsize(file_path)} bytes")
    
    try:
        # Try to open with openpyxl engine
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        sheet_names = xls.sheet_names
        print(f"Found {len(sheet_names)} sheets: {sheet_names}")
        
        # Read each sheet
        for sheet_name in sheet_names:
            print(f"\nReading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            
            if df.empty:
                print(f"  Sheet '{sheet_name}' is empty")
                continue
                
            print(f"  Total rows: {len(df)}")
            print(f"  Columns: {list(df.columns)}")
            
            # Check for Lottery data
            if 'Game Name' in df.columns and 'Draw Number' in df.columns and 'Draw Date' in df.columns:
                print(f"  This appears to be a lottery data sheet")
                
                # Get unique lottery types
                if not df['Game Name'].empty:
                    lottery_types = df['Game Name'].dropna().unique()
                    print(f"  Lottery types: {lottery_types}")
                
                # Check draw numbers
                if not df['Draw Number'].empty:
                    first_draw = df['Draw Number'].dropna().iloc[0] if len(df['Draw Number'].dropna()) > 0 else "N/A"
                    last_draw = df['Draw Number'].dropna().iloc[-1] if len(df['Draw Number'].dropna()) > 0 else "N/A"
                    print(f"  Draw number range: {first_draw} to {last_draw}")
                
                # Check draw dates
                if not df['Draw Date'].empty:
                    date_col = df['Draw Date'].dropna()
                    if len(date_col) > 0:
                        first_date = date_col.iloc[0]
                        last_date = date_col.iloc[-1]
                        if isinstance(first_date, datetime):
                            print(f"  Date range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
                        else:
                            print(f"  Date range: {first_date} to {last_date}")
                
                # Show sample data - first 2 rows
                print("\n  Sample data (first 2 rows):")
                print(df.head(2))
                
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "attached_assets/lottery_data_template_20250429_020457.xlsx"
    
    check_excel_file(file_path)