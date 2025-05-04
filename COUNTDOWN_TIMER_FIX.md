# Countdown Timer Fix

This document outlines the fixes implemented to resolve the issue where the 30-second countdown timer was resetting around 26-25 seconds or sometimes even at 10 seconds.

## Issue

The countdown timer was resetting unexpectedly during its countdown sequence, causing user frustration as they would have to wait longer than the expected 30 seconds to view results.

## Root Cause Analysis

After investigating the code, we identified several issues:

1. Multiple timer instances were being created when scanning tickets in sequence
2. The global timer state wasn't being properly tracked, allowing new timers to start while existing ones were running
3. Timers weren't being properly cleaned up when:
   - A new scan was initiated
   - The "View Results" button was clicked
   - An error occurred during scanning

## Implemented Fixes

### 1. Global Timer State Tracking

Added a global flag to track if a countdown is already running:

```javascript
// We'll use a global flag to track if countdown is already running
if (!window.countdownRunning) {
    console.log('Setting 30-second mandatory ad display timer...');
    
    // Set global flag to prevent multiple timers
    window.countdownRunning = true;
    
    // Timer code...
} else {
    console.log('Countdown already running, not starting a new one');
}
```

### 2. Accurate Time Tracking

Updated the time calculation to use actual elapsed time instead of decrementing a counter:

```javascript
// Store timer start time to prevent deviations
window.countdownStartTime = Date.now();
window.countdownDuration = 30000; // 30 seconds in milliseconds

// Update the counter every second based on elapsed time
window.countdownInterval = setInterval(() => {
    // Calculate remaining time based on actual elapsed time
    const elapsedMs = Date.now() - window.countdownStartTime;
    const remainingMs = Math.max(0, window.countdownDuration - elapsedMs);
    const remainingSeconds = Math.ceil(remainingMs / 1000);
    
    // Update display
    counterElement.textContent = `Results available in ${remainingSeconds} seconds...`;
    
    // Update button text
    viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${remainingSeconds}s)`;
    
    // Check if countdown is complete based on actual time
    if (remainingSeconds <= 0) {
        // Cleanup code...
    }
}, 1000);
```

### 3. Comprehensive Timer Cleanup

Added timer cleanup to multiple places in the code:

#### In clearPreviousResults()

```javascript
function clearPreviousResults() {
    // Clean up any existing countdown timers when clearing results
    if (window.countdownInterval) {
        clearInterval(window.countdownInterval);
        window.countdownInterval = null;
    }
    
    if (window.countdownTimeout) {
        clearTimeout(window.countdownTimeout);
        window.countdownTimeout = null;
    }
    
    // Reset the countdown running flag since we're starting fresh
    window.countdownRunning = false;
    
    // Rest of the function...
}
```

#### In "View Results" Button Click Handler

```javascript
viewResultsBtn.onclick = function() {
    adOverlayResults.style.display = 'none';
    
    // Clean up all timers and reset the state
    if (window.countdownInterval) {
        clearInterval(window.countdownInterval);
        window.countdownInterval = null;
    }
    
    if (window.countdownTimeout) {
        clearTimeout(window.countdownTimeout);
        window.countdownTimeout = null;
    }
    
    // Reset the countdown running flag
    window.countdownRunning = false;
    
    // Make sure scrolling is enabled
    enableScrolling();
    displayResults(data);
    console.log('User clicked View Results, countdown state cleared');
};
```

#### In Error Handler

```javascript
.catch(error => {
    console.error('Error:', error);
    
    // Clean up any running timers in case of error
    if (window.countdownInterval) {
        clearInterval(window.countdownInterval);
        window.countdownInterval = null;
    }
    
    if (window.countdownTimeout) {
        clearTimeout(window.countdownTimeout);
        window.countdownTimeout = null;
    }
    
    // Reset the countdown running flag
    window.countdownRunning = false;
    
    // Hide ad loading overlay
    const adOverlayLoading = document.getElementById('ad-overlay-loading');
    adOverlayLoading.style.display = 'none';
    
    // Make sure scrolling is enabled in case of error
    enableScrolling();
    showError('An error occurred while scanning your ticket. Please try again.');
})
```

## Benefits

These changes ensure:

1. The countdown timer runs exactly once for each ticket scan
2. The timer tracks actual elapsed time rather than relying on incremental updates
3. The timer is properly cleaned up in all scenarios (new scan, view results, error)
4. Users experience a consistent 30-second countdown without unexpected resets

## Testing

The application was tested with multiple ticket scans in sequence to verify that the countdown runs consistently without resets.