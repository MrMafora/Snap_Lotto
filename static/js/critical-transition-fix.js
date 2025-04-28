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
        maxChecks: 60             // Maximum number of state checks (30 seconds)
    };
    
    // State tracking
    let state = {
        countdownRunning: false,
        activeCountdown: null,
        adPhase: 'none',           // 'none', 'first', or 'second'
        checkCount: 0,
        transitionInProgress: false
    };
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', initializeTransitionFix);
    
    // If document already loaded, initialize immediately
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(initializeTransitionFix, 100);
    }
    
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
            viewResultsBtn.addEventListener('click', function() {
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
        // Clear any existing countdown
        if (state.activeCountdown) {
            clearInterval(state.activeCountdown);
            state.activeCountdown = null;
        }
        
        // Find the countdown element
        const countdownSpan = document.getElementById('countdown');
        const viewResultsBtn = document.getElementById('view-results-btn');
        
        if (!countdownSpan || !viewResultsBtn) {
            console.error('Transition fix: Could not find countdown or button elements');
            return;
        }
        
        // Reset the countdown display
        countdownSpan.textContent = config.adDisplayTime.toString();
        
        // Disable the button
        viewResultsBtn.disabled = true;
        
        // Update button text based on phase
        if (phase === 'first') {
            viewResultsBtn.innerHTML = '<i class="fas fa-lock me-2"></i> View Results (Wait 15s)';
            viewResultsBtn.classList.remove('btn-success');
            viewResultsBtn.classList.add('btn-secondary');
        } else {
            viewResultsBtn.innerHTML = '<i class="fas fa-lock me-2"></i> Continue to Results (Wait 15s)';
            viewResultsBtn.classList.remove('btn-success');
            viewResultsBtn.classList.add('btn-secondary');
        }
        
        // Set the start time to ensure consistent countdown
        const startTime = Date.now();
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
            
            // Check if button text should change
            if (phase === 'first') {
                viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${secondsRemaining}s)`;
                console.log('Found countdown button: ' + viewResultsBtn.innerHTML);
            } else {
                viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> Continue to Results (Wait ${secondsRemaining}s)`;
            }
            
            // Check if countdown is complete
            if (secondsRemaining <= 0) {
                // Clean up
                clearInterval(state.activeCountdown);
                state.activeCountdown = null;
                state.countdownRunning = false;
                
                // Enable the button
                viewResultsBtn.disabled = false;
                viewResultsBtn.classList.remove('btn-secondary');
                viewResultsBtn.classList.add('btn-success');
                viewResultsBtn.classList.add('btn-pulse');
                
                // Update button text
                if (phase === 'first') {
                    viewResultsBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                } else {
                    viewResultsBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> Continue to Results!';
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