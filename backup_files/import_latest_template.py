
import pandas as pd
import os
from datetime import datetime
import logging
from models import LotteryResult, ImportHistory, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_latest_template():
    """Import lottery data from the latest template file"""
    try:
        # Find latest template file
        template_dir = "attached_assets"
        template_files = [f for f in os.listdir(template_dir) 
                         if f.endswith('.xlsx') and 'template' in f.lower()]
        
        if not template_files:
            return {
                'success': False,
                'error': 'No template files found'
            }
            
        latest_file = max(template_files, 
                         key=lambda x: os.path.getmtime(os.path.join(template_dir, x)))
        file_path = os.path.join(template_dir, latest_file)
        
        # Import data from template
        stats = {
            'total': 0,
            'added': 0,
            'updated': 0,
            'errors': 0
        }
        
        # Read Excel file
        xls = pd.ExcelFile(file_path)
        
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name)
                
                for _, row in df.iterrows():
                    try:
                        stats['total'] += 1
                        
                        # Process row data
                        draw_number = str(row.get('Draw Number', ''))
                        draw_date = row.get('Draw Date')
                        
                        if pd.isna(draw_number) or pd.isna(draw_date):
                            continue
                            
                        # Create or update result
                        result = LotteryResult.query.filter_by(
                            lottery_type=sheet_name,
                            draw_number=draw_number
                        ).first()
                        
                        if result:
                            stats['updated'] += 1
                        else:
                            result = LotteryResult(
                                lottery_type=sheet_name,
                                draw_number=draw_number
                            )
                            stats['added'] += 1
                            
                        # Update result data
                        result.draw_date = draw_date
                        result.numbers = row.get('Numbers', '')
                        result.bonus_numbers = row.get('Bonus Numbers', '')
                        
                        db.session.add(result)
                        
                    except Exception as row_error:
                        logger.error(f"Error processing row: {str(row_error)}")
                        stats['errors'] += 1
                        
            except Exception as sheet_error:
                logger.error(f"Error processing sheet {sheet_name}: {str(sheet_error)}")
                stats['errors'] += 1
                
        # Commit changes
        db.session.commit()
        
        # Create import history record
        history = ImportHistory(
            import_type='template',
            file_name=latest_file,
            records_added=stats['added'],
            records_updated=stats['updated'],
            total_processed=stats['total'],
            errors=stats['errors']
        )
        db.session.add(history)
        db.session.commit()
        
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Error importing template: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
