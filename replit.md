# South African Lottery Ticket Scanner

## Project Overview
Advanced AI-powered lottery intelligence platform that processes and synchronizes South African lottery results with Google Gemini 2.5 Pro for accurate data extraction.

## Current State
- Complete lottery application with authentic SA lottery data display
- Google Gemini 2.5 Pro integration for AI-powered ticket scanning
- Full prize divisions display (8 for Lotto types, 9 for Powerball types, 4 for Daily Lotto)
- PostgreSQL database with comprehensive lottery results

## User Preferences
- Requires authentic data only - no mock or placeholder data
- Single-image processing with Gemini 2.5 Pro for maximum accuracy
- Complete lottery result display with all prize divisions and financial details

## Recent Changes
- Fixed duplicate function issues in main.py (June 22, 2025)
- Resolved database access issues for authentic prize divisions display
- Successfully implemented complete lottery data display with all 8 prize divisions
- Fixed JSON data parsing for proper database prize division rendering
- Updated lottery details template to display complete prize division tables

## Active Request
User wants a data preview and approval system that allows:
- Preview extracted data from each image
- Approve correct data
- Send incorrect data back for deeper extraction
- Process each image individually

## Architecture
- Python Flask backend with PostgreSQL database
- Google Gemini 2.5 Pro AI integration via GOOGLE_API_KEY_SNAP_LOTTERY
- Responsive web interface with mobile-friendly design
- Real-time data processing and extraction capabilities