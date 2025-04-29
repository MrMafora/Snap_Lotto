import pandas as pd
import sys
import os

def check_daily_lottery(excel_path):
    """Check Excel file for Daily Lottery draws 2234, 2235, and 2236"""
    print(f"Checking file: {excel_path}")
    print(f"File exists: {os.path.exists(excel_path)}")
    
    try:
        # Try to open with openpyxl engine
        xls = pd.ExcelFile(excel_path, engine='openpyxl')
        
        # Check if 'Daily Lottery' sheet exists
        daily_lottery_sheets = [sheet for sheet in xls.sheet_names if 'daily' in sheet.lower()]
        print(f"Daily Lottery related sheets: {daily_lottery_sheets}")
        
        # Check all sheets for Daily Lottery draws
        for sheet_name in xls.sheet_names:
            print(f"\nChecking sheet: {sheet_name}")
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet_name, engine='openpyxl')
                
                # Skip empty sheets
                if df.empty:
                    print(f"Sheet is empty")
                    continue
                
                # Check if this is a lottery data sheet
                if 'Game Name' in df.columns and 'Draw Number' in df.columns:
                    # Look for Daily Lottery entries
                    daily_entries = df[df['Game Name'].astype(str).str.contains('Daily', case=False, na=False)]
                    if not daily_entries.empty:
                        print(f"Found {len(daily_entries)} Daily Lottery entries")
                        
                        # Look specifically for draws 2234, 2235, 2236
                        target_draws = daily_entries[daily_entries['Draw Number'].astype(str).isin(['2234', '2235', '2236'])]
                        if not target_draws.empty:
                            print(f"Found {len(target_draws)} target draws (2234, 2235, 2236)")
                            print("\nTarget draws:")
                            print(target_draws[['Game Name', 'Draw Number', 'Draw Date']].to_string())
                        else:
                            print("Target draws not found in this sheet")
                else:
                    print("Not a lottery data sheet (missing Game Name or Draw Number columns)")
            
            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {str(e)}")
    
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "attached_assets/lottery_data_template_20250429_020457.xlsx"
    
    check_daily_lottery(file_path)