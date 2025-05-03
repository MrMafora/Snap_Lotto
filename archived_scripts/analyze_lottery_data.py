import pandas as pd
import sys
import os

def analyze_lottery_data(excel_path):
    """Analyze lottery data in Excel file with more precise filtering"""
    print(f"Analyzing Excel file: {excel_path}")
    
    try:
        # Check if file exists
        if not os.path.exists(excel_path):
            print(f"File does not exist: {excel_path}")
            return
            
        # Open Excel file with openpyxl engine
        xls = pd.ExcelFile(excel_path, engine='openpyxl')
        sheet_names = xls.sheet_names
        print(f"Found sheets: {sheet_names}")
        
        # Process Lottery sheet (the main sheet)
        if 'Lottery' in sheet_names:
            df = pd.read_excel(excel_path, sheet_name='Lottery', engine='openpyxl')
            
            # Find essential columns
            game_name_col = None
            draw_number_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'game' in col_lower and 'name' in col_lower:
                    game_name_col = col
                elif 'draw' in col_lower and ('number' in col_lower or 'no' in col_lower):
                    draw_number_col = col
            
            if not game_name_col or not draw_number_col:
                print("Could not find essential columns (Game Name and Draw Number)")
                return
                
            print(f"Using columns: Game={game_name_col}, Draw={draw_number_col}")
            
            # Count valid rows by lottery type - only count rows with both game name and draw number
            counts = {}
            valid_rows = []
            
            for idx, row in df.iterrows():
                game_name = row[game_name_col]
                draw_number = row[draw_number_col]
                
                # Skip rows missing either game name or draw number
                if pd.isna(game_name) or pd.isna(draw_number):
                    continue
                    
                # Skip rows with example or note text
                if isinstance(game_name, str) and any(x in game_name.lower() for x in ['example', 'note:', 'includes', 'sheet']):
                    continue
                
                # Normalize game name for consistent counting
                game_name = str(game_name).strip()
                draw_number = str(draw_number).strip()
                
                # Standardize common names for better grouping
                if game_name.lower() == 'lotto':
                    game_name = 'Lottery'
                elif game_name.lower() == 'daily lotto':
                    game_name = 'Daily Lottery'
                elif game_name.lower() == 'powerball':
                    game_name = 'Powerball'
                elif game_name.lower() == 'powerball plus':
                    game_name = 'Powerball Plus'
                
                # Only consider rows that have a numeric draw number
                if not any(c.isdigit() for c in draw_number):
                    continue
                
                valid_rows.append((idx, game_name, draw_number))
                
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
            
            # Now compare with database counts
            print("\nComparing with database counts:")
            from sqlalchemy import create_engine, text
            
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                print("DATABASE_URL environment variable not set")
                return
                
            try:
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    type_query = text("""
                        SELECT lottery_type, COUNT(*) 
                        FROM lottery_result 
                        GROUP BY lottery_type
                        ORDER BY lottery_type
                    """)
                    
                    print("\nDatabase counts:")
                    db_counts = {}
                    for lottery_type, count in conn.execute(type_query):
                        print(f"{lottery_type}: {count}")
                        db_counts[lottery_type] = count
                    
                    # Check for discrepancies
                    print("\nChecking for missing draws...")
                    for game_name, count in counts.items():
                        # Handle naming variations between Excel and DB
                        db_name = game_name
                        if game_name == 'PowerBall':
                            db_name = 'Powerball'
                        elif game_name == 'PowerBall PLUS':
                            db_name = 'Powerball Plus'
                        
                        if db_name in db_counts:
                            if counts[game_name] > db_counts[db_name]:
                                missing = counts[game_name] - db_counts[db_name]
                                print(f"Missing {missing} draws for {db_name}")
                            elif counts[game_name] < db_counts[db_name]:
                                extra = db_counts[db_name] - counts[game_name]
                                print(f"Database has {extra} additional draws for {db_name}")
                        else:
                            print(f"No database entries for {db_name}")
            except Exception as e:
                print(f"Error comparing with database: {str(e)}")
        else:
            print("No 'Lottery' sheet found")
    
    except Exception as e:
        print(f"Error analyzing Excel file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "attached_assets/lottery_data_template_20250429_020457.xlsx"
    
    analyze_lottery_data(excel_path)