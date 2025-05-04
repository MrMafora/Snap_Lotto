# Correlation Analysis Fix

## Issue Description
The correlation analysis tab in the lottery analysis dashboard was failing with the error: "Analysis failed: cannot reindex on an axis with duplicate labels". This was happening because the `reindex` operation in pandas was encountering duplicate dates in the lottery draw data.

## Root Causes
1. Multiple lottery draws occurring on the same date caused duplicate indices in the dataframe
2. The `reindex` operation in pandas fails when there are duplicate indices in the source dataframe
3. No proper error handling was in place to handle this scenario

## Fix Implementation

### 1. Handle Duplicate Date Indices
Added code to detect and handle duplicate dates before setting the index:

```python
# If there are multiple draws on the same date, use the latest one
if lt_df['draw_date'].duplicated().any():
    # Sort by draw_date and any other relevant columns (e.g., draw_number if available)
    sort_cols = ['draw_date']
    if 'draw_number' in lt_df.columns:
        sort_cols.append('draw_number')
    
    # Sort and drop duplicates keeping the last occurrence
    lt_df = lt_df.sort_values(by=sort_cols).drop_duplicates(subset=['draw_date'], keep='last')
```

### 2. Added Fallback Mechanism
Implemented a try-catch block with a fallback approach for reindexing when the primary method fails:

```python
try:
    # Use reindex with a clean index to avoid duplicate issues
    temp_df[f'{lt}_{col}'] = lt_df[col].reindex(temp_df.index, method='ffill')
except Exception as e:
    logger.warning(f"Could not reindex column {col} for {lt}: {e}")
    # Alternative approach: use a safer method with forward fill
    merged = pd.DataFrame({col: lt_df[col]})
    merged = merged.reset_index()
    merged = merged.drop_duplicates(subset=['draw_date'], keep='last')
    merged = merged.set_index('draw_date')
    temp_df[f'{lt}_{col}'] = merged[col].reindex(temp_df.index, method='ffill')
```

### 3. Improved Sorting Strategy
Enhanced the sorting logic to ensure that when there are multiple draws on the same date, we consistently use the latest draw data based on draw number when available:

```python
# Sort by draw_date and any other relevant columns (e.g., draw_number if available)
sort_cols = ['draw_date']
if 'draw_number' in lt_df.columns:
    sort_cols.append('draw_number')
```

## Enhanced Robustness
These changes make the correlation analysis much more robust, as it can now handle:
- Multiple lottery draws on the same date
- Missing or incorrect draw data
- Inconsistencies in the dataset

The fix also provides detailed warning logs to help identify any remaining issues with specific lottery types or columns.