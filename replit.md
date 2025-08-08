# South African Lottery Ticket Scanner

## Overview
This project is an AI-powered lottery intelligence platform for South African lotteries. Its primary purpose is to process and synchronize South African lottery results, enabling accurate data extraction and display. Key capabilities include AI-powered ticket scanning, comprehensive display of prize divisions, and robust database management of lottery results. The business vision is to be the leading platform for South African lottery intelligence, offering unparalleled accuracy and real-time data to users.

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
- Successfully extracted and added missing Daily Lotto Draw 2325 from July 26, 2025
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
- CRITICAL DATA INTEGRITY: Manually added missing Daily Lotto draws 2332 (2025-08-02) and 2333 (2025-08-03) that were identified by user as missing from database
- Daily automation workflow is essential to prevent missing lottery results - user evidence shows gaps when automation doesn't run daily
- Implemented comprehensive AI-powered pattern analysis on /visualizations page using Google Gemini 2.5 Pro
  - Created gemini_pattern_analyzer.py for advanced pattern detection and analysis
  - Added AI pattern analysis routes: /api/lottery-analysis/ai-patterns and /api/lottery-analysis/game-insights
  - Enhanced visualizations page with interactive AI analysis sections for number patterns and game-specific insights
  - Integrated frontend JavaScript (ai-pattern-analyzer.js) for seamless AI analysis interface
  - AI analyzes mathematical patterns, sequences, statistical anomalies, and game-specific characteristics from authentic lottery data
- MAJOR NEW FEATURE COMPLETED: AI-Powered Lottery Predictor System with Complete Navigation Integration
  - Created comprehensive AI lottery predictor system (ai_lottery_predictor.py) with accuracy tracking and self-improvement capabilities
  - Added prediction routes to lottery_analysis.py with endpoints for generating predictions and tracking accuracy
  - Created predictions page template with interactive AI prediction interface
  - Integrated predictions navigation links in both desktop and mobile navigation menus
  - Enhanced system to generate lottery number predictions, validate accuracy against actual results, and fine-tune future predictions
  - Added predictions route handler in main.py to serve the predictions page
  - Full navigation system implemented with "AI Predictions" in desktop menu and "AI" icon in mobile bottom bar
- SECURITY ENHANCEMENT COMPLETED: Admin-Only Access for AI Predictions Feature
  - Applied @require_admin decorator to /predictions route for admin-only page access
  - Protected all AI prediction API endpoints with admin authentication:
    * /api/lottery-analysis/predictions - Get AI-generated predictions
    * /api/lottery-analysis/prediction-accuracy - Get accuracy statistics  
    * /api/lottery-analysis/generate-prediction - Generate new predictions
    * /api/lottery-analysis/prediction-history - Get historical predictions
    * /api/lottery-analysis/system-metrics - Get system performance data
  - Hidden AI Predictions navigation links from non-admin users in both desktop and mobile menus
  - Implemented conditional Jinja2 templates using current_user.is_authenticated and current_user.is_admin checks
  - Ensures AI prediction system is exclusively available to administrators while maintaining secure access control
- UI/UX REDESIGN COMPLETED: Clean AI Predictions Interface
  - Completely redesigned predictions page with clean, organized card-based layout
  - Simplified navigation with clear sections: Generate, Latest Predictions, Statistics
  - Enhanced readability with improved typography and spacing
  - Added intuitive controls for generating new predictions with game type selection
  - Streamlined display of AI findings with lottery ball visualizations and confidence badges
  - Implemented clear loading states and error handling for better user experience
- AUTOMATED PREDICTION SYSTEM IMPLEMENTED: Weekly AI Prediction Generation
  - Created comprehensive weekly prediction scheduler that generates 3 predictions per draw based on game schedules
  - Automated system processes all 6 lottery games with proper draw frequency:
    * LOTTO/LOTTO PLUS 1/LOTTO PLUS 2: 6 predictions each (2 draws × 3 predictions per draw)
    * POWERBALL/POWERBALL PLUS: 6 predictions each (2 draws × 3 predictions per draw)  
    * DAILY LOTTO: 21 predictions (7 days × 3 predictions per day)
  - Enhanced AI predictor with variation seeds to ensure diverse predictions for each draw
  - Added manual trigger functionality through admin interface for immediate weekly batch generation
  - Implemented automatic cleanup of old predictions to prevent database bloat
  - Total weekly output: 45 predictions with detailed AI analysis and confidence scores
- PREDICTION VALIDATION SYSTEM IMPLEMENTED: Match Analysis and Learning
  - Added comprehensive prediction validation against actual lottery results
  - Enhanced database schema with match tracking fields (main_number_matches, bonus_number_matches, accuracy_percentage, prize_tier)
  - Implemented automatic validation system that compares predictions with actual draws
  - Created prediction accuracy insights API for analyzing which numbers perform best
  - Added validation interface showing match results, prize tiers, and accuracy percentages
  - Enhanced predictions display with validation status, match counts, and improvement recommendations
- STATIC PREDICTION SYSTEM IMPLEMENTED: Draw-Based Refresh Logic
  - Created prediction_refresh_system.py for intelligent prediction management
  - Predictions now remain static until new draw results become available for each game type
  - Each game displays exactly 3 predictions for the upcoming draw only
  - System automatically refreshes predictions when new draw data is detected
  - Enhanced user experience with consistent predictions until validation against actual results
  - Eliminates confusion from constantly changing predictions without new data justification
- COMPREHENSIVE AI ANALYSIS SYSTEM: Deep Lottery Data Analysis
  - Enhanced AI predictor to analyze ALL available lottery data, not just winning numbers
  - AI now examines prize distributions, financial patterns, temporal correlations, and mathematical properties
  - Comprehensive analysis includes division winner counts, payout amounts, jackpot progressions, rollover frequencies
  - Advanced pattern detection for algorithmic signatures in even/odd ratios, sum analysis, consecutive sequences
  - Temporal pattern analysis for day-of-week, monthly, and yearly correlations
  - Financial correlation analysis between jackpot amounts, sales volumes, and number patterns
  - Google Gemini 2.5 Pro tasked with finding exploitable algorithmic behaviors rather than just statistical analysis
- FULL SYSTEM INTEGRATION COMPLETED: All Prediction Tools Use Comprehensive AI
  - Updated all scheduled prediction systems (weekly_prediction_scheduler.py, prediction_refresh_system.py)
  - Updated all API endpoints (/predictions, /generate-prediction, /prediction-accuracy, /validate-prediction, /accuracy-insights)
  - Updated prediction validation system (prediction_validation_system.py) to use comprehensive analysis
  - All prediction generation now uses AILotteryPredictor class with complete lottery ecosystem analysis
  - Every prediction spends 60-75 seconds analyzing prize patterns, financial flows, temporal correlations
  - Unified system ensures consistent comprehensive AI analysis across all prediction interfaces

## System Architecture
The platform features a modular codebase designed for enhanced security and performance. The UI/UX prioritizes consistency and readability, with optimized ball sizes and clear visual elements across the application.

- **Frontend**: Responsive web interface with mobile-friendly design with PWA functionality. Visual consistency is maintained across all lottery ball displays through specific CSS classes.
- **Backend**: Python Flask framework.
- **Database**: PostgreSQL with optimized architecture including performance indexes and efficient storage. Strict adherence to authentic data.
- **AI Integration**: Google Gemini 2.5 Pro powers AI-driven ticket scanning, data extraction, pattern analysis, and lottery prediction. This includes an `ai_lottery_processor.py` for data extraction and an `ai_lottery_predictor.py` for generating and validating predictions with deep data analysis.
- **Automation Workflow**: A robust 4-step daily automation process utilizing Playwright + Chromium for screenshot capture, AI processing, database updates, and frontend verification, with anti-detection measures.
- **Security**: Implemented CSRF protection, comprehensive form validation, secure session settings, rate limiting, input sanitization, centralized error handling, and admin-only access for sensitive AI features.
- **Performance**: Optimized database queries, critical performance indexes, and a cache manager. Decoupled card heights for optimal content display.
- **Admin Dashboard**: Comprehensive interface for data management, system settings, system health monitoring, advertisement management, and automation control, including manual triggers for AI prediction generation and data approval.
- **Core Features**:
    - **Ticket Scanner**: Extracts player-selected numbers and detects multiple game types (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2) with multi-line support.
    - **Results Display**: Shows complete lottery results with all prize divisions and financial details, with numbers sorted ascending.
    - **Data Analytics**: Displays hot/cold/absent numbers and frequency charts, derived from authentic lottery data, including AI-powered pattern analysis.
    - **AI-Powered Lottery Predictor**: Generates and validates lottery number predictions with accuracy tracking and self-improvement, based on comprehensive AI analysis of historical data, with automated weekly generation.
    - **Data Preview and Approval System**: Allows review, approval, deeper extraction requests, and rejection of AI-extracted data.

## External Dependencies
- **Google Gemini 2.5 Pro**: Integrated via `GOOGLE_API_KEY_SNAP_LOTTERY` for all AI-powered functionalities.
- **Playwright + Chromium**: Used for automated screenshot capture of South African lottery websites.
- **PostgreSQL**: The primary database for storing and managing all lottery results and related data.
- **psycopg2**: Python adapter for PostgreSQL.
- **Flask**: Python web framework.
- **Gunicorn**: WSGI HTTP server for production.
- **SQLAlchemy**: ORM for database interaction.
- **Flask-WTF**: For CSRF protection.
- **Flask-Login**: For user management.
- **APScheduler**: For task scheduling.