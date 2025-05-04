/**
 * Scan Advancement Fix - iOS Specific
 * Ensures the scanning process advances from the loading advertisement to results
 * Handles cases where the process gets stuck in a loop on mobile devices
 */
 
document.addEventListener('DOMContentLoaded', function() {
    // Track the scan state
    let scanState = {
        scanning: false,
        processingStarted: null,
        stuckTimeout: null,
        processingFinished: false,
        advancementAttempts: 0
    };

    // Force advancement after timeout
    function setupStuckDetection() {
        // Clear any existing stuck detection
        if (scanState.stuckTimeout) {
            clearTimeout(scanState.stuckTimeout);
        }
        
        // Set up timeout to detect if scanning is stuck
        scanState.stuckTimeout = setTimeout(function() {
            console.log('Stuck detection activated - checking if scanning is stuck');
            
            // If we're still in scanning mode after 20 seconds, force advancement
            if (scanState.scanning && !scanState.processingFinished) {
                console.log('STUCK DETECTED: Forcing advancement to next ad stage');
                scanState.advancementAttempts++;
                
                // Force hide the loading overlay
                const adOverlayLoading = document.getElementById('ad-overlay-loading');
                if (adOverlayLoading) {
                    console.log('Forcibly hiding loading overlay');
                    adOverlayLoading.style.display = 'none';
                }
                
                // Force show the results overlay
                const adOverlayResults = document.getElementById('ad-overlay-results');
                if (adOverlayResults) {
                    console.log('Forcibly showing results overlay');
                    adOverlayResults.style.display = 'flex';
                }
                
                // If we have stored results data and we're still stuck, force display results
                if (window.lastResultsData && scanState.advancementAttempts > 1) {
                    console.log('Multiple advancement attempts failed - forcing direct display of results');
                    displayResults(window.lastResultsData);
                    
                    // Reset scan state
                    scanState.scanning = false;
                    scanState.processingFinished = true;
                }
            }
        }, 20000); // 20 second timeout
    }

    // Override the processTicketWithAds function to track scanning state
    const originalProcessTicketWithAds = window.processTicketWithAds;
    window.processTicketWithAds = function() {
        console.log('Enhanced processTicketWithAds called with tracking');
        
        // Set scanning state
        scanState.scanning = true;
        scanState.processingStarted = new Date();
        scanState.processingFinished = false;
        scanState.advancementAttempts = 0;
        
        // Set up stuck detection
        setupStuckDetection();
        
        // Call original function
        if (typeof originalProcessTicketWithAds === 'function') {
            originalProcessTicketWithAds();
        }
    };
    
    // Also monitor the View Results button to ensure it works
    document.body.addEventListener('click', function(e) {
        // Look for clicks on the view results button
        if (e.target && (e.target.id === 'view-results-btn' || e.target.closest('#view-results-btn'))) {
            console.log('View Results button click detected by observer');
            
            // If we have results data, make sure it's displayed
            if (window.lastResultsData) {
                scanState.processingFinished = true;
                
                // Force removal of overlays
                const adOverlayLoading = document.getElementById('ad-overlay-loading');
                if (adOverlayLoading) {
                    adOverlayLoading.style.display = 'none';
                }
                
                const adOverlayResults = document.getElementById('ad-overlay-results');
                if (adOverlayResults) {
                    adOverlayResults.style.display = 'none';
                }
                
                // Force display of results
                displayResults(window.lastResultsData);
            }
        }
    });
    
    // Add a global emergency function to force advance
    window.forceAdvanceScanProcess = function() {
        console.log('EMERGENCY: Manual force advancement triggered');
        
        // Hide loading overlay
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading) {
            adOverlayLoading.style.display = 'none';
        }
        
        // Show results overlay
        const adOverlayResults = document.getElementById('ad-overlay-results');
        if (adOverlayResults) {
            adOverlayResults.style.display = 'flex';
        }
        
        // If we have data, force display
        if (window.lastResultsData) {
            displayResults(window.lastResultsData);
        }
    };
    
    // Set up emergency timeout to force advancement regardless of other conditions
    setTimeout(function() {
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading && adOverlayLoading.style.display !== 'none') {
            console.log('EMERGENCY TIMEOUT: Loading overlay still visible after 30s, forcing advancement');
            window.forceAdvanceScanProcess();
        }
    }, 30000);
});