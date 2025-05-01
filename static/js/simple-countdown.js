/**
 * Ultra Simple Ad Countdown System
 * This is a stripped-down version that only does the essential countdown logic
 */
(function() {
    // Configuration
    const firstAdCountdownTime = 5; // seconds (FIXED to exactly 5 seconds)
    const secondAdCountdownTime = 15; // seconds
    const updateInterval = 1000; // ms

    // DOM elements we'll need
    let firstAdCountdown = null;
    let secondAdCountdown = null;
    let viewResultsBtn = null;

    // State tracking
    let firstAdTimer = null;
    let secondAdTimer = null;
    let firstAdComplete = false;
    let secondAdComplete = false;

    // Initialize when document is ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Simple countdown system initializing');
        
        // Find the countdown elements
        firstAdCountdown = document.getElementById('first-countdown');
        secondAdCountdown = document.getElementById('countdown');
        viewResultsBtn = document.getElementById('view-results-btn');
        
        // Set up listeners
        setupListeners();
    });

    function setupListeners() {
        // Listen for when ad overlays become visible
        const firstAdObserver = new MutationObserver(function(mutations) {
            for (let mutation of mutations) {
                if (mutation.attributeName === 'style') {
                    if (mutation.target.style.display === 'flex' || mutation.target.style.display === 'block') {
                        console.log('First ad detected - starting countdown');
                        startFirstAdCountdown();
                    }
                }
            }
        });

        const secondAdObserver = new MutationObserver(function(mutations) {
            for (let mutation of mutations) {
                if (mutation.attributeName === 'style') {
                    if (mutation.target.style.display === 'flex' || mutation.target.style.display === 'block') {
                        console.log('Second ad detected - starting countdown');
                        startSecondAdCountdown();
                    }
                }
            }
        });

        // Watch the ad overlays
        const firstAdOverlay = document.getElementById('ad-overlay-loading');
        const secondAdOverlay = document.getElementById('ad-overlay-results');
        
        if (firstAdOverlay) {
            firstAdObserver.observe(firstAdOverlay, { attributes: true });
        }
        
        if (secondAdOverlay) {
            secondAdObserver.observe(secondAdOverlay, { attributes: true });
        }

        // Reset on new scan
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', function() {
                resetCountdowns();
            });
        }
    }

    function resetCountdowns() {
        // Clear any active timers
        if (firstAdTimer) {
            clearInterval(firstAdTimer);
            firstAdTimer = null;
        }
        
        if (secondAdTimer) {
            clearInterval(secondAdTimer);
            secondAdTimer = null;
        }
        
        // Reset completion flags
        firstAdComplete = false;
        secondAdComplete = false;
        
        // Reset countdown displays
        if (firstAdCountdown) firstAdCountdown.textContent = firstAdCountdownTime;
        if (secondAdCountdown) secondAdCountdown.textContent = secondAdCountdownTime;
    }

    function startFirstAdCountdown() {
        // Ignore if timer already running
        if (firstAdTimer) return;
        
        // Reset state
        firstAdComplete = false;
        
        // Start with full countdown time
        let secondsLeft = firstAdCountdownTime;
        if (firstAdCountdown) firstAdCountdown.textContent = secondsLeft;
        
        // Start timer
        firstAdTimer = setInterval(function() {
            secondsLeft--;
            
            // Update display
            if (firstAdCountdown) firstAdCountdown.textContent = secondsLeft;
            
            // Check if complete
            if (secondsLeft <= 0) {
                // Clear timer
                clearInterval(firstAdTimer);
                firstAdTimer = null;
                
                // Set completion flag
                firstAdComplete = true;
                
                // Enable continue button
                enableContinueButton();
            }
        }, updateInterval);
    }

    function startSecondAdCountdown() {
        // Ignore if timer already running
        if (secondAdTimer) return;
        
        // Reset state
        secondAdComplete = false;
        
        // Make sure the button is disabled
        if (viewResultsBtn) {
            viewResultsBtn.disabled = true;
            viewResultsBtn.classList.remove('btn-success', 'btn-pulse');
            viewResultsBtn.classList.add('btn-secondary');
            viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${secondAdCountdownTime}s)`;
        }
        
        // Start with full countdown time
        let secondsLeft = secondAdCountdownTime;
        if (secondAdCountdown) secondAdCountdown.textContent = secondsLeft;
        
        // Start timer
        secondAdTimer = setInterval(function() {
            secondsLeft--;
            
            // Update display
            if (secondAdCountdown) secondAdCountdown.textContent = secondsLeft;
            
            // Update button text
            if (viewResultsBtn) {
                viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${secondsLeft}s)`;
            }
            
            // Check if complete
            if (secondsLeft <= 0) {
                // Clear timer
                clearInterval(secondAdTimer);
                secondAdTimer = null;
                
                // Set completion flag
                secondAdComplete = true;
                
                // Enable results button
                enableViewResultsButton();
            }
        }, updateInterval);
    }

    function enableContinueButton() {
        // Create a new continue button with a clean event handler
        const continueBtn = document.getElementById('view-results-btn');
        if (!continueBtn) return;
        
        // Create a replacement button to clear stale handlers
        const newBtn = continueBtn.cloneNode(true);
        newBtn.disabled = false;
        newBtn.classList.remove('btn-secondary');
        newBtn.classList.add('btn-success', 'btn-pulse');
        newBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
        
        // Add a fresh click handler
        newBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Continue button clicked after first ad');
            
            // Hide the first ad overlay
            const firstAdOverlay = document.getElementById('ad-overlay-loading');
            if (firstAdOverlay) {
                firstAdOverlay.style.display = 'none';
            }
            
            // Make sure results container is visible
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.classList.remove('d-none');
            }
            
            // Show the second ad
            const secondAdOverlay = document.getElementById('ad-overlay-results');
            if (secondAdOverlay) {
                secondAdOverlay.style.display = 'flex';
            }
        });
        
        // Replace the button
        continueBtn.parentNode.replaceChild(newBtn, continueBtn);
    }

    function enableViewResultsButton() {
        // Show the button container first
        const btnContainer = document.getElementById('view-results-btn-container');
        if (btnContainer) {
            console.log('📢 Now showing the View Results button container');
            btnContainer.style.display = 'block';
        }

        // Get the view results button
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (!viewResultsBtn) return;
        
        // Create a replacement button to clear stale handlers
        const newBtn = viewResultsBtn.cloneNode(true);
        newBtn.disabled = false;
        newBtn.classList.remove('btn-secondary');
        newBtn.classList.add('btn-success', 'btn-pulse');
        newBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
        
        // Add a fresh click handler
        newBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('View Results button clicked after second ad');
            
            // Hide the second ad overlay
            const secondAdOverlay = document.getElementById('ad-overlay-results');
            if (secondAdOverlay) {
                secondAdOverlay.style.display = 'none';
            }
            
            // Show the results
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.classList.remove('d-none');
                resultsContainer.style.display = 'block';
            }
            
            // Set global flags
            window.resultsShown = true;
        });
        
        // Replace the button
        viewResultsBtn.parentNode.replaceChild(newBtn, viewResultsBtn);
        
        console.log('🎯 View Results button enabled and fully configured');
    }
})();