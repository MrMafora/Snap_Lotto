#!/usr/bin/env python
"""
Script to view the contents of an Excel file on the command line.
This helps diagnose issues with Excel file imports.
"""

import os
import sys
import pandas as pd

def view_excel_file(file_path, rows=5):
    """View the first few rows of an Excel file."""
    try:
        # Try to read with openpyxl engine
        print(f"Attempting to read Excel file with openpyxl engine: {file_path}")
        df = pd.read_excel(file_path, engine='openpyxl')
        print(f"\nFile successfully read! Found {len(df)} rows and {len(df.columns)} columns.")
        
        # Display information
        print("\nColumn names:")
        for i, col in enumerate(df.columns):
            print(f"  Column {i}: {col}")
        
        print(f"\nFirst {min(rows, len(df))} rows:")
        print(df.head(rows))
        
        # Print full details of first row
        print("\nDetail view of first row:")
        first_row = df.iloc[0]
        for col in df.columns:
            print(f"  {col}: {first_row[col]}")
        
        return True
    except Exception as e:
        print(f"Error with openpyxl engine: {e}")
        
        try:
            # Try with different engines
            print(f"\nAttempting with xlrd engine...")
            df = pd.read_excel(file_path, engine='xlrd')
            print(f"File successfully read with xlrd! Found {len(df)} rows and {len(df.columns)} columns.")
            
            # Display information
            print("\nColumn names:")
            for i, col in enumerate(df.columns):
                print(f"  Column {i}: {col}")
            
            print(f"\nFirst {min(rows, len(df))} rows:")
            print(df.head(rows))
            
            return True
        except Exception as e2:
            print(f"Error with xlrd engine: {e2}")
            
            try:
                # Try with odf engine for OpenDocument files
                print(f"\nAttempting with odf engine...")
                df = pd.read_excel(file_path, engine='odf')
                print(f"File successfully read with odf! Found {len(df)} rows and {len(df.columns)} columns.")
                
                # Display information
                print("\nColumn names:")
                for i, col in enumerate(df.columns):
                    print(f"  Column {i}: {col}")
                
                print(f"\nFirst {min(rows, len(df))} rows:")
                print(df.head(rows))
                
                return True
            except Exception as e3:
                print(f"Error with odf engine: {e3}")
                return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view_excel.py <excel_file> [num_rows]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    rows = 5  # Default to 5 rows
    
    if len(sys.argv) > 2:
        try:
            rows = int(sys.argv[2])
        except ValueError:
            print(f"Invalid row count: {sys.argv[2]}. Using default of 5.")
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        sys.exit(1)
    
    success = view_excel_file(file_path, rows)
    if not success:
        print("\nAll attempts to read the Excel file failed.")
        sys.exit(1)