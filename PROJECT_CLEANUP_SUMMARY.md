# Snap Lotto Project Cleanup Summary

## Project Overview
Snap Lotto is a Python-powered lottery data intelligence platform that leverages advanced AI and machine learning to transform lottery ticket scanning and result analysis in South Africa. The application provides real-time lottery results, ticket scanning, and predictive analysis.

## Cleanup Actions Completed

### 1. Project Structure Optimization
- Identified and documented essential files in `essential_files_list.txt`
- Permanently deleted 100+ unnecessary and redundant scripts
- Organized remaining files by function (core application, data processing, utilities)

### 2. Database Configuration
- Fixed database configuration to properly use PostgreSQL (previously had SQLite references)
- Addressed connection pooling issues by optimizing connection parameters
- Fixed `SQLALCHEMY_DATABASE_URI` to properly handle both production and development environments

### 3. Web Server Configuration
- Simplified gunicorn configuration to eliminate redundant port proxy processes
- Configured direct binding to port 5000 (Replit handles forwarding)
- Removed all custom port proxy implementations that were causing conflicts

### 4. Screenshot Management
- Fixed screenshot synchronization across all 12 lottery types
- Ensured proper timestamp updates to prevent duplicate screenshots
- Implemented proper file format handling (PNG only)

### 5. Health Monitoring
- Addressed health monitor warnings about missing ports
- Improved error handling and reporting
- Enhanced database connection validation

## Essential Files Documentation

### Core Application Files
- `main.py` - Core Flask application with routes and admin functionality
- `models.py` - Database models for all application data
- `config.py` - Configuration settings including database connections
- `gunicorn.conf.py` - Web server configuration

### Task Management
- `scheduler.py` - Scheduled task management
- `automated_lottery_extraction.py` - Automated lottery data extraction
- `screenshot_manager.py` - Screenshot capture and management

### Data Processing
- `data_aggregator.py` - Processes and aggregates lottery results
- `lottery_analysis.py` - Analysis and prediction functionality
- `ocr_processor.py` - OCR processing using Anthropic API
- `import_excel.py` - Excel data import functionality
- `import_snap_lotto_data.py` - Lottery data import functionality
- `import_latest_template.py` - Template importing utility
- `import_latest_spreadsheet.py` - Spreadsheet importing utility
- `import_missing_draws.py` - Utility to import missing lottery draws

### Support Functions
- `excel_date_utils.py` - Excel date parsing utilities
- `create_template.py` - Excel template generation
- `sync_all_timestamps.py` - Screenshot timestamp synchronization
- `csrf_fix.py` - Enhanced CSRF protection
- `health_monitor.py` - System health monitoring
- `ad_management.py` - Advertisement management system

## Essential Folders
- `static/` - Static assets (CSS, JS, images)
- `templates/` - HTML templates
- `screenshots/` - Screenshot storage
- `uploads/` - User uploaded files
- `attached_assets/` - Additional resources
- `instance/` - Instance-specific files

## Configuration Files
- `.env` - Environment variables
- `.replit` - Replit configuration
- `.replit-deployment` - Deployment configuration
- `.replit-ports` - Port configuration
- `.replit-run-command` - Run command configuration
- `Procfile` - Process file for deployments
- `pyproject.toml` - Python project configuration

## Ongoing Improvements
- Continue refactoring code for better maintainability
- Implement proper error handling throughout the application
- Enhance documentation for new developers
- Address remaining LSP issues in key files