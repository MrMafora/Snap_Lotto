/**
 * Scan Process Watchdog - Ensures scanning process never gets stuck
 * This script will monitor the scanning process and force advancement
 * if it gets stuck in any of the ad screens.
 */

// Create a self-executing function to avoid polluting global scope
(function() {
    let watchdogConfig = {
        firstAdMaxTime: 15000,  // Max time in first ad (15 seconds)
        secondAdMaxTime: 20000, // Max time in second ad (20 seconds)
        checkInterval: 1000,    // Check every second
        running: false          // Watchdog status flag
    };
    
    let watchdogState = {
        startTime: 0,
        firstAdStarted: false,
        firstAdCompleted: false,
        secondAdStarted: false,
        secondAdCompleted: false,
        intervalsRun: 0
    };
    
    // Core monitoring function
    function monitorScanProcess() {
        watchdogState.intervalsRun++;
        
        // Get elements we need to monitor
        const loadingOverlay = document.getElementById('ad-overlay-loading');
        const resultsOverlay = document.getElementById('ad-overlay-results');
        
        // Check if we're in the first ad
        if (loadingOverlay && getComputedStyle(loadingOverlay).display !== 'none') {
            if (!watchdogState.firstAdStarted) {
                watchdogState.firstAdStarted = true;
                watchdogState.startTime = Date.now();
                console.log('Watchdog: First ad started at ' + new Date().toISOString());
            }
            
            // Check if we've been in the first ad too long
            const timeInFirstAd = Date.now() - watchdogState.startTime;
            if (timeInFirstAd > watchdogConfig.firstAdMaxTime) {
                console.warn('Watchdog: First ad has been shown for too long, forcing advancement');
                
                // Force hide first ad
                loadingOverlay.style.display = 'none';
                
                // Force show second ad if we have results
                if (window.lastResultsData) {
                    if (resultsOverlay) {
                        console.log('Watchdog: Showing results overlay');
                        resultsOverlay.style.display = 'flex';
                    }
                    
                    // Also call AdManager if available
                    if (window.AdManager && typeof window.AdManager.showInterstitialAd === 'function') {
                        console.log('Watchdog: Forcing AdManager.showInterstitialAd()');
                        window.AdManager.showInterstitialAd();
                    }
                }
                
                watchdogState.firstAdCompleted = true;
            }
        } 
        // Check if we're in the second ad
        else if (resultsOverlay && getComputedStyle(resultsOverlay).display !== 'none') {
            if (!watchdogState.secondAdStarted) {
                watchdogState.secondAdStarted = true;
                watchdogState.startTime = Date.now();
                console.log('Watchdog: Second ad started at ' + new Date().toISOString());
                
                // Mark first ad as complete if we got here
                watchdogState.firstAdCompleted = true;
            }
            
            // Check if we've been in the second ad too long
            const timeInSecondAd = Date.now() - watchdogState.startTime;
            if (timeInSecondAd > watchdogConfig.secondAdMaxTime) {
                console.warn('Watchdog: Second ad has been shown for too long, force showing results');
                
                // Force hide second ad
                resultsOverlay.style.display = 'none';
                
                // Force show results container
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer && window.lastResultsData) {
                    console.log('Watchdog: Forcibly showing results container');
                    resultsContainer.classList.remove('d-none');
                    resultsContainer.style.display = 'block';
                    
                    // If there's a displayResults function, call it
                    if (typeof window.displayResults === 'function' && window.lastResultsData) {
                        console.log('Watchdog: Calling displayResults with cached data');
                        window.displayResults(window.lastResultsData);
                    }
                }
                
                watchdogState.secondAdCompleted = true;
            }
        } 
        // If neither overlay is shown, consider the process complete
        else {
            if (watchdogState.firstAdStarted && !watchdogState.firstAdCompleted) {
                console.log('Watchdog: First ad completed normally');
                watchdogState.firstAdCompleted = true;
            }
            
            if (watchdogState.secondAdStarted && !watchdogState.secondAdCompleted) {
                console.log('Watchdog: Second ad completed normally');
                watchdogState.secondAdCompleted = true;
            }
        }
        
        // If we've completed the process, or run for too long, stop the watchdog
        if ((watchdogState.firstAdCompleted && watchdogState.secondAdCompleted) || 
            watchdogState.intervalsRun > 60) { // Stop after 60 seconds max
            console.log('Watchdog: Scan process completed or timed out, stopping');
            stopWatchdog();
        }
    }
    
    // Start the watchdog
    function startWatchdog() {
        // Reset state
        watchdogState = {
            startTime: Date.now(),
            firstAdStarted: false,
            firstAdCompleted: false,
            secondAdStarted: false,
            secondAdCompleted: false,
            intervalsRun: 0
        };
        
        // Only start if not already running
        if (!watchdogConfig.running) {
            console.log('Watchdog: Starting scan process monitor');
            watchdogConfig.running = true;
            watchdogConfig.intervalId = setInterval(monitorScanProcess, watchdogConfig.checkInterval);
        }
    }
    
    // Stop the watchdog
    function stopWatchdog() {
        if (watchdogConfig.running) {
            console.log('Watchdog: Stopping scan process monitor');
            clearInterval(watchdogConfig.intervalId);
            watchdogConfig.running = false;
        }
    }
    
    // Watch for scan button clicks to start the watchdog
    document.addEventListener('DOMContentLoaded', function() {
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', function() {
                console.log('Watchdog: Scan button clicked, starting watchdog');
                startWatchdog();
            });
        }
        
        // Also add a global failsafe command for the console
        window.forceAdvanceToResults = function() {
            console.log('Manual force advancement to results initiated');
            
            // Hide all ad overlays
            const overlays = document.querySelectorAll('[id^="ad-overlay"]');
            overlays.forEach(overlay => {
                overlay.style.display = 'none';
            });
            
            // Force show results if we have data
            if (window.lastResultsData) {
                // Show results container
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.classList.remove('d-none');
                    resultsContainer.style.display = 'block';
                }
                
                // Call display results function if available
                if (typeof window.displayResults === 'function') {
                    window.displayResults(window.lastResultsData);
                }
            }
            
            return "Results forcibly displayed";
        };
    });
})();