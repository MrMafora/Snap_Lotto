import pandas as pd
import sys

file_path = './attached_assets/lottery_data_template_new.xlsx'
print(f"Checking Excel file: {file_path}")

try:
    xls = pd.ExcelFile(file_path)
    print(f"Sheet names: {xls.sheet_names}")
    
    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            print(f"\nSheet: {sheet}")
            print(f"Columns: {list(df.columns)}")
            print(f"Num rows: {len(df)}")
            if len(df) > 0:
                print(f"First row: {df.iloc[0].to_dict()}")
        except Exception as e:
            print(f"Error reading sheet {sheet}: {e}")
except Exception as e:
    print(f"Error opening Excel file: {e}")
