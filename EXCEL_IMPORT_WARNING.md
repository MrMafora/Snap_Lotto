# Excel Import Special Case Handling

## Issue Description

When importing Excel lottery data files, there's a special case for row entries like "Lottery 2536" where:
1. The lottery type and draw number are combined into a single cell
2. The lottery type needs to be normalized to just "Lottery"
3. The draw number (2536) needs to be extracted and used as the actual draw number

## Changes Made

We've updated the Excel import functionality to handle this special case:

1. Added regex pattern matching to detect formats like "Lottery 2536" or "Lotto 2536" 
2. Added extraction logic to separate the lottery type and draw number
3. Improved logging to track what's happening during the import process
4. Ensured row 2 data (the first data row) is properly imported without being skipped
5. Updated the normalize_lottery_type function to correctly handle "Lottery 2536" format

## How to Test

We've created a special test script, `fix_row2.py`, to verify the fix:

```bash
# Run the test script on your Excel file
./fix_row2.py path/to/excel_file.xlsx
```

The script specifically checks for the "Lottery 2536" pattern and verifies:
- That it correctly extracts "Lottery" as the game type
- That it correctly extracts "2536" as the draw number
- That all the data from row 2 is properly processed

## Understanding the Code Changes

The key changes were made in two files:

1. **improved_excel_import.py**:
   - Added detection and extraction in the `process_row` function
   - Improved logging for debugging row data issues
   - Fixed issue with skipping row 2 data

2. **integrate_excel_import.py**:
   - Updated `normalize_lottery_type` to handle the embedded draw number case
   - Ensured consistent naming convention (using "Lottery" instead of "Lotto")

## Avoiding Future Issues

To ensure consistent data importing:
1. Try to use a consistent format in Excel spreadsheets
2. Use separate columns for lottery type and draw number
3. Always include headers in the Excel file
4. Use the standard lottery type names: "Lottery", "Lottery Plus 1", etc.

If you see missing data after an import, you can use the `fix_row2.py` script to diagnose the issue.