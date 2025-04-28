/**
 * Scan Process Watchdog
 * 
 * This script monitors the scanning process and ensures it advances properly,
 * preventing the system from getting stuck in any state.
 * 
 * Features:
 * - Detects stalled scanning processes
 * - Forces advancement if stuck in loading ad
 * - Ensures results are always shown after processing
 * - Prevents infinite loops in the scan process
 */

(function() {
    'use strict';
    
    console.log('Scan process watchdog initializing');
    
    // Watchdog configuration
    const WATCHDOG_CONFIG = {
        checkInterval: 2000,         // How often to check status (milliseconds)
        maxLoadingTime: 30000,       // Maximum time allowed in loading state (30 seconds)
        maxProcessingTime: 60000,    // Maximum time for entire scan process (60 seconds)
        maxAdDisplayTime: 20000      // Maximum time for any ad to display (20 seconds)
    };
    
    // State tracking
    let watchdogState = {
        scanStarted: false,
        scanStartTime: null,
        adDisplayStartTime: null,
        resultsDisplayed: false,
        stuckDetected: false,
        recoveryAttempts: 0,
        maxRecoveryAttempts: 3
    };
    
    // Start the watchdog monitoring
    function startWatchdog() {
        console.log('Scan process watchdog started');
        
        // Reset state when starting
        resetWatchdogState();
        
        // Set up interval to check scan process
        const watchdogInterval = setInterval(monitorScanProcess, WATCHDOG_CONFIG.checkInterval);
        
        // Store interval reference
        watchdogState.interval = watchdogInterval;
    }
    
    // Reset watchdog state 
    function resetWatchdogState() {
        watchdogState = {
            scanStarted: false,
            scanStartTime: null,
            adDisplayStartTime: null,
            resultsDisplayed: false,
            stuckDetected: false,
            recoveryAttempts: 0,
            maxRecoveryAttempts: 3,
            interval: null
        };
    }
    
    // Monitor scan process and detect issues
    function monitorScanProcess() {
        // Check if a scan is in progress
        const scanInProgress = detectScanInProgress();
        
        if (scanInProgress && !watchdogState.scanStarted) {
            // Scan just started
            watchdogState.scanStarted = true;
            watchdogState.scanStartTime = Date.now();
            watchdogState.adDisplayStartTime = Date.now();
            console.log('Watchdog detected scan start at:', new Date().toISOString());
        }
        
        // Don't proceed with checks if no scan is happening
        if (!watchdogState.scanStarted) {
            return;
        }
        
        // Check for stuck loading ad
        if (isLoadingAdStuck()) {
            handleStuckLoadingAd();
        }
        
        // Check for stuck results ad
        if (isResultsAdStuck()) {
            handleStuckResultsAd();
        }
        
        // Check if the entire process is taking too long
        if (isEntireProcessStuck()) {
            handleStuckProcess();
        }
        
        // Check if we should be showing results but aren't
        if (shouldShowResults() && !watchdogState.resultsDisplayed) {
            forceShowResults();
        }
    }
    
    // Detect if a scan is in progress
    function detectScanInProgress() {
        // Check for visible ad overlays
        const loadingAdVisible = document.getElementById('ad-overlay-loading') && 
                                 document.getElementById('ad-overlay-loading').style.display !== 'none';
        
        const resultsAdVisible = document.getElementById('ad-overlay-results') && 
                                 document.getElementById('ad-overlay-results').style.display !== 'none';
        
        // Also check for results container having content
        const hasResults = document.getElementById('results-container') && 
                          !document.getElementById('results-container').classList.contains('d-none');
        
        return loadingAdVisible || resultsAdVisible || hasResults;
    }
    
    // Check if loading ad is stuck
    function isLoadingAdStuck() {
        const loadingAdVisible = document.getElementById('ad-overlay-loading') && 
                               document.getElementById('ad-overlay-loading').style.display !== 'none';
        
        if (!loadingAdVisible) {
            return false;
        }
        
        // Check time in this state
        const timeInState = Date.now() - watchdogState.adDisplayStartTime;
        return timeInState > WATCHDOG_CONFIG.maxAdDisplayTime;
    }
    
    // Check if results ad is stuck
    function isResultsAdStuck() {
        const resultsAdVisible = document.getElementById('ad-overlay-results') && 
                               document.getElementById('ad-overlay-results').style.display !== 'none';
        
        if (!resultsAdVisible) {
            return false;
        }
        
        // Check time in this state
        const timeInState = Date.now() - watchdogState.adDisplayStartTime;
        return timeInState > WATCHDOG_CONFIG.maxAdDisplayTime;
    }
    
    // Check if entire process is stuck
    function isEntireProcessStuck() {
        if (!watchdogState.scanStartTime) {
            return false;
        }
        
        const totalProcessTime = Date.now() - watchdogState.scanStartTime;
        return totalProcessTime > WATCHDOG_CONFIG.maxProcessingTime;
    }
    
    // Determine if results should be showing
    function shouldShowResults() {
        // If we have results populated, we should display them
        const resultsContainer = document.getElementById('results-container');
        
        if (!resultsContainer) {
            return false;
        }
        
        // Check if we have ticket numbers displayed
        const hasTicketNumbers = document.getElementById('ticket-numbers') && 
                               document.getElementById('ticket-numbers').children.length > 0;
        
        // Check if we have winning numbers displayed
        const hasWinningNumbers = document.getElementById('winning-numbers') && 
                               document.getElementById('winning-numbers').children.length > 0;
        
        return hasTicketNumbers || hasWinningNumbers;
    }
    
    // Handle stuck loading ad
    function handleStuckLoadingAd() {
        if (watchdogState.recoveryAttempts >= watchdogState.maxRecoveryAttempts) {
            console.warn('Watchdog: Maximum recovery attempts reached for loading ad, forcing process reset');
            forceResetScanProcess();
            return;
        }
        
        console.warn('Watchdog: Loading ad appears stuck, attempting recovery');
        watchdogState.recoveryAttempts++;
        watchdogState.stuckDetected = true;
        
        // Force hide the loading overlay
        const loadingOverlay = document.getElementById('ad-overlay-loading');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
        
        // Force show the results overlay
        const resultsOverlay = document.getElementById('ad-overlay-results');
        if (resultsOverlay) {
            resultsOverlay.style.display = 'flex';
            watchdogState.adDisplayStartTime = Date.now(); // Reset timer for next stage
        }
        
        console.log('Watchdog: Forced transition from loading ad to results ad');
    }
    
    // Handle stuck results ad
    function handleStuckResultsAd() {
        if (watchdogState.recoveryAttempts >= watchdogState.maxRecoveryAttempts) {
            console.warn('Watchdog: Maximum recovery attempts reached for results ad, forcing process reset');
            forceResetScanProcess();
            return;
        }
        
        console.warn('Watchdog: Results ad appears stuck, attempting recovery');
        watchdogState.recoveryAttempts++;
        watchdogState.stuckDetected = true;
        
        // Force hide the results overlay
        const resultsOverlay = document.getElementById('ad-overlay-results');
        if (resultsOverlay) {
            resultsOverlay.style.display = 'none';
        }
        
        // Ensure the results container is visible
        forceShowResults();
        
        console.log('Watchdog: Forced transition from results ad to results display');
    }
    
    // Handle stuck entire process
    function handleStuckProcess() {
        console.warn('Watchdog: Entire scan process appears stuck, forcing reset');
        forceResetScanProcess();
    }
    
    // Force results to show
    function forceShowResults() {
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
            resultsContainer.style.display = 'block';
            
            // Hide all possible ad overlays
            const adOverlays = document.querySelectorAll('[id^="ad-overlay"]');
            adOverlays.forEach(overlay => {
                overlay.style.display = 'none';
            });
            
            watchdogState.resultsDisplayed = true;
            console.log('Watchdog: Forced results to display');
            
            // Ensure body scrolling is enabled
            document.body.style.overflow = '';
        }
    }
    
    // Force reset of entire scan process
    function forceResetScanProcess() {
        // Hide all overlays
        const adOverlays = document.querySelectorAll('[id^="ad-overlay"]');
        adOverlays.forEach(overlay => {
            overlay.style.display = 'none';
        });
        
        // Reset the form if possible
        const ticketForm = document.getElementById('ticket-form');
        if (ticketForm) {
            ticketForm.reset();
        }
        
        // Show the drop area
        const dropArea = document.getElementById('drop-area');
        if (dropArea) {
            dropArea.classList.remove('d-none');
        }
        
        // Hide the preview container
        const previewContainer = document.getElementById('preview-container');
        if (previewContainer) {
            previewContainer.classList.add('d-none');
        }
        
        // Ensure body scrolling is enabled
        document.body.style.overflow = '';
        
        // Reset watchdog state
        resetWatchdogState();
        
        console.log('Watchdog: Forced complete scan process reset');
    }
    
    // Attach to scan button
    function attachToScanButton() {
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', function() {
                // Reset watchdog state when starting new scan
                resetWatchdogState();
                startWatchdog();
            });
            
            console.log('Watchdog: Attached to scan button');
        }
    }
    
    // Initialize watchdog on page load
    document.addEventListener('DOMContentLoaded', function() {
        attachToScanButton();
        console.log('Scan process watchdog initialized');
        
        // Expose emergency functions to console for manual recovery
        window.emergencyResetScan = forceResetScanProcess;
        window.emergencyShowResults = forceShowResults;
    });
})();