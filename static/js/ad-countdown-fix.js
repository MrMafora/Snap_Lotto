/**
 * Ad Countdown System - Fixed Version
 * This is a completely rewritten, simplified approach to the ad countdown system.
 */
(function() {
    // Configuration
    const config = {
        displayTime: 15, // seconds
        interval: 1000, // update interval in ms
    };

    // Store countdown state
    let state = {
        firstAdTimer: null,
        secondAdTimer: null,
        firstAdComplete: false,
        secondAdComplete: false
    };

    // Set up event listeners once the page is ready
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(initCountdownSystem, 100);
    } else {
        document.addEventListener('DOMContentLoaded', initCountdownSystem);
    }

    function initCountdownSystem() {
        console.log("Ad countdown fix: Initializing simplified countdown system");

        // Listen for scan button to reset state
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', resetState);
        }

        // Set up visibility observers for ad overlays
        setupOverlayObservers();

        // Set up display callbacks for the Continue button
        setupViewResultsButtonFunctionality();

        console.log("Ad countdown fix: Initialization complete");
    }

    function resetState() {
        console.log("Ad countdown fix: Resetting state");
        
        // Clear any existing timers
        if (state.firstAdTimer) {
            clearInterval(state.firstAdTimer);
            state.firstAdTimer = null;
        }
        
        if (state.secondAdTimer) {
            clearInterval(state.secondAdTimer);
            state.secondAdTimer = null;
        }
        
        // Reset completion flags
        state.firstAdComplete = false;
        state.secondAdComplete = false;
    }

    function setupOverlayObservers() {
        // First ad overlay 
        const firstAdObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'style') {
                    const overlay = document.getElementById('ad-overlay-loading');
                    if (overlay && (overlay.style.display === 'flex' || overlay.style.display === 'block')) {
                        console.log("Ad countdown fix: First ad detected");
                        startFirstAdCountdown();
                    }
                }
            });
        });

        const firstOverlay = document.getElementById('ad-overlay-loading');
        if (firstOverlay) {
            firstAdObserver.observe(firstOverlay, { attributes: true });
        }

        // Second ad overlay
        const secondAdObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'style') {
                    const overlay = document.getElementById('ad-overlay-results');
                    if (overlay && (overlay.style.display === 'flex' || overlay.style.display === 'block')) {
                        console.log("Ad countdown fix: Second ad detected");
                        startSecondAdCountdown();
                    }
                }
            });
        });

        const secondOverlay = document.getElementById('ad-overlay-results');
        if (secondOverlay) {
            secondAdObserver.observe(secondOverlay, { attributes: true });
        }
    }

    function startFirstAdCountdown() {
        // Clear any existing first ad countdown
        if (state.firstAdTimer) {
            clearInterval(state.firstAdTimer);
        }

        // Reset completion flag
        state.firstAdComplete = false;

        const countdownSpan = document.getElementById('first-countdown');
        if (!countdownSpan) {
            console.error("Ad countdown fix: First countdown element not found");
            return;
        }

        // Set initial countdown value
        countdownSpan.textContent = config.displayTime.toString();

        // Start time for precise timing
        const startTime = Date.now();
        let secondsRemaining = config.displayTime;

        // Start the countdown
        state.firstAdTimer = setInterval(function() {
            // Calculate time elapsed and remaining
            const elapsed = Date.now() - startTime;
            secondsRemaining = Math.max(0, Math.ceil((config.displayTime * 1000 - elapsed) / 1000));

            // Update display
            countdownSpan.textContent = secondsRemaining.toString();

            // Check if countdown is complete
            if (secondsRemaining <= 0) {
                // Clean up
                clearInterval(state.firstAdTimer);
                state.firstAdTimer = null;
                state.firstAdComplete = true;

                // Inform other scripts
                document.dispatchEvent(new CustomEvent('first-ad-complete'));
                
                // Enable the first View Results button
                const viewResultsBtn = document.getElementById('view-results-btn');
                if (viewResultsBtn) {
                    enableViewResultsButton(viewResultsBtn);
                }
            }
        }, config.interval);
    }

    function startSecondAdCountdown() {
        // Clear any existing second ad countdown
        if (state.secondAdTimer) {
            clearInterval(state.secondAdTimer);
        }

        // Reset completion flag
        state.secondAdComplete = false;

        const countdownSpan = document.getElementById('countdown');
        if (!countdownSpan) {
            console.error("Ad countdown fix: Second countdown element not found");
            return;
        }

        const viewResultsBtn = document.getElementById('view-results-btn');
        if (!viewResultsBtn) {
            console.error("Ad countdown fix: View results button not found");
            return;
        }

        // Reset the button to disabled state
        disableViewResultsButton(viewResultsBtn);

        // Set initial countdown value
        countdownSpan.textContent = config.displayTime.toString();

        // Start time for precise timing
        const startTime = Date.now();
        let secondsRemaining = config.displayTime;

        // Start the countdown
        state.secondAdTimer = setInterval(function() {
            // Calculate time elapsed and remaining
            const elapsed = Date.now() - startTime;
            secondsRemaining = Math.max(0, Math.ceil((config.displayTime * 1000 - elapsed) / 1000));

            // Update display
            countdownSpan.textContent = secondsRemaining.toString();
            
            // Update button text
            viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${secondsRemaining}s)`;

            // Check if countdown is complete
            if (secondsRemaining <= 0) {
                // Clean up
                clearInterval(state.secondAdTimer);
                state.secondAdTimer = null;
                state.secondAdComplete = true;

                // Inform other scripts
                document.dispatchEvent(new CustomEvent('second-ad-complete'));
                
                // Enable the View Results button
                enableViewResultsButton(viewResultsBtn);
            }
        }, config.interval);
    }

    function enableViewResultsButton(button) {
        // Replace the button with a fresh copy to remove stale event handlers
        const newButton = button.cloneNode(true);
        
        // Style the button as enabled
        newButton.disabled = false;
        newButton.classList.remove('btn-secondary');
        newButton.classList.add('btn-success', 'btn-pulse');
        newButton.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
        
        // Add click handler
        newButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log("Ad countdown fix: View Results button clicked");
            
            // Handle ad transition based on which overlay is visible
            const firstAdOverlay = document.getElementById('ad-overlay-loading');
            const secondAdOverlay = document.getElementById('ad-overlay-results');
            
            if (firstAdOverlay && 
                (firstAdOverlay.style.display === 'flex' || firstAdOverlay.style.display === 'block')) {
                // Hide first ad
                firstAdOverlay.style.display = 'none';
                
                // Make sure results container is visible
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.classList.remove('d-none');
                }
                
                // Show second ad
                if (secondAdOverlay) {
                    secondAdOverlay.style.display = 'flex';
                }
                
            } else if (secondAdOverlay && 
                      (secondAdOverlay.style.display === 'flex' || secondAdOverlay.style.display === 'block')) {
                // Hide second ad
                secondAdOverlay.style.display = 'none';
                
                // Make sure results container is visible
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.classList.remove('d-none');
                    resultsContainer.style.display = 'block';
                }
                
                // Set global state for other scripts
                window.resultsShown = true;
                window.inResultsMode = true;
                window.hasCompletedAdFlow = true;
            }
        });
        
        // Replace the button
        button.parentNode.replaceChild(newButton, button);
    }

    function disableViewResultsButton(button) {
        // Replace the button with a fresh copy to remove stale event handlers
        const newButton = button.cloneNode(true);
        
        // Style the button as disabled
        newButton.disabled = true;
        newButton.classList.remove('btn-success', 'btn-pulse');
        newButton.classList.add('btn-secondary');
        newButton.innerHTML = '<i class="fas fa-lock me-2"></i> View Results (Wait 15s)';
        
        // Replace the button
        button.parentNode.replaceChild(newButton, button);
    }

    function setupViewResultsButtonFunctionality() {
        // Get the View Results button
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (!viewResultsBtn) return;
        
        // Add MutationObserver to monitor when button is added to DOM
        const buttonObserver = new MutationObserver(function(mutations) {
            const viewResultsBtn = document.getElementById('view-results-btn');
            if (viewResultsBtn && !viewResultsBtn._observed) {
                viewResultsBtn._observed = true;
                
                // Replace with a fresh button to ensure no stale handlers
                const newButton = viewResultsBtn.cloneNode(true);
                viewResultsBtn.parentNode.replaceChild(newButton, viewResultsBtn);
                
                // Add the appropriate state
                if (document.getElementById('ad-overlay-loading').style.display === 'flex' &&
                    !state.firstAdComplete) {
                    disableViewResultsButton(newButton);
                } else if (document.getElementById('ad-overlay-results').style.display === 'flex' &&
                    !state.secondAdComplete) {
                    disableViewResultsButton(newButton);
                } else {
                    enableViewResultsButton(newButton);
                }
            }
        });
        
        // Observe the entire document for button changes
        buttonObserver.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
    }
})();