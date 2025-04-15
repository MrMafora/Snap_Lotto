#!/usr/bin/env python
"""
Utility script to examine the Excel spreadsheet structure
"""

import pandas as pd
import sys

def examine_excel(excel_file):
    """Examine Excel file structure"""
    try:
        # Get all sheet names
        xl = pd.ExcelFile(excel_file)
        print(f"Excel file contains {len(xl.sheet_names)} sheets:")
        for i, sheet in enumerate(xl.sheet_names):
            print(f"  Sheet {i+1}: {sheet}")
            
        # Try to read each sheet and show its structure
        for sheet_name in xl.sheet_names:
            print(f"\nExamining sheet: {sheet_name}")
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
                print("Columns:")
                for col in df.columns:
                    print(f"  - {col}")
                
                # Show first 5 rows
                print("\nFirst 5 rows sample:")
                print(df.head(5).to_string())
                
                # Check for lottery type columns
                lottery_columns = [col for col in df.columns if 'lotto' in str(col).lower() or 'power' in str(col).lower() or 'game' in str(col).lower()]
                if lottery_columns:
                    print("\nFound potential lottery-related columns:")
                    for col in lottery_columns:
                        print(f"  - {col}")
                        # Show sample values
                        sample_values = df[col].dropna().unique()[:5]
                        if len(sample_values) > 0:
                            print(f"    Sample values: {', '.join(str(v) for v in sample_values)}")
                
            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {str(e)}")
                
    except Exception as e:
        print(f"Error examining Excel file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python examine_excel.py <excel_file>")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    examine_excel(excel_file)