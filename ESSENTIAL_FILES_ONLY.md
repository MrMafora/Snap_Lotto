# Essential Files for Snap Lotto Platform

## CORE APPLICATION FILES (Keep These)
✓ main.py - Main application entry point  
✓ config.py - Configuration settings
✓ models.py - Database models
✓ lottery_analysis.py - Core lottery analysis functionality
✓ ocr_processor.py - AI ticket scanning feature
✓ health_monitor.py - System monitoring
✓ gunicorn.conf.py - Server configuration

## DIRECTORIES TO KEEP
✓ templates/ - HTML templates
✓ static/ - CSS, JavaScript, images
✓ instance/ - Database files
✓ attached_assets/ - User data and lottery templates
✓ uploads/ - User uploaded ticket images

## STATUS AFTER CLEANUP
- Removed: node_modules, __pycache__, logs, archived_scripts
- Removed: All test_, debug_, fix_, simple_ files
- Removed: Duplicate backup and experimental files
- Current: ~8,000 files (mostly in .cache from dependencies)
- Target: Focus on core functionality only