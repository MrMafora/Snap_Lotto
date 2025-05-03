# ⚠️ CRITICAL EXCEL IMPORT WARNING ⚠️

## Important Notice for All Developers

### Excel Import Data Loss Prevention

A critical bug was identified and fixed on April 25, 2025 related to importing lottery data from Excel spreadsheets. The issue caused the first 4 rows of valuable lottery data to be skipped during import, resulting in missing records in the database.

### Root Cause:
- Excel import code was skipping multiple rows (first 4 rows) during spreadsheet processing
- This caused recent lottery results to be missed entirely
- The issue was revealed when data from the spreadsheet couldn't be found in the database

### The Fix:
1. Modified `import_excel.py` to only skip the header row (row 0) during import
2. Added explicit warning messages in logs to prevent future regressions
3. Enhanced `import_latest_spreadsheet.py` with additional error checking and validation
4. Updated `import_snap_lotto_data.py` with consistent row handling approach
5. Added warning comments in all relevant code sections to prevent reintroduction of the bug

### CRITICAL GUIDELINE FOR ALL DEVELOPERS:
- **NEVER SKIP MORE THAN 1 ROW** when importing lottery data from Excel
- The first row (row 0) is the header, all subsequent rows contain valuable lottery data
- Rows 1-4 typically contain the most recent lottery results, which are critical
- Always verify import results with explicit logging of before/after record counts

### Affected Files:
- `import_excel.py`
- `import_snap_lotto_data.py`
- `import_latest_spreadsheet.py`

### Testing:
Always verify a successful import by:
1. Checking the first row of data in the Excel file
2. Confirming that data exists in the database after import
3. Checking the logs for accurate record counts

**Remember: Data integrity is critical to our application's value proposition. Never compromise on complete data import.**