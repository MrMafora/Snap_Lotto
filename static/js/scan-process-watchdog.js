/**
 * Scan Process Watchdog
 * Ensures the ticket scanning process doesn't get stuck
 * and advances if needed
 */

(function() {
    console.log('Scan process watchdog initializing');
    
    // Global variables to track the scan process
    let scanStarted = false;
    let scanCompleted = false;
    let processingTimeout = null;
    let scanStartTime = null;
    
    // Constants for timeout values
    const MAX_SCAN_TIME = 45000; // 45 seconds
    const CHECK_INTERVAL = 3000; // 3 seconds
    const WATCHDOG_CHECK_INTERVAL = 5000; // 5 seconds
    
    // Function to check and advance stuck processes
    function checkScanProgress() {
        if (!scanStarted) {
            return; // Nothing to check yet
        }
        
        // Get relevant elements
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        const adOverlayResults = document.getElementById('ad-overlay-results');
        const resultsContainer = document.getElementById('results-container');
        
        // Calculate elapsed time
        const elapsedTime = Date.now() - scanStartTime;
        
        // If the scan has been running for too long, force completion
        if (elapsedTime > MAX_SCAN_TIME && !scanCompleted) {
            console.log(`WATCHDOG: Scan running for ${Math.round(elapsedTime/1000)}s, force advancing`);
            
            // Hide loading overlay
            if (adOverlayLoading && adOverlayLoading.style.display === 'flex') {
                adOverlayLoading.style.display = 'none';
                
                // Force show the results overlay to at least show an ad
                if (adOverlayResults) {
                    adOverlayResults.style.display = 'flex';
                    console.log('WATCHDOG: Forced transition to results ad');
                    
                    // Try to initialize the countdown if needed
                    const countdownContainer = document.getElementById('countdown-container');
                    const viewResultsBtn = document.getElementById('view-results-btn');
                    
                    if (countdownContainer && viewResultsBtn) {
                        if (!countdownContainer.innerText || countdownContainer.innerText.trim() === '') {
                            countdownContainer.innerText = 'Wait 15s';
                            viewResultsBtn.innerText = 'Wait 15s';
                            viewResultsBtn.disabled = true;
                            console.log('WATCHDOG: Initialized countdown');
                        }
                    }
                }
            }
            
            // Mark as completed to avoid repeated force completions
            scanCompleted = true;
        }
    }
    
    // Watch for scan process to start
    function watchForScanStart() {
        const ticketForm = document.getElementById('ticket-form');
        const scanButton = document.getElementById('scan-button');
        
        if (ticketForm && scanButton) {
            // Watch for form submission
            ticketForm.addEventListener('submit', function() {
                scanStarted = true;
                scanCompleted = false;
                scanStartTime = Date.now();
                console.log('WATCHDOG: Scan process started');
                
                // Set a timeout to check for scan completion
                processingTimeout = setTimeout(() => {
                    if (!scanCompleted) {
                        console.log('WATCHDOG: Initial scan timeout reached, checking status');
                        checkScanProgress();
                    }
                }, MAX_SCAN_TIME / 2); // Check halfway through max time
            });
            
            // Also watch for direct button click
            scanButton.addEventListener('click', function() {
                // Only set if not already tracking
                if (!scanStarted) {
                    scanStarted = true;
                    scanCompleted = false;
                    scanStartTime = Date.now();
                    console.log('WATCHDOG: Scan button clicked, tracking started');
                }
            });
            
            console.log('WATCHDOG: Scan start monitoring initialized');
        }
    }
    
    // Watch for scan process completion
    function watchForScanCompletion() {
        const viewResultsBtn = document.getElementById('view-results-btn');
        
        if (viewResultsBtn) {
            // Watch for "View Results" button click
            viewResultsBtn.addEventListener('click', function() {
                scanCompleted = true;
                console.log('WATCHDOG: Scan process marked as completed via button click');
                
                // Clear any existing timeout
                if (processingTimeout) {
                    clearTimeout(processingTimeout);
                    processingTimeout = null;
                }
            });
            
            console.log('WATCHDOG: Scan completion monitoring initialized');
        }
    }
    
    // Watch for ad overlay changes
    function watchAdOverlays() {
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        const adOverlayResults = document.getElementById('ad-overlay-results');
        
        if (adOverlayLoading && adOverlayResults) {
            // Create observers for each overlay
            const loadingObserver = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                        if (adOverlayLoading.style.display === 'none' && adOverlayResults.style.display === 'flex') {
                            // This indicates we've transitioned from first ad to second ad
                            console.log('WATCHDOG: Observed transition to second ad');
                        }
                    }
                });
            });
            
            const resultsObserver = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                        if (adOverlayResults.style.display === 'none') {
                            // This indicates the second ad was closed
                            scanCompleted = true;
                            console.log('WATCHDOG: Observed second ad closing, marking scan as complete');
                        }
                    }
                });
            });
            
            // Start observing
            loadingObserver.observe(adOverlayLoading, { attributes: true });
            resultsObserver.observe(adOverlayResults, { attributes: true });
            console.log('WATCHDOG: Ad overlay observers initialized');
        }
    }
    
    // Start the watchdog periodic check
    function startWatchdogTimer() {
        // Set up periodic check
        setInterval(checkScanProgress, WATCHDOG_CHECK_INTERVAL);
        console.log('WATCHDOG: Timer started');
    }
    
    // Initialize everything when the DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Set up all the watchers
        watchForScanStart();
        watchForScanCompletion();
        watchAdOverlays();
        startWatchdogTimer();
        
        console.log('WATCHDOG: Scan process monitoring fully initialized');
    });
    
    // Provide global debugging tools
    window.debugScanWatchdog = function() {
        return {
            scanStarted,
            scanCompleted,
            scanStartTime,
            elapsedTime: scanStartTime ? Date.now() - scanStartTime : 0,
            maxScanTime: MAX_SCAN_TIME
        };
    };
    
    // Provide global function to force scan completion for stuck scans
    window.forceScanCompletion = function() {
        scanCompleted = true;
        
        // Force hiding of all overlays
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        const adOverlayResults = document.getElementById('ad-overlay-results');
        
        if (adOverlayLoading) {
            adOverlayLoading.style.display = 'none';
        }
        
        if (adOverlayResults) {
            adOverlayResults.style.display = 'none';
        }
        
        // Clear any existing timeout
        if (processingTimeout) {
            clearTimeout(processingTimeout);
            processingTimeout = null;
        }
        
        console.log('WATCHDOG: Manually forced scan completion');
        return 'Scan process forcefully completed';
    };
    
    console.log('Scan process watchdog loaded');
})();