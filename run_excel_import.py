#!/usr/bin/env python3
"""
Script to run excel import with the main application
"""
import sys
import os
from main import app
from direct_excel_import import direct_excel_import

def main():
    # Get file path from command line
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "attached_assets/lottery_data_template_20250502_033148.xlsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    # Import data
    print(f"Importing data from {file_path}...")
    stats = direct_excel_import(file_path, app)
    
    # Print summary
    print("\n=== IMPORT SUMMARY ===")
    print(f"Total processed: {stats['total_processed']}")
    print(f"Sheets processed: {stats['sheets_processed']}")
    print(f"New records: {stats['new_records']}")
    print(f"Updated records: {stats['updated_records']}")
    print(f"Errors: {stats['errors']}")
    print("\nBy lottery type:")
    for lottery_type, type_stats in stats['lottery_types'].items():
        print(f"  {lottery_type}: {type_stats['processed']} processed "
             f"({type_stats['new']} new, {type_stats['updated']} updated, "
             f"{type_stats['errors']} errors)")

if __name__ == "__main__":
    main()