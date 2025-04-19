# Pattern Analysis Fix

## Issue Description
The pattern analysis tab in the lottery analysis dashboard was not displaying properly due to errors in handling missing data. The Principal Component Analysis (PCA) was failing with the error: "PCA does not accept missing values encoded as NaN natively."

## Root Causes
1. The code was not properly preprocessing the lottery number data before performing PCA
2. There were NaN values in the input data matrix that caused PCA to fail
3. The drawing of lottery numbers on the pattern visualization wasn't handling the filtered dataset correctly

## Fix Implementation

### 1. Data Preprocessing
Modified the code to properly detect and handle missing values:
```python
# Check if we have missing values
if number_df.isna().any().any():
    # Filter out rows with NaN values
    complete_rows = number_df.dropna(how='any')
    
    # If we don't have enough data after filtering, skip this lottery type
    if len(complete_rows) < 5:
        logger.warning(f"Not enough complete data for {lt} after removing NaN values")
        results[lt] = {
            'error': f"Not enough complete data after removing rows with missing values"
        }
        continue
        
    # Use only complete rows for analysis
    features = complete_rows.values
    # Keep track of indices for later when adding draw numbers
    valid_indices = complete_rows.index
else:
    # All data is complete, proceed normally
    features = number_df.values
    valid_indices = number_df.index
```

### 2. Drawing Number Mapping
Enhanced the code to correctly map draw numbers from the original dataframe to the filtered dataset:
```python
# Add draw numbers safely, taking into account we might be using a subset of rows
if 'draw_number' in lt_df.columns:
    # Map original dataframe indices to PCA dataframe rows
    draw_numbers = []
    for idx in valid_indices:
        if idx < len(lt_df) and pd.notna(lt_df.loc[idx, 'draw_number']):
            draw_numbers.append(str(lt_df.loc[idx, 'draw_number']))
        else:
            draw_numbers.append(f"Draw {idx}")
            
    # If we have the right number of draw numbers, use them
    if len(draw_numbers) == len(pca_df):
        pca_df['Draw'] = draw_numbers
    else:
        # Fallback to generic numbering if something went wrong
        pca_df['Draw'] = [f"Draw {i+1}" for i in range(len(pca_df))]
else:
    # Use row index as a fallback for missing draw numbers
    pca_df['Draw'] = [f"Draw {i+1}" for i in range(len(pca_df))]
```

## Additional Considerations
- The fix properly handles both scenarios where there are no missing values and where some rows have missing values
- Additional logging was added to help diagnose issues with insufficient data after filtering
- Graceful degradation is implemented by providing a user-friendly error message when there's not enough data
- The code maintains the ability to generate visualizations for each lottery type independently