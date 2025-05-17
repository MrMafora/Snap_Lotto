/**
 * Critical Transition Fix for Advertisement System
 * 
 * This script ensures smooth transitions between advertisement states
 * and consolidates the various countdown timers to prevent conflicts.
 * 
 * It works alongside ads-mobile.js and scan-process-watchdog.js
 * to provide triple redundancy for ensuring proper ad display flow.
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        adDisplayTime: 15,         // Seconds to display each ad
        countdownInterval: 1000,   // Update countdown every 1 second
        checkInterval: 500,        // Check ad state every 500ms
        maxChecks: 60,            // Maximum number of state checks (30 seconds)
        adMinimumDisplayTime: 15000 // Minimum time in ms before ad can be closed
    };
    
    // State tracking
    let state = {
        countdownRunning: false,
        activeCountdown: null,
        adPhase: 'none',           // 'none', 'first', or 'second'
        checkCount: 0,
        transitionInProgress: false,
        countdownStartTime: 0      // When the countdown started (timestamp)
    };
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', initializeTransitionFix);
    
    // If document already loaded, initialize immediately
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(initializeTransitionFix, 100);
    }
    
    // Listen for direct countdown trigger events from other scripts
    document.addEventListener('trigger-countdown', function(e) {
        console.log('Received trigger-countdown event:', e.detail);
        
        // Extract button ID and phase from event detail
        const buttonId = e.detail.buttonId || 'view-results-btn';
        const phase = e.detail.phase || 'second';
        const forceReset = e.detail.force === true;
        
        // Always update the ad phase state
        state.adPhase = phase;
        
        // Reset any ongoing countdown to avoid conflicts
        if (state.activeCountdown) {
            clearInterval(state.activeCountdown);
            state.activeCountdown = null;
            state.countdownRunning = false;
        }
        
        // Set up countdown based on the requested phase
        console.log('Setting up countdown for phase:', phase, forceReset ? '(forced)' : '');
        setupCountdown(phase);
    });
    
    // Listen for reset countdown events to force a clean state
    document.addEventListener('reset-countdown', function() {
        console.log('Received reset-countdown event, clearing all countdown state');
        
        // Reset all countdown state
        if (state.activeCountdown) {
            clearInterval(state.activeCountdown);
            state.activeCountdown = null;
        }
        
        state.countdownRunning = false;
        state.countdownStartTime = 0;
    });
    
    // Initialize the transition fix
    function initializeTransitionFix() {
        // Set up state monitoring interval
        setInterval(monitorAdState, config.checkInterval);
        
        // Find and listen to the scan button to detect start of process
        setupScanButtonListener();
        
        // Find and connect the view results button
        connectViewResultsButtons();
        
        console.log('Critical transition fix initialized');
    }
    
    // Set up listener for scan button click
    function setupScanButtonListener() {
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', function() {
                // Reset state for new scan
                state.adPhase = 'none';
                state.checkCount = 0;
                
                // Schedule the first check
                setTimeout(checkFirstAdState, 1000);
            });
        }
    }
    
    // Connect to view results buttons
    function connectViewResultsButtons() {
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            viewResultsBtn.addEventListener('click', function(e) {
                const now = Date.now();
                const elapsed = now - state.countdownStartTime;
                
                // Check if minimum display time has elapsed before allowing button click
                if (elapsed < config.adMinimumDisplayTime && state.countdownRunning) {
                    console.log(`Button clicked too early (${elapsed}ms). Minimum required: ${config.adMinimumDisplayTime}ms`);
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
                
                // Check if the minimum time has elapsed
                const timeElapsed = now - state.countdownStartTime;
                if (timeElapsed < config.adMinimumDisplayTime) {
                    console.log(`Button clicked too early (${timeElapsed}ms). Need ${config.adMinimumDisplayTime}ms minimum.`);
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }

                // Only proceed if the countdown has completed
                if (state.countdownRunning) {
                    console.log('Countdown still running, button should be disabled');
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
                
                // Identify which phase we're in based on which overlay is visible
                if (isFirstAdVisible()) {
                    // Transition from first ad to second ad 
                    state.adPhase = 'second';
                    state.checkCount = 0;
                    
                    // Schedule the second ad check
                    setTimeout(checkSecondAdState, 1000);
                } else if (isSecondAdVisible()) {
                    // Completed the entire ad viewing process
                    state.adPhase = 'none';
                }
            });
        }
    }
    
    // Check if first ad has appeared and set up countdown
    function checkFirstAdState() {
        // Skip if we're past this phase
        if (state.adPhase !== 'none') return;
        
        if (isFirstAdVisible()) {
            // First ad is now showing
            state.adPhase = 'first';
            
            // Set up the countdown for first ad
            setupCountdown('first');
            
            // Log detection
            console.log('Transition fix: First ad detected');
        } else {
            // Increment check count
            state.checkCount++;
            
            // If we haven't exceeded max checks, schedule another check
            if (state.checkCount < config.maxChecks) {
                setTimeout(checkFirstAdState, config.checkInterval);
            }
        }
    }
    
    // Check if second ad has appeared and set up countdown
    function checkSecondAdState() {
        // Skip if we're not in the right phase
        if (state.adPhase !== 'second') return;
        
        if (isSecondAdVisible()) {
            // Second ad is now showing
            
            // Set up the countdown for second ad
            setupCountdown('second');
            
            // Log detection
            console.log('Transition fix: Second ad detected');
        } else {
            // Increment check count
            state.checkCount++;
            
            // If we haven't exceeded max checks, schedule another check
            if (state.checkCount < config.maxChecks) {
                setTimeout(checkSecondAdState, config.checkInterval);
            }
        }
    }
    
    // Monitor the ad state to detect inconsistencies
    function monitorAdState() {
        // Skip if no specific ad phase
        if (state.adPhase === 'none') return;
        
        // Check for inconsistencies
        if (state.adPhase === 'first' && !isFirstAdVisible()) {
            // First ad no longer visible but we think it should be
            if (isSecondAdVisible()) {
                // We've moved to second ad without updating state
                state.adPhase = 'second';
                console.log('Transition fix: Detected transition to second ad');
                
                // Set up second ad countdown
                setupCountdown('second');
            }
        } else if (state.adPhase === 'second' && !isSecondAdVisible()) {
            // Second ad no longer visible
            state.adPhase = 'none';
            console.log('Transition fix: Ad cycle complete');
        }
    }
    
    // Set up a consolidated countdown for the specified ad phase
    function setupCountdown(phase) {
        console.log(`Setting up ${phase} ad countdown`);
        
        // Prevent multiple countdowns by checking if we're already running one for this phase
        if (state.activeCountdown && state.countdownRunning && state.adPhase === phase) {
            console.log(`Countdown for ${phase} phase already running, not starting a new one`);
            return;
        }
        
        // Clear any existing countdown
        if (state.activeCountdown) {
            clearInterval(state.activeCountdown);
            state.activeCountdown = null;
        }
        
        // Clear running state
        state.countdownRunning = false;
        
        // Find the appropriate countdown elements based on phase
        let countdownSpan;
        
        if (phase === 'first') {
            countdownSpan = document.getElementById('first-countdown');
        } else {
            countdownSpan = document.getElementById('countdown');
        }
        
        const viewResultsBtn = document.getElementById('view-results-btn');
        
        if (!countdownSpan) {
            console.error('Transition fix: Could not find countdown element for phase ' + phase);
            return;
        }
        
        if (!viewResultsBtn && phase === 'second') {
            console.error('Transition fix: Could not find view results button');
            return;
        }
        
        // Reset the countdown display
        countdownSpan.textContent = config.adDisplayTime.toString();
        
        // Only update button if it exists and we're in the second phase
        if (viewResultsBtn && phase === 'second') {
            // Disable the button
            viewResultsBtn.disabled = true;
            
            // Update button text and appearance
            viewResultsBtn.innerHTML = '<i class="fas fa-lock me-2"></i> View Results (Wait 15s)';
            viewResultsBtn.classList.remove('btn-success', 'btn-pulse');
            viewResultsBtn.classList.add('btn-secondary');
            
            // Remove any previous event listeners by cloning
            const oldBtn = viewResultsBtn;
            const newBtn = oldBtn.cloneNode(true);
            oldBtn.parentNode.replaceChild(newBtn, oldBtn);
        }
        
        // Set the start time to ensure consistent countdown
        const startTime = Date.now();
        state.countdownStartTime = startTime;  // Save it in state for button check
        const duration = config.adDisplayTime * 1000;
        
        // Start the consolidated countdown
        let secondsRemaining = config.adDisplayTime;
        state.countdownRunning = true;
        
        state.activeCountdown = setInterval(function() {
            // Calculate remaining time based on elapsed time to avoid drift
            const elapsed = Date.now() - startTime;
            secondsRemaining = Math.max(0, Math.ceil((duration - elapsed) / 1000));
            
            // Update the display
            countdownSpan.textContent = secondsRemaining.toString();
            
            // Update button text only if button exists
            if (viewResultsBtn && phase === 'second') {
                viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${secondsRemaining}s)`;
            }
            
            // Check if countdown is complete
            if (secondsRemaining <= 0) {
                // Clean up
                clearInterval(state.activeCountdown);
                state.activeCountdown = null;
                state.countdownRunning = false;
                
                // Only update button if it exists (only in second phase)
                if (viewResultsBtn && phase === 'second') {
                    // Enable the button
                    viewResultsBtn.disabled = false;
                    viewResultsBtn.classList.remove('btn-secondary');
                    viewResultsBtn.classList.add('btn-success');
                    viewResultsBtn.classList.add('btn-pulse');
                    
                    // Update button text
                    viewResultsBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                    
                    // Add working click handler
                    const newBtn = viewResultsBtn.cloneNode(true);
                    if (viewResultsBtn.parentNode) {
                        viewResultsBtn.parentNode.replaceChild(newBtn, viewResultsBtn);
                        
                        // Add a new, reliable event listener
                        newBtn.addEventListener('click', function(e) {
                            console.log('View Results button clicked after countdown completion');
                            
                            // Hide the results overlay
                            const resultsOverlay = document.getElementById('ad-overlay-results');
                            if (resultsOverlay) {
                                resultsOverlay.style.display = 'none';
                            }
                            
                            // Show results container
                            const resultsContainer = document.getElementById('results-container');
                            if (resultsContainer) {
                                resultsContainer.style.display = 'block';
                                resultsContainer.classList.remove('d-none');
                            }
                            
                            // Set global flags for other scripts to detect
                            window.resultsShown = true;
                            window.inResultsMode = true;
                            window.hasCompletedAdFlow = true;
                            
                            // Prevent default and stop propagation
                            e.preventDefault();
                            e.stopPropagation();
                        }, true); // Using capture phase to ensure this runs first
                    }
                }
                
                console.log('Transition fix: Countdown complete for ' + phase + ' ad');
                
                // Update global state for other scripts to detect
                if (window.SnapLottoAds) {
                    if (phase === 'first') {
                        window.SnapLottoAds.firstAdComplete = true;
                    } else {
                        window.SnapLottoAds.secondAdComplete = true;
                    }
                }
                
                // Dispatch event to notify other scripts that countdown is complete
                document.dispatchEvent(new CustomEvent('countdown-complete', {
                    detail: { phase: phase, timeElapsed: Date.now() - startTime }
                }));
            }
        }, config.countdownInterval);
    }
    
    // Check if the first ad overlay is visible
    function isFirstAdVisible() {
        const overlay = document.getElementById('ad-overlay-loading');
        return overlay && (overlay.style.display === 'flex' || overlay.style.display === 'block');
    }
    
    // Check if the second ad overlay is visible
    function isSecondAdVisible() {
        const overlay = document.getElementById('ad-overlay-results');
        return overlay && (overlay.style.display === 'flex' || overlay.style.display === 'block');
    }
    
})();