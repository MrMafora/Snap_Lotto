/**
 * Scan Process Watchdog
 * 
 * This script monitors the scanning process and ensures users don't get stuck.
 * It forces progression if the system detects the process is stalled.
 * 
 * Features:
 * - Monitors the entire scan process from start to finish
 * - Detects when timers, ads, or transitions get stuck
 * - Forces advancement after specific timeouts
 * - Logs detailed diagnostic information for debugging
 */

(function() {
    'use strict';
    
    console.log('Scan process watchdog initializing');
    
    // Configuration
    const config = {
        scanTimeout: 30000,             // 30 seconds max for scanning process
        firstAdMinTime: 15000,          // 15 seconds minimum for first ad
        firstAdMaxTime: 25000,          // 25 seconds maximum for first ad (force advance)
        secondAdMinTime: 15000,         // 15 seconds minimum for second ad
        secondAdMaxTime: 25000,         // 25 seconds maximum for second ad (force advance)
        checkInterval: 2000,            // Check every 2 seconds
        buttonCheckInterval: 5000,      // Check button state every 5 seconds
        monitorStartDelay: 1000         // Start monitoring after 1 second
    };
    
    // State tracking
    let state = {
        scanStartTime: null,            // When scan button was clicked
        firstAdStartTime: null,         // When first ad started showing
        secondAdStartTime: null,        // When second ad started showing
        scanComplete: false,            // Has scanning completed?
        firstAdShown: false,            // Has first ad been shown?
        firstAdComplete: false,         // Has first ad display completed?
        secondAdShown: false,           // Has second ad been shown?
        secondAdComplete: false,        // Has second ad display completed?
        resultsDisplayed: false,        // Have final results been displayed?
        forcedReset: false,             // Has the process been force reset?
        intervalId: null                // Reference to the monitoring interval
    };
    
    // Initialize the watchdog
    function initialize() {
        // Set up monitoring interval
        state.intervalId = setInterval(monitorScanProcess, config.checkInterval);
        
        // Set up button check interval
        setInterval(checkButtonState, config.buttonCheckInterval);
        
        // Attach to scan button
        attachToScanButton();
        
        console.log('Scan process watchdog initialized');
    }
    
    // Attach events to the scan button
    function attachToScanButton() {
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            // Add event listener to capture when scanning starts
            scanButton.addEventListener('click', function() {
                // Reset state
                resetState();
                
                // Record start time
                state.scanStartTime = Date.now();
                
                console.log('Watchdog detected scan start at:', new Date(state.scanStartTime).toISOString());
            });
        }
    }
    
    // Monitor the entire scan process
    function monitorScanProcess() {
        // Skip if scan hasn't started
        if (!state.scanStartTime) return;
        
        const now = Date.now();
        const scanElapsedTime = now - state.scanStartTime;
        
        // Check if first ad is showing
        if (!state.firstAdShown && isFirstAdShowing()) {
            state.firstAdShown = true;
            state.firstAdStartTime = now;
            console.log('Watchdog detected first ad shown at:', new Date(state.firstAdStartTime).toISOString());
        }
        
        // Check if second ad is showing
        if (!state.secondAdShown && isSecondAdShowing()) {
            state.secondAdShown = true;
            state.secondAdStartTime = now;
            console.log('Watchdog detected second ad shown at:', new Date(state.secondAdStartTime).toISOString());
        }
        
        // Check if scan is taking too long
        if (!state.firstAdShown && scanElapsedTime > config.scanTimeout) {
            console.warn('Watchdog: Entire scan process appears stuck, forcing reset');
            forceResetScanProcess();
            return;
        }
        
        // Check if first ad has been shown too long
        if (state.firstAdShown && !state.secondAdShown) {
            const firstAdElapsedTime = now - state.firstAdStartTime;
            
            if (firstAdElapsedTime > config.firstAdMaxTime) {
                console.warn('Watchdog: First ad shown too long, forcing advance to second ad');
                forceAdvanceToSecondAd();
            }
        }
        
        // Check if second ad has been shown too long
        if (state.secondAdShown && !state.resultsDisplayed) {
            const secondAdElapsedTime = now - state.secondAdStartTime;
            
            if (secondAdElapsedTime > config.secondAdMaxTime) {
                console.warn('Watchdog: Second ad shown too long, forcing display of results');
                forceDisplayResults();
            }
        }
    }
    
    // Check for stuck buttons
    function checkButtonState() {
        const now = Date.now();
        
        // Check if first ad shown long enough but button still disabled
        if (state.firstAdShown && !state.secondAdShown && state.firstAdStartTime) {
            const firstAdElapsedTime = now - state.firstAdStartTime;
            
            if (firstAdElapsedTime > config.firstAdMinTime) {
                console.log('Mobile button check: More than 15s since countdown start, checking for stuck buttons');
                
                // Find the view results button
                const viewResultsBtn = document.getElementById('view-results-btn');
                if (viewResultsBtn && viewResultsBtn.disabled && firstAdElapsedTime > config.firstAdMinTime) {
                    console.warn('Watchdog: View Results button still disabled after min time, forcing enable');
                    enableViewResultsButton();
                }
            }
        }
        
        // Check if second ad shown long enough but button still disabled
        if (state.secondAdShown && !state.resultsDisplayed && state.secondAdStartTime) {
            const secondAdElapsedTime = now - state.secondAdStartTime;
            
            if (secondAdElapsedTime > config.secondAdMinTime) {
                // Find the continue button
                const continueBtn = document.getElementById('view-results-btn');
                if (continueBtn && continueBtn.disabled && secondAdElapsedTime > config.secondAdMinTime) {
                    console.warn('Watchdog: Continue button still disabled after min time, forcing enable');
                    enableContinueButton();
                }
            }
        }
    }
    
    // Force reset the entire scan process
    function forceResetScanProcess() {
        console.log('Watchdog: Forced complete scan process reset');
        
        // Reset state
        resetState();
        state.forcedReset = true;
        
        // Hide all overlays
        hideAllOverlays();
        
        // Reset scan form
        resetScanForm();
    }
    
    // Force advance to second ad
    function forceAdvanceToSecondAd() {
        console.log('Watchdog: Forcing advance to second ad');
        
        // Enable View Results button
        enableViewResultsButton();
        
        // Simulate click after a short delay
        setTimeout(function() {
            const viewResultsBtn = document.getElementById('view-results-btn');
            if (viewResultsBtn) {
                viewResultsBtn.click();
            }
        }, 500);
    }
    
    // Force display of final results
    function forceDisplayResults() {
        console.log('Watchdog: Forcing display of final results');
        
        // Enable Continue button
        enableContinueButton();
        
        // Simulate click after a short delay
        setTimeout(function() {
            const continueBtn = document.getElementById('view-results-btn');
            if (continueBtn) {
                continueBtn.click();
            }
        }, 500);
        
        // Mark as completed
        state.resultsDisplayed = true;
    }
    
    // Check if first ad is showing
    function isFirstAdShowing() {
        const overlay = document.getElementById('ad-overlay-loading');
        return overlay && overlay.style.display === 'flex';
    }
    
    // Check if second ad is showing
    function isSecondAdShowing() {
        const overlay = document.getElementById('ad-overlay-results');
        return overlay && overlay.style.display === 'flex';
    }
    
    // Enable the View Results button for first ad
    function enableViewResultsButton() {
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            viewResultsBtn.disabled = false;
            viewResultsBtn.classList.remove('btn-secondary');
            viewResultsBtn.classList.add('btn-success');
            viewResultsBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
            
            // Update our state
            state.firstAdComplete = true;
            
            // Also update the ad manager state if available
            if (window.SnapLottoAds) {
                window.SnapLottoAds.firstAdComplete = true;
            }
        }
    }
    
    // Enable the Continue button for second ad
    function enableContinueButton() {
        const continueBtn = document.getElementById('view-results-btn');
        if (continueBtn) {
            continueBtn.disabled = false;
            continueBtn.classList.remove('btn-secondary');
            continueBtn.classList.add('btn-success');
            continueBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> Continue to Results!';
            
            // Update our state
            state.secondAdComplete = true;
            
            // Also update the ad manager state if available
            if (window.SnapLottoAds) {
                window.SnapLottoAds.secondAdComplete = true;
            }
        }
    }
    
    // Hide all overlay elements
    function hideAllOverlays() {
        const overlays = [
            document.getElementById('ad-overlay-loading'),
            document.getElementById('ad-overlay-results')
        ];
        
        overlays.forEach(function(overlay) {
            if (overlay) {
                overlay.style.display = 'none';
            }
        });
    }
    
    // Reset scan form to initial state
    function resetScanForm() {
        const scanForm = document.getElementById('ticket-form');
        if (scanForm) {
            scanForm.reset();
        }
        
        const previewContainer = document.getElementById('preview-container');
        if (previewContainer) {
            previewContainer.classList.add('d-none');
        }
        
        const scannerLoading = document.getElementById('scanner-loading');
        if (scannerLoading) {
            scannerLoading.style.display = 'none';
        }
    }
    
    // Reset watchdog state
    function resetState() {
        state = {
            scanStartTime: null,
            firstAdStartTime: null,
            secondAdStartTime: null,
            scanComplete: false,
            firstAdShown: false,
            firstAdComplete: false,
            secondAdShown: false,
            secondAdComplete: false,
            resultsDisplayed: false,
            forcedReset: false,
            intervalId: state.intervalId
        };
    }
    
    // Initialize after a short delay to let other scripts load
    setTimeout(initialize, config.monitorStartDelay);
})();