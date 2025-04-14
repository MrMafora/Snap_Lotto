# Workflow Configuration Guide for Lottery Data Platform

## Current Status

We've encountered a consistent issue with Replit's workflow system:

- Replit's workflow system has a strict 20-second timeout for port detection
- Our application requires more time to fully initialize due to:
  - Database connections
  - Scheduler initialization
  - OCR client setup
  - Multiple model imports

## Optimization Solutions

We've implemented several optimizations to address the slow startup:

1. **Lazy Loading**: Deferred module imports in main.py and scheduler.py
2. **Optimized OCR Client**: Only initializes when actually needed
3. **Quick Port Binding**: Ultra-minimal socket binding script for immediate port detection
4. **Background Initialization**: Heavy components start in background threads

## Latest Workflow Configuration

The current workflow uses our optimized startup approach:

1. `quick_bind.py` - Ultra-minimal socket binder that immediately opens port 5000
2. `workflow_wrapper.sh` - Shell script that launches the quick binder
3. `main.py` - Optimized application code with lazy loading
4. `scheduler.py` - Improved scheduler with delayed initialization

## Manual Startup Solution (Backup)

If the workflow solution still has issues, the most reliable fallback is:

1. Open a Shell tab in Replit
2. Run: `./start_manually.sh`
3. Wait approximately 30 seconds for full initialization
4. Access the application via the normal Replit URL

## For Deployment

When deploying to production, either:

1. Use the optimized startup scripts included in the project, or
2. Modify your hosting configuration to allow more time for port detection