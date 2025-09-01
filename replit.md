# South African Lottery Ticket Scanner

## Overview
This project is an AI-powered lottery intelligence platform for South African lotteries. Its main purpose is to process and synchronize South African lottery results, enabling accurate data extraction and display. Key capabilities include AI-powered ticket scanning, comprehensive display of prize divisions, robust database management of lottery results, and AI-powered prediction. The business vision is to be the leading platform for South African lottery intelligence, offering unparalleled accuracy and real-time data to users with significant market potential in the South African lottery sector.

## User Preferences
- STRICT RULE: NO PLACEHOLDER DATA - All data must be authentic and extracted from real sources
- Requires authentic data only - no mock or placeholder data ever
- Single-image processing with Gemini 2.5 Pro for maximum accuracy
- Complete lottery result display with all prize divisions and financial details
- All lottery numbers must be extracted using Google Gemini API 2.5 Pro from official screenshots
- Fixed automation workflow to always follow complete 4-step cycle
  - STEP 1: Delete any existing images from screenshots folder (complete cleanup)
  - STEP 2: Capture 6 fresh screenshots from all SA lottery websites using Playwright + Chromium
  - STEP 3: Extract lottery data with Google Gemini 2.5 Pro AI and update database
  - STEP 4: Verify frontend updates with database confirmation
- Fixed PowerBall numbers appearing in separate row at bottom instead of inline with their respective main numbers
- Reduced ticket scanner lottery ball sizes from 58px to 40px to match Data Analytics preview card
- Fixed missing click functionality on "Numbers Not Drawn Recently" (third row) in Data Analytics
- Reduced hot/cold/absent number ball sizes from 58px to 40px for better space utilization
- Restored compact match notation (5+PB, 4+B, etc.) instead of verbose descriptions
- Implemented comprehensive SEO optimization for "lotto" keyword throughout webapp
- Fixed "View Full Analytics Dashboard" button appearing outside the Data Analytics Preview card
- Removed height linking between cards to eliminate extra rows and optimize each card individually
- Optimized Data Analytics sections to ensure all information fits properly within each box
- Removed horizontal scroll wheel from "Latest Lottery Results" card
- Reduced space between Draw, Date, and Numbers columns for more efficient layout
- Applied proper text contrast to lottery balls in "Latest Lottery Results" card
- Removed "BONUS NUMBERS" column from Daily Lottery results display
- Fixed lottery numbers to display in ascending order (small to large) followed by bonus numbers
- Removed the entire HISTORICAL RESULTS card section from the results page as requested
- Implemented comprehensive PWA (Progressive Web App) functionality for proper mobile shortcut display
  - Created complete web app manifest with South African lottery branding and shortcuts
  - Generated custom PWA icons in all required sizes (72x72 to 512x512)
  - Added service worker for offline functionality and caching
  - Implemented PWA meta tags for iOS Safari and Android Chrome standalone modes
  - Added mobile-optimized CSS for proper display when added as phone shortcut
  - Created install button for browsers that support PWA installation
  - Added safe area inset support for devices with notches/cutouts
- Successfully fixed PWA styling issues - restored white/yellow header theme and prevented content from scrolling behind status bar
- CRITICAL DATA INTEGRITY: Manually added missing Daily Lotto draws 2332 (2025-08-02), 2333 (2025-08-03), and 2342 (2025-08-12) that were identified by user as missing from database
- Historical lottery draws require manual entry when screenshot capture window has passed - user provided screenshot evidence for accurate data entry
- Daily automation workflow is essential to prevent missing lottery results - user evidence shows gaps when automation doesn't run daily
- CRITICAL FIX: Scheduler now uses same proven working system as manual button instead of separate unreliable code paths
- Fixed critical automation inconsistency where manual workflow button and automated schedulers used different code execution paths. Both scheduler_fix.py and simple_daily_scheduler.py now use identical CompleteLotteryProcessor().process_all_screenshots() method as manual button, eliminating code path discrepancies.
- Fixed critical issue where screenshots were captured successfully but data wasn't saving to database due to extraction vs insertion gap
- Successfully identified and saved missing Daily Lotto Draw 2350 (2025-08-20) with numbers [7, 14, 17, 22, 25] and 99% confidence - confirmed displaying correctly on frontend
- Implemented comprehensive AI prediction accuracy tracking that compares predictions against actual results, calculates match percentages, determines prize tiers, maintains historical accuracy statistics for continuous algorithm improvement, and automatically generates new replacement predictions after validation
- When a prediction is validated against a draw result, the system automatically generates a new prediction for the next draw of the same game type to maintain continuous prediction coverage
- Fixed target draw date calculation to use next day (daily draws) instead of next week for Daily Lotto predictions, ensuring accurate prediction timing for daily draws
- CRITICAL BUG FIX (2025-09-01): Fixed Daily Lotto type detection bug where screenshots were being misclassified as 'LOTTO' instead of 'DAILY LOTTO' due to filename pattern matching order. Moved daily_lotto check to highest priority in get_lottery_type_from_filename method, ensuring accurate processing of all 6 lottery types with 99% AI confidence. Manual workflow fully restored to operational status.
- Completely removed "Numbers Not Drawn Recently" section from both backend API and frontend as user recognized all numbers will eventually be drawn in active lottery systems, leaving only Hot Numbers (most frequent) and Cold Numbers (least frequent) for cleaner, more focused analysis
- Implemented robust screenshot capture system with enhanced error handling, progressive retry logic, and network connectivity testing to resolve daily automation failures. System now successfully captures all 6 screenshots and processes lottery results with 99% AI confidence
- Implemented proper prediction management to ensure only one pending prediction per game type exists at any time. Fixed save_prediction method to update existing pending predictions instead of creating duplicates, cleaned up 27 excess predictions, and ensured Daily Lotto draw 2350 displays AI prediction performance data correctly
- Major prediction accuracy enhancement - expanded analysis from 15 draws to 100 historical draws (optimized for AI processing), implemented multi-timeframe analysis (recent 20, medium-term 40, long-term 40+), added cyclical pattern detection (monthly/quarterly/seasonal), drought cycle analysis, hot/cold transition tracking, and anomaly detection for statistical outliers and pattern breaks
- Optimized validation system to only generate replacement predictions for game types that actually have new results and successful validations, eliminating unnecessary AI API calls and improving system efficiency by preventing prediction generation for game types without new lottery results
- Successfully implemented comprehensive draw ID linking system where predictions are automatically linked to specific future draw IDs (e.g., prediction [4,9,22,30,33] linked to Daily Lotto draw 2357). Added linked_draw_id column to database, created API endpoints for draw-specific prediction lookup (/api/predictions/by-draw/{id}), and fixed confidence display bug where scores were incorrectly multiplied by 100 again (44.25% showing as 4425% - now correctly displays as 44%)
- Eliminated all backup and fallback prediction methods across all game types. All 6 lottery games (Daily Lotto, Lotto, Lotto Plus 1/2, Powerball/Plus) now use the same intelligent "Hybrid Frequency-Gap Analysis with Learning" methodology that incorporates 40+ historical draws, hot/cold number patterns, mean reversion strategies, and performance-based learning from validated predictions. Removed AI Ensemble backup methods that were using simple statistical sampling instead of comprehensive learning intelligence.
- Implemented automatic AI prediction generation that triggers immediately after new lottery results are captured by the manual workflow or automation schedulers. Both simple_daily_scheduler.py and scheduler_fix.py now include Step 4 that automatically calls PredictionRefreshSystem when new lottery results are detected, ensuring fresh AI predictions are generated based on the latest lottery data without manual intervention. This creates a seamless workflow: screenshot capture → AI extraction → database update → automatic prediction generation.
- Resolved two critical bugs preventing prediction generation and validation. Fixed missing 'generate_ai_prediction' method in AILotteryPredictor class and completed PredictionValidationSystem class with all required methods (validate_prediction, validate_prediction_against_result, validate_all_pending_predictions, calculate_prediction_accuracy). Both automation schedulers and manual workflows now have complete functionality for the full prediction lifecycle: generation, validation, and automatic replacement predictions.
- Added automatic prediction validation to manual workflow. Enhanced both simple_daily_scheduler.py and scheduler_fix.py to include Step 4a (prediction validation) and Step 4b (prediction generation). Manual workflow now: capture results → validate existing predictions → generate new predictions.
- Fixed major prediction date logic issue where predictions were being generated for past dates (e.g., generated 2025-08-31 targeting 2025-08-25). Implemented robust future date calculation ensuring all predictions target future draws only. Fixed Gemini API key conflicts and created simple_ai_predictor.py with optimized token limits. All predictions now use logical future dates and maintain required "Hybrid Frequency-Gap Analysis with Learning" methodology exclusively.

## System Architecture
The platform features a modular codebase designed for enhanced security and performance. The UI/UX prioritizes consistency and readability, with optimized ball sizes and clear visual elements across the application.

-   **Frontend**: Responsive web interface with mobile-friendly design and PWA functionality, ensuring visual consistency.
-   **Backend**: Python Flask framework.
-   **Database**: PostgreSQL with optimized architecture including performance indexes and efficient storage, adhering to authentic data.
-   **AI Integration**: Google Gemini 2.5 Pro powers AI-driven ticket scanning, data extraction, pattern analysis, and lottery prediction.
    **Unified Prediction Algorithm Details:**
    -   **Core Engine**: Hybrid Frequency-Gap Analysis with Learning (unified across all game types)
    -   **Historical Analysis**: 40+ historical draws per game with extended pattern recognition
    -   **Learning Framework**: Hot number frequency patterns, cold number mean reversion, statistical balance validation
    -   **Performance Integration**: Incorporates accuracy feedback from validated predictions to improve future predictions
    -   **Confidence Scoring**: 45-65% confidence scores based on historical frequency patterns and pattern strength
    -   **Individual Game Rules**: LOTTO (6 main, 1-52), LOTTO PLUS 1/2 (6 main, 1-52), POWERBALL/PLUS (5 main 1-50 + 1 bonus 1-20), DAILY LOTTO (5 main, 1-36)
-   **Automation Workflow**: A robust 4-step daily automation process utilizing Playwright + Chromium for screenshot capture, AI processing, database updates, and frontend verification, with anti-detection measures.
-   **Security**: Implemented CSRF protection, comprehensive form validation, secure session settings, rate limiting, input sanitization, centralized error handling, and admin-only access for sensitive AI features.
-   **Performance**: Optimized database queries, critical performance indexes, and a cache manager. Decoupled card heights for optimal content display.
-   **Admin Dashboard**: Comprehensive interface for data management, system settings, system health monitoring, advertisement management, and automation control, including manual triggers for AI prediction generation and data approval.
-   **Core Features**:
    -   **Ticket Scanner**: Extracts player-selected numbers and detects multiple game types (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2) with multi-line support.
    -   **Results Display**: Shows complete lottery results with all prize divisions and financial details, with numbers sorted ascending.
    -   **Data Analytics**: Displays hot/cold numbers and frequency charts, derived from authentic lottery data, including AI-powered pattern analysis.
    -   **AI-Powered Lottery Predictor**: Generates and validates lottery number predictions with accuracy tracking and self-improvement, based on comprehensive AI analysis of historical data. Predictions are static until new draw results are available.
    -   **Data Preview and Approval System**: Allows review, approval, deeper extraction requests, and rejection of AI-extracted data.

## External Dependencies
-   **Google Gemini 2.5 Pro**: Integrated via `GOOGLE_API_KEY_SNAP_LOTTERY` for all AI-powered functionalities.
-   **Playwright + Chromium**: Used for automated screenshot capture of South African lottery websites.
-   **PostgreSQL**: The primary database for storing and managing all lottery results and related data.
-   **psycopg2**: Python adapter for PostgreSQL.
-   **Flask**: Python web framework.
-   **Gunicorn**: WSGI HTTP server for production.
-   **SQLAlchemy**: ORM for database interaction.
-   **Flask-WTF**: For CSRF protection.
-   **Flask-Login**: For user management.
-   **APScheduler**: For task scheduling.