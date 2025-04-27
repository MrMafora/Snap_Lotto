import pandas as pd

try:
    df = pd.read_excel('./attached_assets/lottery_test_data.xlsx', engine='openpyxl')
    print('File is valid')
    print(f'Columns: {df.columns.tolist()}')
    print(f'Number of rows: {len(df)}')
except Exception as e:
    print(f'Error reading file: {e}')