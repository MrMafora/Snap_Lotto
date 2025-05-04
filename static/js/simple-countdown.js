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
        
        // Make sure the button is disabled and hidden initially
        // (The button container is now hidden by default in HTML)
        if (viewResultsBtn) {
            viewResultsBtn.disabled = true;
            viewResultsBtn.setAttribute('disabled', 'disabled'); // Double ensure disabled state
            viewResultsBtn.classList.remove('btn-success', 'btn-pulse');
            viewResultsBtn.classList.add('btn-secondary', 'disabled'); // Add disabled class for visual indication
            viewResultsBtn.style.pointerEvents = 'none'; // Prevent any click events
            viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${secondAdCountdownTime}s)`;
            
            // Force browser to recognize disabled state
            viewResultsBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            };
        }
        
        // Start with full countdown time
        let secondsLeft = secondAdCountdownTime;
        if (secondAdCountdown) secondAdCountdown.textContent = secondsLeft;
        
        // Signal that second ad started (for coordination with ad-countdown-fix.js)
        console.log('🔔 Sending adStateChange message to notify of second ad start');
        window.postMessage({ 
            type: 'adStateChange', 
            adType: 'second', 
            state: 'start', 
            timestamp: Date.now(),
            source: 'simple-countdown'
        }, '*');
        
        // Start timer - ONLY UPDATES COUNTDOWN DISPLAY, doesn't control button anymore
        secondAdTimer = setInterval(function() {
            secondsLeft--;
            
            // Update display
            if (secondAdCountdown) secondAdCountdown.textContent = secondsLeft;
            
            // Only update text - button activation is now handled by ad-countdown-fix.js
            if (viewResultsBtn && secondsLeft > 0) {
                // Ensure button remains disabled during countdown
                viewResultsBtn.disabled = true;
                viewResultsBtn.setAttribute('disabled', 'disabled');
                viewResultsBtn.classList.remove('btn-success', 'btn-pulse');
                viewResultsBtn.classList.add('btn-secondary', 'disabled');
                viewResultsBtn.style.pointerEvents = 'none';
                viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${secondsLeft}s)`;
            }
            
            // When countdown finishes, just clear the timer - 
            // ad-countdown-fix.js will handle button enablement consistently
            if (secondsLeft <= 0) {
                // Clear timer
                clearInterval(secondAdTimer);
                secondAdTimer = null;
                
                // Set completion flag
                secondAdComplete = true;
                
                console.log('🔄 Second ad countdown finished in simple-countdown.js');
                // We no longer enable the button directly here
                // enableViewResultsButton() call removed
            }
        }, updateInterval);
    }

    function enableContinueButton() {
        console.log("⚠️ simple-countdown.js: enableContinueButton DEPRECATED - Now handled by ad-countdown-fix.js");
        
        // Signal to ad-countdown-fix.js that we've reached this point
        window.postMessage({ 
            type: 'adStateChange', 
            adType: 'first', 
            state: 'complete', 
            timestamp: Date.now(),
            source: 'simple-countdown'
        }, '*');
        
        // Don't directly manipulate the button anymore
        return;
    }

    function enableViewResultsButton() {
        console.log("⚠️ simple-countdown.js: enableViewResultsButton DEPRECATED - Now handled by ad-countdown-fix.js");
        
        // Signal to ad-countdown-fix.js that we've reached this point
        window.postMessage({ 
            type: 'adStateChange', 
            adType: 'second', 
            state: 'complete', 
            timestamp: Date.now(),
            source: 'simple-countdown'
        }, '*');
        
        // Don't directly manipulate the button anymore
        return;
    }
})();