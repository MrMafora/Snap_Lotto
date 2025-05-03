#!/usr/bin/env python3
"""
Test script to verify excel import with all lottery types
"""

import pandas as pd
import json
import os
from datetime import datetime
import sys

# Set up logging to console
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_lottery_type(lottery_type):
    """
    Normalize lottery type names, prioritizing "Lottery" terminology.
    
    Args:
        lottery_type (str): The lottery type name
        
    Returns:
        str: Normalized lottery type
    """
    if not lottery_type:
        return "Unknown"
    
    # First, handle exact matches for special cases
    cleaned_type = str(lottery_type).strip()
    
    # Handle the exact matches from the Excel file
    if cleaned_type == 'PowerBall':
        return 'Powerball'
    elif cleaned_type == 'PowerBall PLUS':
        return 'Powerball Plus'
    elif cleaned_type == 'Lottery Plus 1':
        return 'Lottery Plus 1'
    elif cleaned_type == 'Lottery Plus 2':
        return 'Lottery Plus 2'
    elif cleaned_type == 'Daily Lottery':
        return 'Daily Lottery'
    
    # Convert to uppercase for case-insensitive matching
    upper_type = cleaned_type.upper()
    
    # Prioritize "Lottery" terminology
    if upper_type == 'LOTTO' or upper_type == 'LOTTERY':
        return 'Lottery'
    elif 'LOTTERY PLUS 1' in upper_type or 'LOTTO PLUS 1' in upper_type:
        return 'Lottery Plus 1'
    elif 'LOTTERY PLUS 2' in upper_type or 'LOTTO PLUS 2' in upper_type:
        return 'Lottery Plus 2' 
    elif 'POWERBALL PLUS' in upper_type or 'POWERBALL PLUS' in upper_type:
        return 'Powerball Plus'
    elif 'POWERBALL' in upper_type:
        return 'Powerball'
    elif 'DAILY LOTTERY' in upper_type or 'DAILY LOTTO' in upper_type:
        return 'Daily Lottery'
        
    # If no match, return original with proper capitalization
    return cleaned_type

def test_excel_import(excel_path):
    """
    Analyze the Excel file for lottery types and verify the import would work correctly.
    
    Args:
        excel_path (str): Path to Excel file
        
    Returns:
        dict: Analysis results
    """
    stats = {
        "total_processed": 0,
        "lottery_types": {}
    }
    
    try:
        # Get list of sheets in Excel file
        xlsx = pd.ExcelFile(excel_path)
        sheets = [sheet for sheet in xlsx.sheet_names if sheet.lower() not in ['instructions', 'info', 'readme']]
        
        logger.info(f"Processing Excel file: {excel_path}")
        logger.info(f"Found {len(sheets)} sheets: {', '.join(sheets)}")
        
        # Process each sheet
        for sheet in sheets:
            try:
                logger.info(f"Processing sheet: {sheet}")
                
                # Try to determine lottery type from sheet name
                sheet_lottery_type = normalize_lottery_type(sheet)
                logger.info(f"Sheet name suggests lottery type: {sheet_lottery_type}")
                
                # Read sheet
                df = pd.read_excel(excel_path, sheet_name=sheet)
                
                # Skip empty sheets
                if df.empty:
                    logger.info(f"Sheet {sheet} is empty, skipping")
                    continue
                
                # Replace NaN with None
                df = df.replace({pd.NA: None})
                
                # Group by Game Name to count draws by lottery type
                if 'Game Name' in df.columns:
                    game_name_groups = df.groupby('Game Name').size().reset_index(name='count')
                    logger.info(f"Found {len(game_name_groups)} unique lottery types in sheet {sheet}")
                    
                    for _, row in game_name_groups.iterrows():
                        game_name = row['Game Name']
                        count = row['count']
                        
                        if pd.isna(game_name) or game_name == 'Game Name' or 'Sheet' in str(game_name) or 'Note' in str(game_name):
                            continue
                            
                        lottery_type = normalize_lottery_type(game_name)
                        
                        # Add to stats
                        if lottery_type not in stats["lottery_types"]:
                            stats["lottery_types"][lottery_type] = 0
                        stats["lottery_types"][lottery_type] += count
                        stats["total_processed"] += count
                        
                        # Get the highest draw number for this lottery type
                        lottery_type_df = df[df['Game Name'] == game_name]
                        if not lottery_type_df.empty and 'Draw Number' in lottery_type_df.columns:
                            try:
                                latest_draw = lottery_type_df.sort_values('Draw Number', ascending=False).iloc[0]
                                draw_number = latest_draw['Draw Number']
                                
                                # Get the winning numbers
                                winning_numbers = None
                                if 'Winning Numbers (Numerical)' in latest_draw:
                                    winning_numbers = latest_draw['Winning Numbers (Numerical)']
                                
                                # Get the bonus ball
                                bonus_ball = None
                                if 'Bonus Ball' in latest_draw:
                                    bonus_ball = latest_draw['Bonus Ball']
                                
                                logger.info(f"Latest draw for {lottery_type}: #{draw_number}, " 
                                           f"Numbers: {winning_numbers}, Bonus: {bonus_ball}")
                            except Exception as e:
                                logger.error(f"Error processing latest draw for {lottery_type}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error processing sheet {sheet}: {str(e)}")
        
        logger.info(f"Import analysis completed: {stats}")
        
    except Exception as e:
        logger.error(f"Error analyzing Excel file: {str(e)}")
    
    return stats

if __name__ == "__main__":
    # Get file path from command line
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "attached_assets/lottery_data_template_20250502_033148.xlsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    # Analyze data
    stats = test_excel_import(file_path)
    
    # Print summary
    print("\n=== IMPORT ANALYSIS SUMMARY ===")
    print(f"Total processed: {stats['total_processed']}")
    print("\nBy lottery type:")
    for lottery_type, count in stats['lottery_types'].items():
        print(f"  {lottery_type}: {count} draws")