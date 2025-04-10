# Snap Lotto Application Structure

## Core Files

- `main.py` - Application entry point, imports the Flask app and runs it
- `app.py` - Main Flask application with routes and business logic
- `config.py` - Configuration settings and environment variables
- `models.py` - Database models and ORM definitions

## Data Processing

- `data_aggregator.py` - Aggregates lottery results from various sources
- `ocr_processor.py` - Processes images using Claude AI to extract lottery data
- `ticket_scanner.py` - Logic for scanning tickets and checking for winning numbers

## Screenshot Management

- `screenshot_manager.py` - Base screenshot manager interface
- `screenshot_manager_light.py` - Lightweight screenshot manager (no Playwright)
- `screenshot_manager_playwright.py` - Full-featured screenshot manager with Playwright

## Scheduling

- `scheduler.py` - Task scheduling for automated data collection

## DB Management

- `db_models.py` - Database model definitions
- `import_excel.py` - Import lottery data from Excel spreadsheets
- `import_snap_lotto_data.py` - Specialized importer for Snap Lotto data format

## Testing and Utils

- `check_html.py` - Utility for examining HTML structure
- `examine_excel.py` - Utility for examining Excel structure
- `fix_daily_lotto_bonus.py` - Utility to fix data inconsistencies

## Front-end Assets

- `static/` - Static files (CSS, JavaScript, images)
  - `static/js/ticket_scanner.js` - Ticket scanning UI logic
  - `static/js/ads.js` - Advertisement display management
  - `static/css/custom.css` - Custom styles

- `templates/` - Jinja2 HTML templates
  - `templates/base.html` - Base template for site-wide layout
  - `templates/ticket_scanner_new.html` - Ticket scanner UI
  - `templates/results.html` - Results display page