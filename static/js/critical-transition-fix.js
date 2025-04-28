/**
 * Critical Ad Transition Fix
 * Ensures smooth transitions between the first and second ads
 * Optimized for mobile performance and reliability
 */

(function() {
    console.log('Critical transition fix loading');
    
    // Global state tracking variables
    let firstAdShown = false;
    let secondAdShown = false;
    let transitionInProgress = false;
    
    // Log state changes to help debug
    function logTransitionState(message) {
        console.log(`TRANSITION: ${message} (first: ${firstAdShown}, second: ${secondAdShown})`);
    }
    
    // Function to ensure the transition between ads happens correctly
    function ensureAdTransition() {
        if (transitionInProgress) {
            return; // Don't interrupt an active transition
        }
        
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        const adOverlayResults = document.getElementById('ad-overlay-results');
        
        // If first ad is shown but second isn't yet
        if (firstAdShown && !secondAdShown && adOverlayLoading && adOverlayLoading.style.display === 'flex') {
            logTransitionState('First ad detected, preparing transition to second ad');
            
            transitionInProgress = true;
            
            // Force transition to second ad
            setTimeout(() => {
                logTransitionState('Forcing transition to second ad');
                
                // Hide the first ad overlay
                adOverlayLoading.style.display = 'none';
                
                // Show the second ad overlay
                if (adOverlayResults) {
                    adOverlayResults.style.display = 'flex';
                    secondAdShown = true;
                    
                    // Make sure countdown is shown and running
                    ensureCountdownVisible();
                }
                
                transitionInProgress = false;
            }, 500);
        }
    }
    
    // Function to ensure countdown is visible and working
    function ensureCountdownVisible() {
        const countdownContainer = document.getElementById('countdown-container');
        const viewResultsBtn = document.getElementById('view-results-btn');
        
        if (countdownContainer && viewResultsBtn) {
            // If the countdown container is empty, initialize it
            if (!countdownContainer.innerText || countdownContainer.innerText.trim() === '') {
                countdownContainer.innerText = 'Wait 15s';
                
                // Also update button text to match
                if (!viewResultsBtn.innerText.includes('Wait')) {
                    const originalText = viewResultsBtn.innerText;
                    viewResultsBtn.innerText = 'Wait 15s';
                    viewResultsBtn.setAttribute('data-original-text', originalText);
                }
                
                // Ensure button is disabled during countdown
                viewResultsBtn.disabled = true;
                
                logTransitionState('Countdown initialized');
            }
        }
    }
    
    // Watch for the first ad being shown
    function watchFirstAdDisplay() {
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        
        if (adOverlayLoading) {
            // Create a mutation observer to watch for the first ad display changes
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                        const displayStyle = adOverlayLoading.style.display;
                        
                        if (displayStyle === 'flex' && !firstAdShown) {
                            firstAdShown = true;
                            logTransitionState('First ad now displayed');
                            
                            // Set a backup timer to ensure transition happens
                            setTimeout(() => {
                                if (!secondAdShown) {
                                    logTransitionState('Backup timer triggering transition');
                                    ensureAdTransition();
                                }
                            }, 15000); // 15 second backup
                        }
                    }
                });
            });
            
            // Start observing
            observer.observe(adOverlayLoading, { attributes: true });
            logTransitionState('First ad observer started');
        }
    }
    
    // Watch for scanning process to complete
    function watchScanProcess() {
        // If the processTicketWithAds function exists, enhance it
        if (window.processTicketWithAds) {
            const originalFunction = window.processTicketWithAds;
            
            window.processTicketWithAds = function() {
                // Reset the ad display tracking
                firstAdShown = false;
                secondAdShown = false;
                transitionInProgress = false;
                logTransitionState('Ad state reset for new scan');
                
                // Call the original function
                originalFunction.apply(this, arguments);
            };
            
            logTransitionState('Scan process function enhanced');
        }
    }
    
    // Initialize everything when the DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Start watching for the first ad display
        watchFirstAdDisplay();
        
        // Enhance the scan process
        watchScanProcess();
        
        // Set up periodic transition check
        setInterval(ensureAdTransition, 2000);
        
        logTransitionState('Transition monitoring initialized');
    });
    
    // Emergency transition function that can be called from console for debugging
    window.forceAdTransition = function() {
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        const adOverlayResults = document.getElementById('ad-overlay-results');
        
        if (adOverlayLoading) {
            adOverlayLoading.style.display = 'none';
        }
        
        if (adOverlayResults) {
            adOverlayResults.style.display = 'flex';
            ensureCountdownVisible();
        }
        
        logTransitionState('EMERGENCY transition force-triggered');
        return 'Ad transition forced';
    };
    
    // Emergency function to fix a stuck button
    window.fixStuckButton = function() {
        const viewResultsBtn = document.getElementById('view-results-btn');
        
        if (viewResultsBtn) {
            // Read the original text or use a default
            const originalText = viewResultsBtn.getAttribute('data-original-text') || 'View Results';
            
            // Reset the button
            viewResultsBtn.innerText = originalText;
            viewResultsBtn.disabled = false;
            viewResultsBtn.classList.add('btn-pulse');
            
            logTransitionState('EMERGENCY button reset triggered');
            return 'Button has been reset';
        }
        
        return 'Button not found';
    };
    
    console.log('Critical transition fix loaded');
})();