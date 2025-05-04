# Preview Generation Enhancements

## Problem Analysis
The preview-website feature was experiencing timeout issues when trying to capture screenshots of lottery websites. The error message "Preview generation timed out. The website may be unavailable" suggests that:

1. The National Lottery website is responding slowly or implementing measures that delay automated requests
2. Our preview generation timeouts were too short (20 seconds)
3. We lacked a robust retry strategy with exponential backoff

## Implemented Improvements

### 1. Extended Timeouts
- Increased preview navigation timeout from 20 seconds to 45 seconds
- Set maximum wait time to 60 seconds for the entire preview generation process
- Added cache headers to reduce server load (1-hour caching)

### 2. Resilient Retry Logic
- Increased maximum retry attempts for preview operations from 3 to 5
- Implemented exponential backoff for retries (1s, 2s, 4s, 8s, 15s)
- Added varied request strategies on each retry:
  - Different user agents per attempt
  - Alternating viewport sizes
  - Different wait_until strategies ('domcontentloaded' or 'load')
  - Modified HTTP headers including cache control
  - Added referer headers on retry attempts

### 3. Better Error Handling
- More robust error classification to identify timeout vs. other issues
- Continued screenshot process even after navigation timeouts to capture partial content
- Added scrolling attempts to trigger lazy-loaded content on retry attempts
- Improved error messages with clear advice on what to do next

### 4. Improved Caching Strategy  
- Used existing screenshots if fresh (less than 1 hour old)
- Added etag headers for proper caching
- Made cache timeout configurable (PREVIEW_CACHE_SECONDS)

### 5. Optimized Browser Configuration
- Used low-resource mode for preview generation with disabled extensions
- Optimized launch arguments for speed and reliability
- Eliminated non-essential browser features for preview capturing

## Technical Implementation Details
1. Created a specialized `generate_preview_image()` function optimized for previews
2. Modified the `preview_website` route to use the new function with fallback strategies
3. Added timing metrics to monitor performance
4. Enhanced error page to provide more specific information about the failure

## Fallback Mechanisms
If the optimized preview function fails, the system will:
1. First try to use any existing screenshot if available (even if older)
2. Attempt up to 5 retries with exponential backoff
3. Try different browser configurations on each retry 
4. As a last resort, fall back to the standard screenshot function

These improvements make the preview generation more patient and resilient in the face of slow-responding pages and potential anti-scraping measures.