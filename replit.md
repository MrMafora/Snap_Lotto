# South African Lottery Ticket Scanner

## Overview
This project is an AI-powered lottery intelligence platform for South African lotteries. Its primary purpose is to process and synchronize South African lottery results, enabling accurate data extraction and display. Key capabilities include AI-powered ticket scanning, comprehensive display of prize divisions, and robust database management of lottery results. The business vision is to be the leading platform for South African lottery intelligence, offering unparalleled accuracy and real-time data to users.

## User Preferences
- **STRICT RULE: NO PLACEHOLDER DATA** - All data must be authentic and extracted from real sources
- Requires authentic data only - no mock or placeholder data ever
- Single-image processing with Gemini 2.5 Pro for maximum accuracy
- Complete lottery result display with all prize divisions and financial details
- All lottery numbers must be extracted using Google Gemini API 2.5 Pro from official screenshots
- **USER REQUIREMENT IMPLEMENTED**: Fixed automation workflow to always follow complete 4-step cycle
  - **STEP 1**: Delete any existing images from screenshots folder (complete cleanup)
  - **STEP 2**: Capture 6 fresh screenshots from all SA lottery websites using Playwright + Chromium
  - **STEP 3**: Extract lottery data with Google Gemini 2.5 Pro AI and update database
  - **STEP 4**: Verify frontend updates with database confirmation
- **USER ISSUE RESOLVED**: Fixed PowerBall numbers appearing in separate row at bottom instead of inline with their respective main numbers
- **USER REQUEST FULFILLED**: Reduced ticket scanner lottery ball sizes from 58px to 40px to match Data Analytics preview card
- **USER ISSUE RESOLVED**: Fixed missing click functionality on "Numbers Not Drawn Recently" (third row) in Data Analytics
- **USER REQUEST FULFILLED**: Reduced hot/cold/absent number ball sizes from 58px to 40px for better space utilization
- **USER FEEDBACK ADDRESSED**: Restored compact match notation (5+PB, 4+B, etc.) instead of verbose descriptions
- **USER ISSUE RESOLVED**: Successfully extracted and added missing Daily Lotto Draw 2325 from July 26, 2025
- **USER REQUEST FULFILLED**: Implemented comprehensive SEO optimization for "lotto" keyword throughout webapp
- **USER ISSUE RESOLVED**: Fixed "View Full Analytics Dashboard" button appearing outside the Data Analytics Preview card
- **USER REQUEST FULFILLED**: Removed height linking between cards to eliminate extra rows and optimize each card individually
- **USER REQUEST FULFILLED**: Optimized Data Analytics sections to ensure all information fits properly within each box
- **USER REQUEST FULFILLED**: Removed horizontal scroll wheel from "Latest Lottery Results" card
- **USER REQUEST FULFILLED**: Reduced space between Draw, Date, and Numbers columns for more efficient layout
- **USER PREFERENCE IMPLEMENTED**: Applied proper text contrast to lottery balls in "Latest Lottery Results" card
- **USER REQUEST FULFILLED**: Removed "BONUS NUMBERS" column from Daily Lottery results display
- **USER REQUEST FULFILLED**: Fixed lottery numbers to display in ascending order (small to large) followed by bonus numbers
- **USER REQUEST FULFILLED**: Removed the entire HISTORICAL RESULTS card section from the results page as requested

## System Architecture
The platform features a modular codebase designed for enhanced security and performance. The UI/UX prioritizes consistency and readability, with optimized ball sizes and clear visual elements across the application.

- **Frontend**: Responsive web interface with mobile-friendly design. Visual consistency across all lottery ball displays (e.g., ticket scanner and analytics cards). Specific CSS classes manage styling for various components.
- **Backend**: Python Flask framework.
- **Database**: PostgreSQL with optimized architecture including 4 performance indexes, cleaned duplicate tables, and major space savings.
- **AI Integration**: Google Gemini 2.5 Pro for AI-powered ticket scanning and data extraction. This involves a comprehensive AI processor (`ai_lottery_processor.py`) that handles full prize division extraction, number recognition, and confidence scoring.
- **Automation Workflow**: A robust 4-step automation process using Playwright + Chromium for screenshot capture, AI processing, database updates, and frontend verification. This includes anti-detection stealth measures and proper browser headers for reliable data fetching.
- **Data Handling**: Strict adherence to authentic data only. Duplicate prevention system implemented to maintain database integrity. PostgreSQL array parsing is used for bonus numbers.
- **Security**: Implemented CSRF protection, comprehensive form validation, secure session settings, rate limiting, input sanitization, and centralized error handling.
- **Performance**: Optimized database queries, critical performance indexes, and a cache manager for speed improvements. Decoupled card heights for optimal content display and layout optimization.
- **Admin Dashboard**: Comprehensive admin interface for data management, system settings, system health monitoring, advertisement management, and automation control.
- **Core Features**:
    - **Ticket Scanner**: Extracts player-selected numbers and detects multiple game types (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2) with multi-line support.
    - **Results Display**: Shows complete lottery results with all prize divisions (8 for Lotto, 9 for Powerball, 4 for Daily Lotto) and financial details. Numbers are sorted in ascending order.
    - **Data Analytics**: Displays hot/cold/absent numbers and frequency charts, all derived from authentic lottery data.
    - **Automated Scheduler**: Daily scheduler system running at 10:30 PM SA time to automatically run the complete 4-step automation process.
    - **Data Preview and Approval System**: Allows review, approval, deeper extraction requests, and rejection of AI-extracted data.

## External Dependencies
- **Google Gemini 2.5 Pro**: Integrated via `GOOGLE_API_KEY_SNAP_LOTTERY` for AI-powered lottery ticket scanning and data extraction.
- **Playwright + Chromium**: Used for automated screenshot capture of South African lottery websites.
- **PostgreSQL**: The primary database for storing and managing all lottery results and related data.
- **psycopg2**: Python adapter for PostgreSQL, used for direct database connections.
- **Flask**: Python web framework forming the backend of the application.
- **Gunicorn**: WSGI HTTP server for running the Flask application in production.
- **SQLAlchemy**: ORM for database interaction (though direct `psycopg2` is used for critical paths to bypass specific issues).
- **Other Python Libraries**: Includes `Flask-WTF` for CSRF protection, `Flask-Login` for user management, and `APScheduler` for task scheduling.