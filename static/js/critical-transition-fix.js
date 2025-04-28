/**
 * Critical Ad Transition Fix
 * 
 * This script fixes issues with transitions between the first and second
 * advertisement displays, ensuring both ads show for exactly 15 seconds each
 * and that the process advances correctly.
 * 
 * Key fixes:
 * 1. Ensures smooth transition between first and second ad
 * 2. Prevents "View Results" button from activating prematurely
 * 3. Forces strict 15 second display time for both ads
 * 4. Adds safety checks to prevent skipping ads
 */

(function() {
    'use strict';
    
    console.log('Critical ad transition fix initializing');
    
    // Configuration for ad transitions
    const config = {
        firstAdMinTime: 15000,  // 15 seconds in milliseconds
        secondAdMinTime: 15000, // 15 seconds in milliseconds
        transitionDelay: 250,   // Short delay to ensure smooth transition (ms)
        checkInterval: 1000,    // How often to check for transition issues (ms)
        buttonDisabledClass: 'btn-secondary',
        buttonEnabledClass: 'btn-success'
    };
    
    // State tracking
    let state = {
        firstAdStarted: false,
        firstAdStartTime: null,
        firstAdCompleted: false,
        secondAdStarted: false,
        secondAdStartTime: null,
        secondAdCompleted: false,
        transitionInProgress: false,
        intervalId: null
    };
    
    // DOM element references
    let elements = {
        firstAdOverlay: null,
        secondAdOverlay: null,
        viewResultsButton: null,
        countdownElement: null
    };
    
    // Initialize the transition fix
    function initialize() {
        // Cache DOM elements
        elements.firstAdOverlay = document.getElementById('ad-overlay-loading');
        elements.secondAdOverlay = document.getElementById('ad-overlay-results');
        elements.viewResultsButton = document.getElementById('view-results-btn');
        elements.countdownElement = document.getElementById('countdown');
        
        // Set up monitoring interval
        state.intervalId = setInterval(monitorAdTransitions, config.checkInterval);
        
        // Attach to the existing ad system
        attachToExistingAdSystem();
        
        console.log('Critical ad transition fix initialized');
    }
    
    // Monitor ad transitions to catch and fix any issues
    function monitorAdTransitions() {
        // Check if first ad is active
        if (isFirstAdActive() && !state.firstAdStarted) {
            // First ad just started
            state.firstAdStarted = true;
            state.firstAdStartTime = Date.now();
            state.firstAdCompleted = false;
            
            console.log('Transition fix: First ad detected as started');
            
            // Ensure view results button is disabled
            disableViewResultsButton();
            
            // Schedule enabling the button after minimum time
            scheduleFirstAdCompletion();
        }
        
        // Check if second ad is active
        if (isSecondAdActive() && !state.secondAdStarted) {
            // Second ad just started
            state.secondAdStarted = true;
            state.secondAdStartTime = Date.now();
            state.secondAdCompleted = false;
            state.firstAdCompleted = true;  // First ad must be complete if second is showing
            
            console.log('Transition fix: Second ad detected as started');
            
            // Ensure view results button is disabled for second ad
            disableViewResultsButton('Continue to Results (Wait 15s)');
            
            // Schedule enabling the button after minimum time
            scheduleSecondAdCompletion();
        }
        
        // Check for improper button state
        checkAndFixButtonState();
    }
    
    // Attach our logic to the existing ad system
    function attachToExistingAdSystem() {
        // If the ad system is already initialized, hook into its events
        if (window.SnapLottoAds) {
            console.log('Transition fix: Attaching to existing ad system');
            
            // Store original functions to extend them
            const originalShowLoadingAd = window.SnapLottoAds.showLoadingAdOverlay;
            const originalShowResultsAd = window.SnapLottoAds.showResultsAdOverlay;
            const originalEnableViewResults = window.SnapLottoAds.enableViewResultsButton;
            const originalEnableContinueResults = window.SnapLottoAds.enableContinueToResultsButton;
            
            // Extend the first ad display function
            if (typeof originalShowLoadingAd === 'function') {
                window.SnapLottoAds.showLoadingAdOverlay = function() {
                    // Reset our state
                    resetState();
                    
                    // Mark first ad as started
                    state.firstAdStarted = true;
                    state.firstAdStartTime = Date.now();
                    
                    // Call original function
                    originalShowLoadingAd.apply(this, arguments);
                    
                    // Double-check button is disabled
                    disableViewResultsButton();
                    
                    // Schedule enabling the button after minimum time
                    scheduleFirstAdCompletion();
                };
            }
            
            // Extend the second ad display function
            if (typeof originalShowResultsAd === 'function') {
                window.SnapLottoAds.showResultsAdOverlay = function() {
                    // Mark second ad as started
                    state.secondAdStarted = true;
                    state.secondAdStartTime = Date.now();
                    state.firstAdCompleted = true;
                    
                    // Call original function
                    originalShowResultsAd.apply(this, arguments);
                    
                    // Double-check button is disabled 
                    disableViewResultsButton('Continue to Results (Wait 15s)');
                    
                    // Schedule enabling the button after minimum time
                    scheduleSecondAdCompletion();
                };
            }
            
            // Extend the enable view results button function
            if (typeof originalEnableViewResults === 'function') {
                window.SnapLottoAds.enableViewResultsButton = function() {
                    // Only enable if minimum time has truly passed
                    const elapsedTime = Date.now() - state.firstAdStartTime;
                    
                    if (elapsedTime >= config.firstAdMinTime) {
                        // OK to enable button
                        state.firstAdCompleted = true;
                        originalEnableViewResults.apply(this, arguments);
                    } else {
                        // Too early! Schedule for later
                        console.log('Transition fix: Prevented premature button activation, rescheduling');
                        setTimeout(function() {
                            originalEnableViewResults.apply(window.SnapLottoAds);
                        }, config.firstAdMinTime - elapsedTime + 50);
                    }
                };
            }
            
            // Extend the enable continue to results button function
            if (typeof originalEnableContinueResults === 'function') {
                window.SnapLottoAds.enableContinueToResultsButton = function() {
                    // Only enable if minimum time has truly passed
                    const elapsedTime = Date.now() - state.secondAdStartTime;
                    
                    if (elapsedTime >= config.secondAdMinTime) {
                        // OK to enable button
                        state.secondAdCompleted = true;
                        originalEnableContinueResults.apply(this, arguments);
                    } else {
                        // Too early! Schedule for later
                        console.log('Transition fix: Prevented premature button activation, rescheduling');
                        setTimeout(function() {
                            originalEnableContinueResults.apply(window.SnapLottoAds);
                        }, config.secondAdMinTime - elapsedTime + 50);
                    }
                };
            }
        }
    }
    
    // Check if first ad is active
    function isFirstAdActive() {
        return elements.firstAdOverlay && 
               elements.firstAdOverlay.style.display !== 'none';
    }
    
    // Check if second ad is active
    function isSecondAdActive() {
        return elements.secondAdOverlay && 
               elements.secondAdOverlay.style.display !== 'none';
    }
    
    // Ensure view results button is disabled
    function disableViewResultsButton(buttonText) {
        if (elements.viewResultsButton) {
            // Disable the button
            elements.viewResultsButton.disabled = true;
            
            // Update styling
            elements.viewResultsButton.classList.remove('btn-pulse');
            elements.viewResultsButton.classList.remove(config.buttonEnabledClass);
            elements.viewResultsButton.classList.add(config.buttonDisabledClass);
            
            // Update text if provided
            if (buttonText) {
                elements.viewResultsButton.innerHTML = '<i class="fas fa-lock me-2"></i> ' + buttonText;
            }
        }
    }
    
    // Check and fix button state if needed
    function checkAndFixButtonState() {
        // If first ad active but hasn't shown long enough, ensure button disabled
        if (isFirstAdActive() && state.firstAdStarted) {
            const elapsedTime = Date.now() - state.firstAdStartTime;
            
            if (elapsedTime < config.firstAdMinTime && elements.viewResultsButton && !elements.viewResultsButton.disabled) {
                console.log('Transition fix: Fixing button state for first ad');
                disableViewResultsButton();
                
                // Update countdown element if possible
                if (elements.countdownElement) {
                    const remainingSeconds = Math.ceil((config.firstAdMinTime - elapsedTime) / 1000);
                    elements.countdownElement.textContent = remainingSeconds;
                }
            }
        }
        
        // If second ad active but hasn't shown long enough, ensure button disabled
        if (isSecondAdActive() && state.secondAdStarted) {
            const elapsedTime = Date.now() - state.secondAdStartTime;
            
            if (elapsedTime < config.secondAdMinTime && elements.viewResultsButton && !elements.viewResultsButton.disabled) {
                console.log('Transition fix: Fixing button state for second ad');
                disableViewResultsButton('Continue to Results (Wait 15s)');
                
                // Update countdown element if possible
                if (elements.countdownElement) {
                    const remainingSeconds = Math.ceil((config.secondAdMinTime - elapsedTime) / 1000);
                    elements.countdownElement.textContent = remainingSeconds;
                }
            }
        }
    }
    
    // Schedule first ad completion
    function scheduleFirstAdCompletion() {
        setTimeout(function() {
            const elapsedTime = Date.now() - state.firstAdStartTime;
            
            if (isFirstAdActive() && elapsedTime >= config.firstAdMinTime && !state.firstAdCompleted) {
                console.log('Transition fix: First ad completed by scheduler');
                state.firstAdCompleted = true;
                
                // Enable button through ad system if available
                if (window.SnapLottoAds && typeof window.SnapLottoAds.enableViewResultsButton === 'function') {
                    window.SnapLottoAds.enableViewResultsButton();
                }
            }
        }, config.firstAdMinTime + config.transitionDelay);
    }
    
    // Schedule second ad completion
    function scheduleSecondAdCompletion() {
        setTimeout(function() {
            const elapsedTime = Date.now() - state.secondAdStartTime;
            
            if (isSecondAdActive() && elapsedTime >= config.secondAdMinTime && !state.secondAdCompleted) {
                console.log('Transition fix: Second ad completed by scheduler');
                state.secondAdCompleted = true;
                
                // Enable button through ad system if available
                if (window.SnapLottoAds && typeof window.SnapLottoAds.enableContinueToResultsButton === 'function') {
                    window.SnapLottoAds.enableContinueToResultsButton();
                }
            }
        }, config.secondAdMinTime + config.transitionDelay);
    }
    
    // Reset state completely
    function resetState() {
        state = {
            firstAdStarted: false,
            firstAdStartTime: null,
            firstAdCompleted: false,
            secondAdStarted: false,
            secondAdStartTime: null,
            secondAdCompleted: false,
            transitionInProgress: false,
            intervalId: state.intervalId
        };
    }
    
    // Emergency force transition to second ad (for console debug)
    function emergencyForceCompleteFirstAd() {
        if (isFirstAdActive()) {
            console.log('Transition fix: Emergency first ad completion forced');
            state.firstAdCompleted = true;
            
            // Enable button through ad system if available
            if (window.SnapLottoAds && typeof window.SnapLottoAds.enableViewResultsButton === 'function') {
                window.SnapLottoAds.enableViewResultsButton();
            } else if (elements.viewResultsButton) {
                // Direct button enable
                elements.viewResultsButton.disabled = false;
                elements.viewResultsButton.classList.add('btn-pulse');
                elements.viewResultsButton.classList.remove(config.buttonDisabledClass);
                elements.viewResultsButton.classList.add(config.buttonEnabledClass);
                elements.viewResultsButton.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
            }
        }
    }
    
    // Emergency force transition to results (for console debug)
    function emergencyForceCompleteSecondAd() {
        if (isSecondAdActive()) {
            console.log('Transition fix: Emergency second ad completion forced');
            state.secondAdCompleted = true;
            
            // Enable button through ad system if available
            if (window.SnapLottoAds && typeof window.SnapLottoAds.enableContinueToResultsButton === 'function') {
                window.SnapLottoAds.enableContinueToResultsButton();
            } else if (elements.viewResultsButton) {
                // Direct button enable
                elements.viewResultsButton.disabled = false;
                elements.viewResultsButton.classList.add('btn-pulse');
                elements.viewResultsButton.classList.remove(config.buttonDisabledClass);
                elements.viewResultsButton.classList.add(config.buttonEnabledClass);
                elements.viewResultsButton.innerHTML = '<i class="fas fa-check-circle me-2"></i> Continue to Results!';
            }
        }
    }
    
    // Initialize on page load - delay slightly to let ad system initialize first
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(initialize, 100);
        
        // Add emergency functions to window for debugging
        window.emergencyForceCompleteFirstAd = emergencyForceCompleteFirstAd;
        window.emergencyForceCompleteSecondAd = emergencyForceCompleteSecondAd;
    });
    
    // Also initialize immediately in case DOMContentLoaded already fired
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(initialize, 100);
    }
    
})();