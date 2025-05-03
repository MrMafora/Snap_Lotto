import pandas as pd
import sys

def count_excel_data(excel_path):
    """Count lottery draws by type in Excel file"""
    print(f"Analyzing Excel file: {excel_path}")
    
    try:
        # Open Excel file with openpyxl engine
        xls = pd.ExcelFile(excel_path, engine='openpyxl')
        sheet_names = xls.sheet_names
        print(f"Found sheets: {sheet_names}")
        
        # Process Lottery sheet (the main sheet)
        if 'Lottery' in sheet_names:
            df = pd.read_excel(excel_path, sheet_name='Lottery', engine='openpyxl')
            
            # Find game name column
            game_name_col = None
            for col in df.columns:
                if 'game' in str(col).lower() and 'name' in str(col).lower():
                    game_name_col = col
                    break
            
            if not game_name_col:
                print("Could not find Game Name column")
                return
                
            print(f"Using column: {game_name_col}")
            
            # Count valid rows by lottery type (exclude examples and empty rows)
            counts = {}
            
            for _, row in df.iterrows():
                game_name = row[game_name_col]
                
                # Skip empty or example rows
                if pd.isna(game_name) or not game_name:
                    continue
                    
                if isinstance(game_name, str) and 'example' in game_name.lower():
                    continue
                
                # Normalize game name for consistent counting
                game_name = str(game_name).strip()
                
                # Standardize common names
                if game_name.lower() == 'lotto':
                    game_name = 'Lottery'
                elif game_name.lower() == 'daily lotto':
                    game_name = 'Daily Lottery'
                
                if game_name not in counts:
                    counts[game_name] = 0
                counts[game_name] += 1
                
            # Print counts
            print("\nCounts by lottery type:")
            total = 0
            for game_name, count in sorted(counts.items()):
                print(f"{game_name}: {count}")
                total += count
            
            print(f"\nTotal valid draws: {total}")
        else:
            print("No 'Lottery' sheet found")
    
    except Exception as e:
        print(f"Error analyzing Excel file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "attached_assets/lottery_data_template_20250429_020457.xlsx"
    
    count_excel_data(excel_path)