#!/usr/bin/env python
"""
Script to fix import history records by adding proper details.
This will update our existing row2-fix-script import history.
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_import_history():
    """Fix existing import history records to have proper associations"""
    try:
        # This must be run from within Flask context
        from models import db, LotteryResult, ImportHistory, ImportedRecord
        from flask import current_app
        
        # First, let's identify any import history with 'row2-fix-script' type or 'Excel' type without details
        fix_script_imports = ImportHistory.query.filter((ImportHistory.import_type == 'row2-fix-script') | 
                                           (ImportHistory.import_type == 'Excel')).all()
        
        logger.info(f"Found {len(fix_script_imports)} imports to process")
        
        if not fix_script_imports:
            logger.info("No imports to fix")
            return True
            
        for import_record in fix_script_imports:
            # 1. Ensure import_type is 'Excel'
            if import_record.import_type != 'Excel':
                import_record.import_type = 'Excel'
                db.session.add(import_record)
                db.session.commit()
                logger.info(f"Updated import {import_record.id} type to 'Excel'")
            
            # 2. Find lottery results with draw number 2535 (the problematic row)
            results = LotteryResult.query.filter_by(draw_number='2535').all()
            logger.info(f"Found {len(results)} lottery results with draw number 2535")
            
            if not results:
                logger.warning(f"No lottery results found with source_url='row2-fix-script' for import {import_record.id}")
                continue
                
            for result in results:
                # 3. Update the source_url and provider fields
                result.source_url = 'imported-from-excel'
                result.ocr_provider = 'manual-import'
                result.ocr_model = 'excel-spreadsheet'
                db.session.add(result)
                
                # 4. Check if import detail already exists
                existing_detail = ImportedRecord.query.filter_by(
                    import_id=import_record.id,
                    lottery_result_id=result.id
                ).first()
                
                if existing_detail:
                    logger.info(f"Import detail already exists for import {import_record.id} and result {result.id}")
                    continue
                
                # 5. Create import detail record
                import_detail = ImportedRecord(
                    import_id=import_record.id,
                    lottery_result_id=result.id,
                    lottery_type=result.lottery_type,
                    draw_number=result.draw_number,
                    draw_date=result.draw_date,
                    is_new=True
                )
                db.session.add(import_detail)
                logger.info(f"Created detail record linking import {import_record.id} with lottery result {result.id}")
            
            db.session.commit()
            logger.info(f"Successfully updated import {import_record.id} and its lottery results")
            
        return True
    except Exception as e:
        logger.error(f"Error fixing import history: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Usage script with Flask app context
if __name__ == "__main__":
    print("This script must be run from a Flask context")
    print("To run, execute the following from a Python shell:")
    print("from fix_import_history import fix_import_history")
    print("from main import app")
    print("with app.app_context():")
    print("    fix_import_history()")