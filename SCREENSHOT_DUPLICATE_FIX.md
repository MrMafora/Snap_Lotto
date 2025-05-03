# Screenshot Duplicate Issue Fix

## Problem Description

We identified an issue where the same lottery data (Powerball Plus) was being saved under two different file names:
1. `Powerball_Plus_Results_20250503_020809.png` (correct)
2. `Powerball_Results_20250503_021230.png` (incorrect)

This misclassification could lead to:
- Confusion in data extraction and reporting
- Incorrect lottery type classification
- Duplicate data in the system
- Potential errors in statistics and analysis

## Solution Implemented

We've developed a comprehensive solution to identify and fix these issues:

1. **Detection Scripts**:
   - Created `check_asset_duplicates.py` to identify duplicates using image hash comparison
   - Script computes a perceptual hash for each image and groups them by similarity
   - Detects files with the same content but different names/classifications

2. **Fixing Scripts**:
   - Created `fix_screenshot_names.py` to remove incorrectly named duplicate files
   - Focuses on resolving PowerBall vs PowerBall Plus misclassifications

3. **Scheduled Validation**:
   - Created `scheduled_screenshot_validation.py` to run regular validations
   - Can be scheduled to run after screenshot captures (3 AM daily)
   - Automatically detects and fixes classification issues in the database

## Technical Approach

The solution uses image processing techniques:
- **Perceptual Hash**: Computes a "fingerprint" for each image that stays consistent even with minor pixel-level differences
- **Classification Heuristics**: Uses known patterns and filenames to determine correct lottery type
- **Database Integration**: Updates database records to ensure consistent lottery type classification

## Manual Testing Process

When fixing the issue, we:
1. First ran checks in dry-run mode to identify the problem files
2. Confirmed that the files contained identical PowerBall Plus content
3. Applied the fix to remove the incorrect file (keeping the correctly named one)
4. Verified that the duplicate was properly removed

## Prevention Measures

To prevent this issue from recurring:
- The scheduled validation will automatically fix any future misclassifications
- The system now checks for PowerBall Plus content explicitly when classifying screenshots
- Known correct hashes are stored for reference

## Future Improvements

The system could be enhanced with:
- Full OCR integration to improve lottery type detection accuracy
- Expanded hash database of known lottery type screenshots
- Additional validation rules for other lottery types