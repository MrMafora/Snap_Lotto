import pandas as pd
import os

def create_template(output_path):
    """
    Create a properly formatted Excel template for lottery data import with an empty worksheet.
    
    Args:
        output_path (str): Path to save the Excel file
        
    Returns:
        bool: Success status
    """
    # Create Excel writer
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    
    # Create empty DataFrames for each lottery type
    lottery_types = [
        'Lotto',
        'Lotto Plus 1',
        'Lotto Plus 2',
        'Powerball',
        'Powerball Plus',
        'Daily Lotto'
    ]
    
    # Create columns that match our expected format
    columns = [
        'Game Name',
        'Draw Number',
        'Draw Date',
        'Winning Numbers',
        'Bonus Ball',
        'Division 1 Winners',
        'Division 1 Payout',
        'Division 2 Winners',
        'Division 2 Payout',
        'Division 3 Winners',
        'Division 3 Payout',
        'Division 4 Winners',
        'Division 4 Payout',
        'Division 5 Winners',
        'Division 5 Payout',
        'Next Draw Date',
        'Next Draw Jackpot'
    ]
    
    # Create empty DataFrames for each lottery type with the columns
    for lottery_type in lottery_types:
        # Create an empty DataFrame with our columns
        df = pd.DataFrame(columns=columns)
        
        # Add a couple of example rows to show the format
        example_data = {
            'Game Name': lottery_type,
            'Draw Number': f'Example: 1234',
            'Draw Date': 'YYYY-MM-DD',
            'Winning Numbers': 'Example: 1, 2, 3, 4, 5, 6',
            'Bonus Ball': 'Example: 7',
            'Division 1 Winners': 'Example: 1',
            'Division 1 Payout': 'Example: R5,000,000.00',
            'Division 2 Winners': 'Example: 5',
            'Division 2 Payout': 'Example: R250,000.00',
        }
        df = pd.concat([df, pd.DataFrame([example_data])], ignore_index=True)
        
        # Write to Excel
        df.to_excel(writer, sheet_name=lottery_type, index=False)
    
    # Create a main sheet with instructions
    instructions = pd.DataFrame({
        'Instructions': [
            'LOTTERY DATA IMPORT TEMPLATE',
            '',
            'HOW TO USE THIS TEMPLATE:',
            '1. Each sheet represents a different lottery game',
            '2. Fill in the actual draw information on each sheet',
            '3. Save the file',
            '4. Upload through the Import Data page',
            '',
            'REQUIRED FIELDS:',
            '- Game Name: The name of the lottery game',
            '- Draw Number: The official draw number',
            '- Draw Date: The date of the draw (YYYY-MM-DD format)',
            '- Winning Numbers: Comma-separated list of winning numbers',
            '',
            'OPTIONAL FIELDS:',
            '- Bonus Ball: The bonus ball for games that have one',
            '- Division X Winners: Number of winners in each division',
            '- Division X Payout: Prize amount for each division',
            '- Next Draw Date: Date of the next scheduled draw',
            '- Next Draw Jackpot: Estimated jackpot for the next draw',
        ]
    })
    
    instructions.to_excel(writer, sheet_name='Instructions', index=False)
    
    # Save the Excel file
    writer.close()
    
    return os.path.exists(output_path)

# Create the template in both the attached_assets and uploads directory
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Create in attached_assets
create_template('attached_assets/lottery_data_template_new.xlsx')

# Also create in uploads for testing
create_template('uploads/lottery_data_import.xlsx')

print("Templates created successfully!")