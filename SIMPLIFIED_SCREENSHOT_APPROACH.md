# Simplified Screenshot Approach for Lottery Data

## Overview

We've implemented a simplified screenshot capture system that focuses solely on capturing full-page screenshots without any data extraction or complex page interactions. This approach is designed to work with websites that have strong anti-scraping protections, such as the South African National Lottery website.

## Key Features

1. **Basic Screenshot Capture**: The system captures full-page screenshots using Playwright's headless browser without any complex page interactions or data extraction.
2. **Improved Reliability**: Increased timeouts (45 seconds navigation, 5 seconds post-load wait) to accommodate slow-loading websites.
3. **Error Resilience**: Implements an exponential backoff strategy with multiple retry attempts for failed captures.
4. **Resource Efficiency**: Uses semaphores to limit concurrent screenshot operations and prevent "can't start new thread" errors.
5. **Direct Database Integration**: Works directly with the database to store and update screenshot records.

## Components

### 1. Simple Screenshot Manager (`simple_screenshot_manager.py`)

- `capture_screenshot()`: Basic function to capture a screenshot of a URL using Playwright.
- `capture_all_screenshots()`: Captures screenshots for all lottery URLs in the database.
- `sync_single_screenshot()`: Updates a specific screenshot by ID.

### 2. Simple Scheduler (`simple_scheduler.py`)

- `retake_all_screenshots()`: Entry point for capturing all screenshots.
- `sync_single_screenshot()`: Entry point for syncing a single screenshot.

### 3. Routes in `main.py`

- `/sync-all-screenshots`: Route to trigger screenshot capture for all URLs.
- `/sync-screenshot/<id>`: Route to capture a specific screenshot.
- `/cleanup-screenshots`: Route to clean up old screenshots.

## Technical Specifications

1. **Browser Configuration**:
   - Chromium browser in headless mode
   - Standard user-agent string
   - 1280x1024 viewport size

2. **Timeout Settings**:
   - 60 seconds navigation timeout
   - 5 seconds additional wait after page load

3. **Retry Logic**:
   - Maximum 3 retry attempts
   - Increasing wait periods between retries (5, 10, 15 seconds)

4. **Thread Management**:
   - Maximum 2 concurrent screenshot operations
   - Semaphore-based thread limiting

## Usage Examples

### Capturing All Screenshots

```python
import simple_scheduler

# From a Flask route
with app.app_context():
    count = simple_scheduler.retake_all_screenshots()
```

### Syncing a Single Screenshot

```python
import simple_scheduler

# From a Flask route
with app.app_context():
    success = simple_scheduler.sync_single_screenshot(screenshot_id)
```

## Comparison to Original Approach

| Feature | Original Approach | Simplified Approach |
|---------|------------------|-------------------|
| Primary Focus | Screenshot + Data Extraction | Screenshot Only |
| Complexity | High (Page interactions) | Low (Basic capture) |
| Error Handling | Limited | Comprehensive with retries |
| Resource Usage | High | Moderate |
| Anti-Scraping Bypass | Limited | Improved |
| Timeout Settings | 20 seconds | 60 seconds |
| Wait After Load | None | 5 seconds |

## Benefits

1. **Higher Success Rate**: By focusing solely on capturing screenshots without trying to extract data, the system is less likely to be detected as a scraper.
2. **Simplified Maintenance**: Less complex code means fewer points of failure and easier troubleshooting.
3. **Better Resource Efficiency**: Controlled concurrency prevents resource exhaustion.
4. **Improved Error Handling**: Comprehensive retry logic with exponential backoff.
5. **More Reliable for Anti-Scraping Sites**: The reduced footprint helps avoid detection by sophisticated anti-scraping measures.

## Conclusion

This simplified approach solves the persistent issues with screenshot capture by focusing only on the essential functionality. It prioritizes reliability and success rate over complex capabilities, making it more suitable for websites with strong anti-scraping protections.