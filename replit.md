# South African Lottery Ticket Scanner

## Overview
This project is an AI-powered lottery intelligence platform designed for South African lotteries. Its primary purpose is to process, synchronize, and display SA lottery results, enabling accurate data extraction and AI-powered prediction. The platform aims to be the leading source for SA lottery intelligence, providing unparalleled accuracy and real-time data. Key capabilities include AI-powered ticket scanning, comprehensive display of prize divisions, and robust database management of lottery results. The business vision is to become the definitive source for SA lottery intelligence, leveraging AI for predictive analysis and offering a significant market advantage in the market.

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
- Successfully fixed PWA styling issues - restored white/yellow header theme and prevented content from scrolling behind status bar
- Historical lottery draws require manual entry when screenshot capture window has passed - user provided screenshot evidence for accurate data entry
- Daily automation workflow is essential to prevent missing lottery results - user evidence shows gaps when automation doesn't run daily
- Completely removed "Numbers Not Drawn Recently" section from both backend API and frontend as user recognized all numbers will eventually be drawn in active lottery systems, leaving only Hot Numbers (most frequent) and Cold Numbers (least frequent) for cleaner, more focused analysis

## System Architecture
The platform features a modular codebase designed for enhanced security and performance. The UI/UX prioritizes consistency and readability, with optimized ball sizes and clear visual elements across the application.

-   **Frontend**: Responsive web interface with mobile-friendly design and PWA functionality, ensuring visual consistency.
-   **Backend**: Python Flask framework.
-   **Database**: PostgreSQL with optimized architecture including performance indexes and efficient storage, adhering to authentic data.
-   **AI Integration**: Google Gemini 2.5 Pro powers AI-driven ticket scanning, data extraction, pattern analysis, and advanced neural network lottery prediction using multi-phase intelligent systems for maximum accuracy.
    **Advanced Prediction System Details:**
    -   **Phase 1 - Frequency Analysis Engine**: Hybrid Frequency-Gap Analysis with Near-Miss Learning (unified across all game types)
        -   Historical Analysis: 180-day analysis (up to 100 draws) with robust data parsing and frequency mapping
        -   Learning Framework: Hot number frequency patterns (50% selection weight), cold number mean reversion (20% weight), neutral statistical balance (30% weight), weighted bonus number selection
        -   Confidence Scoring: 45-75% evidence-based confidence scores using historical frequency patterns and data quality indicators
    -   **Phase 2 - Neural Network Ensemble (Production Ready)**: Advanced multi-model ensemble with genuine machine learning
        -   Core Models: Random Forest + Gradient Boosting + Neural Network with performance-weighted aggregation
        -   Training: Uses 180+ days of historical data with proper temporal alignment for forward prediction
        -   Bonus Prediction: Dedicated bonus number models for POWERBALL games with intelligent fallback to Phase 1
        -   Confidence Scoring: 50-85% evidence-based scores using model agreement, ensemble performance, and data quality
        -   Smart Selection: Automatically uses Phase 2 when sufficient data available (≥20 samples), falls back to Phase 1 otherwise
    -   **Individual Game Rules**: LOTTO (6 main, 1-52), LOTTO PLUS 1/2 (6 main, 1-52), POWERBALL/PLUS (5 main 1-50 + 1 bonus 1-20), DAILY LOTTO (5 main, 1-36)
    -   **Performance Integration**: Incorporates accuracy feedback from validated predictions to improve future predictions across both phases
-   **Automation Workflow**: A robust 4-step daily automation process utilizing Playwright + Chromium for screenshot capture, AI processing, database updates, and frontend verification, with anti-detection measures. The scheduler uses the same proven system as the manual trigger for consistency. Predictions are automatically generated and validated as part of this workflow, linking predictions to specific future draw IDs.
-   **Security**: Implemented CSRF protection, comprehensive form validation, secure session settings, rate limiting, input sanitization, centralized error handling, and admin-only access for sensitive AI features.
-   **Performance**: Optimized database queries, critical performance indexes, and a cache manager. Decoupled card heights for optimal content display.
-   **Admin Dashboard**: Comprehensive interface for data management, system settings, system health monitoring, advertisement management, and automation control, including manual triggers for AI prediction generation and data approval.
-   **Core Features**:
    -   **Ticket Scanner**: Extracts player-selected numbers and detects multiple game types (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2) with multi-line support.
    -   **Results Display**: Shows complete lottery results with all prize divisions and financial details, with numbers sorted ascending.
    -   **Data Analytics**: Displays hot/cold numbers and frequency charts, derived from authentic lottery data, including AI-powered pattern analysis.
    -   **AI-Powered Lottery Predictor**: Generates and validates lottery number predictions with accuracy tracking and self-improvement, based on comprehensive AI analysis of historical data and near-miss learning. Predictions are static until new draw results are available, and new predictions are automatically generated for the next draw after validation.
    -   **Data Preview and Approval System**: Allows review, approval, deeper extraction requests, and rejection of AI-extracted data.

## Deployment Configuration
-   **Package Management**: Migrated from requirements.txt to modern `pyproject.toml` format (setuptools build system)
-   **Deployment Files Cleaned Up (Oct 1, 2025)**:
    -   ✅ **Active**: `pyproject.toml` - Modern Python dependency management with 31 packages
    -   ✅ **Active**: `.replit` - Single deployment configuration using GCE (Google Compute Engine)
    -   ❌ **Removed**: `runtime.txt` - Old Heroku format (obsolete)
    -   ❌ **Removed**: `Procfile` - Old Heroku format (obsolete)
    -   ❌ **Removed**: `replit_deployment.toml` - Conflicting Cloud Run config (caused 502 errors)
    -   ❌ **Removed**: `deployment_start.py` - Redundant custom startup script
-   **Current Deployment Setup**:
    -   Build: `pip install .` (uses pyproject.toml automatically)
    -   Run: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 1 --timeout 120 main:app`
    -   Platform: Replit Deployment (GCE backend)
    -   Development Port: 5000
    -   Production Port: Dynamic ($PORT environment variable)
-   **Key Files**:
    -   `main.py`: Main Flask application with dynamic PORT support
    -   `app.py`: Gunicorn compatibility bridge (exports `application = app`)
    -   `pyproject.toml`: All dependencies and build configuration

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