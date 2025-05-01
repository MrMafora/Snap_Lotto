/**
 * Advertisement Countdown Fix
 * 
 * This script fixes the following issues with the advertisement system:
 * 1. Changes first ad duration from variable time to exactly 5 seconds
 * 2. Prevents View Results button from becoming active before countdown completes
 * 3. Resolves the "AdManager: First ad complete, enabling view results button" logging issue
 * 4. Coordinates ad sequence between mobile and desktop implementations
 */
(function() {
    'use strict';

    console.log('Advertisement countdown fix loaded');
    
    // Configuration
    const config = {
        firstAdDuration: 5,         // First ad duration in seconds (FIXED to 5 seconds exactly)
        secondAdDuration: 15,       // Second ad duration in seconds
        strictMode: true            // Enforce strict compliance with minimum duration
    };
    
    // State tracking
    let state = {
        firstAdStartTime: null,     // When first ad started showing
        secondAdStartTime: null,    // When second ad started showing
        firstAdComplete: false,     // Is first ad display complete?
        secondAdComplete: false,    // Is second ad display complete?
        viewResultsEnabled: false,  // Is the View Results button enabled?
        adSequenceComplete: false   // Is the entire ad sequence complete?
    };
    
    // Initialization
    document.addEventListener('DOMContentLoaded', initialize);
    
    // Initialize and setup
    function initialize() {
        // Wait for page to be fully loaded
        window.addEventListener('load', function() {
            // Override the SnapLottoAds configuration if it exists
            if (window.SnapLottoAds) {
                console.log('Overriding SnapLottoAds configuration');
                
                // Change first ad duration in the global config
                window.SnapLottoAds.adMinimumTime = config.firstAdDuration * 1000;
                
                // Backup original enableViewResultsButton function if it exists
                if (window.enableViewResultsButton) {
                    const originalEnableFunc = window.enableViewResultsButton;
                    
                    // Override with our own version that enforces timing
                    window.enableViewResultsButton = function() {
                        // Only proceed if strict compliance time has elapsed
                        if (state.firstAdStartTime) {
                            const elapsed = Date.now() - state.firstAdStartTime;
                            
                            if (elapsed < config.firstAdDuration * 1000) {
                                console.log(`View Results button activation prevented - only ${elapsed}ms elapsed, need ${config.firstAdDuration * 1000}ms`);
                                return false;
                            }
                        }
                        
                        // If we get here, timing requirements are met
                        return originalEnableFunc.apply(this, arguments);
                    };
                }
            }
            
            // Listen for ad state changes
            window.addEventListener('message', function(event) {
                // Skip if not from this window
                if (event.source !== window) return;
                
                // Process event data
                if (event.data && event.data.type === 'adStateChange') {
                    processAdStateChange(event.data);
                }
            });
            
            // Detect first ad shown
            setupFirstAdDetection();
            
            // Detect second ad shown
            setupSecondAdDetection();
            
            // Setup button monitors
            setupButtonMonitoring();
        });
    }
    
    // Setup first ad detection
    function setupFirstAdDetection() {
        // Use MutationObserver to detect when first ad appears
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'style' && 
                    mutation.target.id === 'ad-overlay-loading') {
                    
                    // Check if first ad is now showing
                    if (mutation.target.style.display === 'flex' || 
                        mutation.target.style.display === 'block') {
                        
                        // Don't record again if already started
                        if (!state.firstAdStartTime) {
                            state.firstAdStartTime = Date.now();
                            console.log(`First ad showing at ${new Date(state.firstAdStartTime).toISOString()}`);
                            
                            // Set up a timer for exactly 5 seconds
                            setTimeout(function() {
                                completeFirstAd();
                            }, config.firstAdDuration * 1000);
                            
                            // Signal to other components
                            window.postMessage({ 
                                type: 'adStateChange', 
                                adType: 'first', 
                                state: 'start', 
                                timestamp: state.firstAdStartTime 
                            }, '*');
                        }
                    }
                }
            });
        });
        
        // Observe the ad overlay
        const firstAdOverlay = document.getElementById('ad-overlay-loading');
        if (firstAdOverlay) {
            observer.observe(firstAdOverlay, { attributes: true });
            
            // Check if already showing
            if (firstAdOverlay.style.display === 'flex' || firstAdOverlay.style.display === 'block') {
                state.firstAdStartTime = Date.now();
                console.log(`First ad was already showing`);
                
                // Set up a timer for exactly 5 seconds
                setTimeout(function() {
                    completeFirstAd();
                }, config.firstAdDuration * 1000);
            }
        }
    }
    
    // Setup second ad detection
    function setupSecondAdDetection() {
        // Use MutationObserver to detect when second ad appears
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'style' && 
                    mutation.target.id === 'ad-overlay-results') {
                    
                    // Check if second ad is now showing
                    if (mutation.target.style.display === 'flex' || 
                        mutation.target.style.display === 'block') {
                        
                        // Don't record again if already started
                        if (!state.secondAdStartTime) {
                            state.secondAdStartTime = Date.now();
                            console.log(`Second ad showing at ${new Date(state.secondAdStartTime).toISOString()}`);
                            
                            // Signal to other components
                            window.postMessage({ 
                                type: 'adStateChange', 
                                adType: 'second', 
                                state: 'start', 
                                timestamp: state.secondAdStartTime 
                            }, '*');
                        }
                    }
                }
            });
        });
        
        // Observe the ad overlay
        const secondAdOverlay = document.getElementById('ad-overlay-results');
        if (secondAdOverlay) {
            observer.observe(secondAdOverlay, { attributes: true });
            
            // Check if already showing
            if (secondAdOverlay.style.display === 'flex' || secondAdOverlay.style.display === 'block') {
                state.secondAdStartTime = Date.now();
                console.log(`Second ad was already showing`);
            }
        }
    }
    
    // Setup button state monitoring
    function setupButtonMonitoring() {
        // Use MutationObserver to monitor the View Results button
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && 
                    (mutation.attributeName === 'disabled' || 
                     mutation.attributeName === 'class')) {
                    
                    // Check if button is now enabled (not disabled)
                    if (mutation.target.disabled === false) {
                        // If first ad is complete but second one hasn't started
                        if (state.firstAdComplete && !state.secondAdStartTime) {
                            state.viewResultsEnabled = true;
                            console.log('View Results button enabled after first ad');
                        }
                        // If the entire sequence is complete
                        else if (state.secondAdComplete) {
                            state.adSequenceComplete = true;
                            console.log('Ad sequence complete, all buttons enabled');
                        }
                    }
                }
            });
        });
        
        // Listen for the button
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            observer.observe(viewResultsBtn, { attributes: true });
        }
    }
    
    // Process ad state change events
    function processAdStateChange(data) {
        // Skip if this is our own message
        if (data.source === 'ad-countdown-fix') return;
        
        console.log('Ad state change:', data);
        
        if (data.adType === 'first') {
            if (data.state === 'start') {
                // Another component detected first ad start
                state.firstAdStartTime = data.timestamp || Date.now();
            }
            else if (data.state === 'complete') {
                // Another component marked first ad complete
                state.firstAdComplete = true;
            }
        }
        else if (data.adType === 'second') {
            if (data.state === 'start') {
                // Another component detected second ad start
                state.secondAdStartTime = data.timestamp || Date.now();
            }
            else if (data.state === 'complete') {
                // Another component marked second ad complete
                state.secondAdComplete = true;
            }
        }
    }
    
    // Mark first ad as complete after exactly 5 seconds
    function completeFirstAd() {
        // Skip if already marked complete
        if (state.firstAdComplete) return;
        
        // Mark ad as complete
        state.firstAdComplete = true;
        
        // Update global state if available
        if (window.SnapLottoAds) {
            window.SnapLottoAds.firstAdComplete = true;
        }
        
        // Enable View Results button if it exists
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            viewResultsBtn.disabled = false;
            viewResultsBtn.classList.remove('btn-secondary');
            viewResultsBtn.classList.add('btn-success');
            viewResultsBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
            
            // Log this once, not repeatedly
            console.log('AdManager: First ad complete, enabling view results button');
        }
        
        // Signal to other components
        window.postMessage({ 
            type: 'adStateChange', 
            adType: 'first', 
            state: 'complete', 
            timestamp: Date.now(),
            source: 'ad-countdown-fix'
        }, '*');
    }
})();