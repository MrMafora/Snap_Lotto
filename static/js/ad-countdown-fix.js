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
            
            // AUTOMATICALLY TRIGGER THE TRANSITION without requiring user click
            console.log('💥 AUTO-TRIGGERING transition to second ad');
            
            // Hide the first ad overlay immediately
            const firstAdOverlay = document.getElementById('ad-overlay-loading');
            if (firstAdOverlay) {
                firstAdOverlay.style.display = 'none';
                console.log('First ad overlay hidden programmatically');
            }
            
            // Make sure results container is visible
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.classList.remove('d-none');
                console.log('Results container made visible');
            }
            
            // Show the second ad immediately
            const secondAdOverlay = document.getElementById('ad-overlay-results');
            if (secondAdOverlay) {
                secondAdOverlay.style.display = 'flex';
                console.log('Second ad overlay shown programmatically');
            }
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
    // Mark second ad as complete after exactly 15 seconds
    function completeSecondAd() {
        // Skip if already marked complete
        if (state.secondAdComplete) return;
        
        // Mark ad as complete
        state.secondAdComplete = true;
        
        // Update global state if available
        if (window.SnapLottoAds) {
            window.SnapLottoAds.secondAdComplete = true;
        }
        
        // Now reveal and enable the View Results button container
        const btnContainer = document.getElementById('view-results-btn-container');
        if (btnContainer) {
            console.log('📢 Now showing the View Results button container');
            btnContainer.style.display = 'block';
        }
        
        // Enable the View Results button
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            viewResultsBtn.disabled = false;
            viewResultsBtn.classList.remove('btn-secondary');
            viewResultsBtn.classList.add('btn-success', 'btn-pulse');
            viewResultsBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
            
            // Log this once, not repeatedly
            console.log('🏁 Second ad complete, enabling View Results button');
        }
        
        // Signal to other components
        window.postMessage({ 
            type: 'adStateChange', 
            adType: 'second', 
            state: 'complete', 
            timestamp: Date.now(),
            source: 'ad-countdown-fix'
        }, '*');
    }
    
    // Listen for the second ad to appear and start a timer
    document.addEventListener('DOMContentLoaded', function() {
        window.addEventListener('load', function() {
            // Add a custom event listener for when the second ad is displayed
            window.addEventListener('message', function(event) {
                if (event.data && 
                    event.data.type === 'adStateChange' && 
                    event.data.adType === 'second' && 
                    event.data.state === 'start') {
                    
                    console.log('Second ad appeared, starting 15-second countdown');
                    
                    // Set up a timer for exactly 15 seconds
                    setTimeout(function() {
                        completeSecondAd();
                    }, config.secondAdDuration * 1000);
                }
            });
            
            // Also detect if second ad is already visible when page loads
            const secondAdOverlay = document.getElementById('ad-overlay-results');
            if (secondAdOverlay && 
                (secondAdOverlay.style.display === 'flex' || secondAdOverlay.style.display === 'block')) {
                
                // Don't start another timer if we already have second ad start time
                if (!state.secondAdStartTime) {
                    state.secondAdStartTime = Date.now();
                    console.log('Second ad was already showing on page load, starting 15-second countdown');
                    
                    // Set up a timer for exactly 15 seconds
                    setTimeout(function() {
                        completeSecondAd();
                    }, config.secondAdDuration * 1000);
                }
            }
        });
    });
})();