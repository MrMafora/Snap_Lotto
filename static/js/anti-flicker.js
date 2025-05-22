/**
 * Anti-Flicker Script for iOS Countdown Button
 * 
 * This script specifically targets the flashing button issue observed on iOS 
 * where the "View Results (Wait Xs)" button flashes on/off during countdown.
 */

(function() {
    // Execute immediately on script load (highest priority)
    console.log('Anti-flicker script loaded');
    
    // Reference to the original setInterval to restore later
    const originalSetInterval = window.setInterval;
    // Reference to the original setTimeout to restore later
    const originalSetTimeout = window.setTimeout;
    
    // Flag to track if we're currently in countdown mode
    window.inCountdownMode = false;
    
    // Function to apply anti-flicker CSS rules immediately
    function applyAntiFlickerStyles() {
        console.log('Applying anti-flicker styles');
        
        // Create a style element if it doesn't exist
        let styleElement = document.getElementById('anti-flicker-styles');
        if (!styleElement) {
            styleElement = document.createElement('style');
            styleElement.id = 'anti-flicker-styles';
            document.head.appendChild(styleElement);
        }
        
        // Apply critical CSS rules to prevent flashing
        styleElement.textContent = `
            /* Force button visibility in countdown mode */
            .btn.rounded-pill,
            #view-results-btn,
            button:not(.d-none)[id="view-results-btn"],
            button.rounded-pill,
            button.btn-lg.rounded-pill,
            button:not(.d-none).countdown-active {
                opacity: 1 !important;
                visibility: visible !important;
                display: inline-block !important;
                animation: none !important;
                transition: none !important;
                transform: none !important;
                position: relative !important;
                pointer-events: auto !important;
                user-select: auto !important;
            }
            
            /* Ensure countdown container remains visible */
            #countdown-container {
                opacity: 1 !important;
                visibility: visible !important;
                display: block !important;
            }
        `;
    }
    
    // Apply immediate styles for existing elements
    applyAntiFlickerStyles();
    
    // Function to prevent button flicker by overriding interval callbacks
    function installAntiFlickerHooks() {
        // Override setInterval to catch and modify countdown timers
        window.setInterval = function(callback, time, ...args) {
            // If this might be a countdown timer (updating every 1000ms)
            if (time === 1000) {
                const wrappedCallback = function() {
                    // Ensure anti-flicker styles are applied before each tick
                    applyAntiFlickerStyles();
                    
                    // Run the original callback
                    callback();
                    
                    // After callback, find countdown buttons and ensure they're visible
                    setTimeout(function() {
                        const buttons = document.querySelectorAll('button');
                        buttons.forEach(function(btn) {
                            if (btn.textContent && btn.textContent.includes('Wait')) {
                                // Apply anti-flicker styles directly to this button
                                btn.style.opacity = '1';
                                btn.style.visibility = 'visible';
                                btn.style.display = 'inline-block';
                                btn.classList.add('countdown-active');
                            }
                        });
                    }, 0);
                };
                
                // Return modified interval
                return originalSetInterval(wrappedCallback, time, ...args);
            }
            
            // Return standard interval for other cases
            return originalSetInterval(callback, time, ...args);
        };
        
        // Override setTimeout to catch the end of the countdown
        window.setTimeout = function(callback, time, ...args) {
            // If this might be the countdown completion timer (usually 15000ms)
            if (time >= 14000 && time <= 16000) {
                // This is likely our 15-second countdown completion timer
                window.inCountdownMode = true;
                
                const wrappedCallback = function() {
                    // Run the original callback
                    callback();
                    
                    // Countdown completed, we can restore original functions
                    window.inCountdownMode = false;
                    console.log('Countdown completed, restoring normal button behavior');
                };
                
                // Return modified timeout
                return originalSetTimeout(wrappedCallback, time, ...args);
            }
            
            // Return standard timeout for other cases
            return originalSetTimeout(callback, time, ...args);
        };
    }
    
    // Install the anti-flicker hooks immediately
    installAntiFlickerHooks();
    
    // Continuously check for the specific View Results button and stabilize it
    function startButtonMonitoring() {
        // Initial check (run immediately)
        checkForCountdownButton();
        
        // Also set up periodic monitoring using the original setInterval
        originalSetInterval(checkForCountdownButton, 200);
    }
    
    // Function to check for the countdown button and stabilize it
    function checkForCountdownButton() {
        // Look for any button with the Wait text
        const buttons = document.querySelectorAll('button');
        
        buttons.forEach(function(btn) {
            if (btn.textContent && btn.textContent.match(/Wait \d+s/)) {
                // Found countdown button - apply stability fixes
                btn.classList.add('countdown-active');
                btn.style.opacity = '1';
                btn.style.visibility = 'visible';
                btn.style.display = 'inline-block';
                btn.style.animation = 'none';
                btn.style.transition = 'none';
                
                // Set attribute for CSS targeting
                btn.setAttribute('data-countdown-stabilized', 'true');
                
                // Add specific class if it matches the pattern in screenshot
                if (btn.textContent.match(/View Results \(Wait \d+s\)/)) {
                    btn.classList.add('view-results-countdown');
                    
                    // Create an observer for this button to prevent any style changes
                    const observer = new MutationObserver(function(mutations) {
                        mutations.forEach(function(mutation) {
                            if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                                // Ensure the button remains visible if it was changed
                                if (btn.style.opacity !== '1' || 
                                    btn.style.display === 'none' || 
                                    btn.style.visibility === 'hidden') {
                                    
                                    console.log('Fixing button visibility during countdown');
                                    btn.style.opacity = '1';
                                    btn.style.visibility = 'visible';
                                    btn.style.display = 'inline-block';
                                }
                            }
                        });
                    });
                    
                    // Start observing style changes
                    observer.observe(btn, { 
                        attributes: true, 
                        attributeFilter: ['style', 'class'] 
                    });
                }
            }
        });
    }
    
    // Start monitoring for countdown buttons
    startButtonMonitoring();
})();