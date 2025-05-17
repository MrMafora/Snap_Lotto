# Import History Fix Documentation

## Problem: Excel Row 2 Importing Issue and Import History Tracking

Several issues were identified in the import history system:

1. Excel row 2 (index 1) was being skipped during Excel imports
2. ImportHistory records existed without proper association to lottery results
3. Model inconsistency (`ImportDetail` vs `ImportedRecord`)
4. Inconsistent import record labeling

## Solution

### Fix 1: Excel Row 2 Import Issue
- Created `fix_row2.py` script to specifically import row 2 data from Excel
- The script uses `iloc[0]` to directly access the second row (index 1)
- Added error handling to ensure data validity
- Created proper import history records during the fix

### Fix 2: Import History Associations
- Created `fix_import_history.py` script to standardize import records
- Updated all records with source_url = 'row2-fix-script' to 'imported-from-excel'
- Set consistent ocr_provider = 'manual-import' and ocr_model = 'excel-spreadsheet'
- Created `ImportedRecord` associations between ImportHistory and LotteryResult

### Fix 3: Model Consistency
- Standardized all references from `ImportDetail` to `ImportedRecord`
- Updated import scripts to use the correct model name
- Database model uses proper foreign keys and relationships

### Database Verification
- Import 26 is now correctly associated with Draw 2535 for Lotto, Lotto Plus 1, and Lotto Plus 2
- All imported data points to consistent source identifiers

### Future Prevention
- Updated import_excel.py with permanent fixes to ensure row 2 is never skipped
- All imports now create both ImportHistory and ImportedRecord entries
- Standardized labeling ensures consistent tracking

## Technical Implementation
The fix creates proper associations between imports and lottery results by:

1. Identifying ImportHistory records with certain import types
2. Finding lottery results with specific draw numbers
3. Creating ImportedRecord rows to link the two
4. Standardizing metadata fields for consistency

This ensures proper data provenance tracking and will make future Excel imports reliable.