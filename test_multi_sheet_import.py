import unittest
import os
import pandas as pd
import tempfile
from datetime import datetime
from multi_sheet_import import (
    standardize_lottery_type,
    parse_numbers,
    parse_divisions,
    process_row,
    import_multisheet_excel
)

class TestMultiSheetImport(unittest.TestCase):
    """Test suite for the multi-sheet Excel import functionality"""
    
    def test_standardize_lottery_type(self):
        """Test standardizing lottery type names"""
        test_cases = [
            ('lottery', 'Lottery'),
            ('Lottery', 'Lottery'),
            ('LOTTERY', 'Lottery'),
            ('lotto', 'Lottery'),
            ('Lotto', 'Lottery'),
            ('LOTTO', 'Lottery'),
            ('lottery plus 1', 'Lottery Plus 1'),
            ('lotto plus 1', 'Lottery Plus 1'),
            ('lottery plus 2', 'Lottery Plus 2'),
            ('lotto plus 2', 'Lottery Plus 2'),
            ('powerball', 'Powerball'),
            ('Powerball', 'Powerball'),
            ('powerball plus', 'Powerball Plus'),
            ('Powerball Plus', 'Powerball Plus'),
            ('daily lottery', 'Daily Lottery'),
            ('Daily Lottery', 'Daily Lottery'),
            ('daily lotto', 'Daily Lottery'),
            ('Daily Lotto', 'Daily Lottery')
        ]
        
        for input_type, expected_type in test_cases:
            self.assertEqual(standardize_lottery_type(input_type), expected_type)
    
    def test_parse_numbers(self):
        """Test parsing lottery numbers from various formats"""
        test_cases = [
            ('1, 2, 3, 4, 5, 6', [1, 2, 3, 4, 5, 6]),
            ('1,2,3,4,5,6', [1, 2, 3, 4, 5, 6]),
            ('1 2 3 4 5 6', [1, 2, 3, 4, 5, 6]),
            ('1;2;3;4;5;6', [1, 2, 3, 4, 5, 6]),
            ('Example: 1, 2, 3, 4, 5, 6', []),  # Example data should be skipped
            (None, []),
            (123456, [1, 2, 3, 4, 5, 6])
        ]
        
        for input_numbers, expected_numbers in test_cases:
            self.assertEqual(parse_numbers(input_numbers), expected_numbers)
    
    def test_parse_divisions(self):
        """Test parsing division data from structured columns"""
        # Create a sample row with division data
        division_data = {
            'Division 1 Winners': '1',
            'Division 1 Payout': 'R5,000,000.00',
            'Division 2 Winners': '5',
            'Division 2 Payout': 'R250,000.00',
            'Division 3 Winners': 'Example: 10',  # Example data should be skipped
            'Division 3 Payout': 'Example: R10,000.00',  # Example data should be skipped
            # Missing Division 4
            'Division 5 Winners': 100,
            'Division 5 Payout': 500.00
        }
        
        divisions = parse_divisions(division_data)
        
        # Verify Division 1
        self.assertIn('Division 1', divisions)
        self.assertEqual(divisions['Division 1']['winners'], 1)
        self.assertEqual(divisions['Division 1']['prize'], 'R5,000,000.00')
        
        # Verify Division 2
        self.assertIn('Division 2', divisions)
        self.assertEqual(divisions['Division 2']['winners'], 5)
        self.assertEqual(divisions['Division 2']['prize'], 'R250,000.00')
        
        # Division 3 should be skipped as it has example data
        self.assertNotIn('Division 3', divisions)
        
        # Division 4 should be missing as it wasn't in the input
        self.assertNotIn('Division 4', divisions)
        
        # Verify Division 5 with numeric inputs
        self.assertIn('Division 5', divisions)
        self.assertEqual(divisions['Division 5']['winners'], 100)
        self.assertEqual(divisions['Division 5']['prize'], 'R500.00')
    
    def test_process_row(self):
        """Test processing a row from a sheet"""
        # Create a sample row with valid data
        row = pd.Series({
            'Game Name': 'Lottery',
            'Draw Number': '1234',
            'Draw Date': '2025-04-26',
            'Winning Numbers': '1, 2, 3, 4, 5, 6',
            'Bonus Ball': '7',
            'Division 1 Winners': '1',
            'Division 1 Payout': 'R5,000,000.00',
            'Division 2 Winners': '5',
            'Division 2 Payout': 'R250,000.00',
            'Next Draw Date': '2025-05-01',
            'Next Draw Jackpot': 'R10,000,000.00'
        })
        
        # Process the row
        lottery_data = process_row(row, 'Lottery')
        
        # Verify the processed data
        self.assertEqual(lottery_data['lottery_type'], 'Lottery')
        self.assertEqual(lottery_data['draw_number'], '1234')
        self.assertEqual(lottery_data['draw_date'].date(), datetime(2025, 4, 26).date())
        self.assertEqual(lottery_data['numbers'], [1, 2, 3, 4, 5, 6])
        self.assertEqual(lottery_data['bonus_ball'], 7)
        
        # Verify division data
        self.assertIn('divisions', lottery_data)
        self.assertIn('Division 1', lottery_data['divisions'])
        self.assertEqual(lottery_data['divisions']['Division 1']['winners'], 1)
        self.assertEqual(lottery_data['divisions']['Division 1']['prize'], 'R5,000,000.00')
        
        # Verify optional fields
        self.assertEqual(lottery_data['next_draw_date'].date(), datetime(2025, 5, 1).date())
        self.assertEqual(lottery_data['next_jackpot'], 'R10,000,000.00')
    
    def test_skip_example_row(self):
        """Test that rows with example data are skipped"""
        # Create a sample row with example data
        row = pd.Series({
            'Game Name': 'Lottery',
            'Draw Number': 'Example: 1234',
            'Draw Date': 'YYYY-MM-DD',
            'Winning Numbers': 'Example: 1, 2, 3, 4, 5, 6',
            'Bonus Ball': 'Example: 7'
        })
        
        # Process the row - should return None for example data
        lottery_data = process_row(row, 'Lottery')
        self.assertIsNone(lottery_data)
    
    def test_import_multisheet_excel(self):
        """Integration test for the entire import process using a temp file"""
        # Create a temporary Excel file with multiple sheets
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create a writer to save the DataFrame
            writer = pd.ExcelWriter(temp_path, engine='openpyxl')
            
            # Create data for each lottery type
            lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
                            'Powerball', 'Powerball Plus', 'Daily Lottery']
            
            for i, lottery_type in enumerate(lottery_types):
                # Create a DataFrame with one valid row
                df = pd.DataFrame([{
                    'Game Name': lottery_type,
                    'Draw Number': f'{1000 + i}',
                    'Draw Date': '2025-04-26',
                    'Winning Numbers': f'{i+1}, {i+2}, {i+3}, {i+4}, {i+5}, {i+6}',
                    'Bonus Ball': f'{i+7}',
                    'Division 1 Winners': '1',
                    'Division 1 Payout': f'R{1000000*(i+1)}.00',
                    'Division 2 Winners': '5',
                    'Division 2 Payout': f'R{50000*(i+1)}.00'
                }])
                
                # Add example row too (should be skipped)
                example_row = {
                    'Game Name': lottery_type,
                    'Draw Number': 'Example: 1234',
                    'Draw Date': 'YYYY-MM-DD',
                    'Winning Numbers': 'Example: 1, 2, 3, 4, 5, 6',
                    'Bonus Ball': 'Example: 7',
                    'Division 1 Winners': 'Example: 1',
                    'Division 1 Payout': 'Example: R5,000,000.00'
                }
                df = pd.concat([df, pd.DataFrame([example_row])])
                
                # Save to sheet
                df.to_excel(writer, sheet_name=lottery_type, index=False)
            
            # Add instructions sheet
            instructions_df = pd.DataFrame([{'Instructions': 'LOTTERY DATA IMPORT TEMPLATE'}])
            instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
            
            # Save the Excel file
            writer.close()
            
            # Run the import function (without a Flask app context)
            # This will process the data but not save to database
            import_stats = import_multisheet_excel(temp_path)
            
            # Verify results
            self.assertTrue(import_stats['success'])
            self.assertEqual(import_stats['total'], 12)  # 6 games * 2 rows each
            self.assertEqual(import_stats['errors'], 0)
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()