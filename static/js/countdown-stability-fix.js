/**
 * Countdown Button Stability Fix - MAJOR UPDATE FOR MOBILE
 * 
 * This script prevents the View Results button from flashing on/off during countdown 
 * by intercepting any modifications to its visibility, opacity, or display properties.
 * 
 * Updated version adds multiple safeguards for mobile devices and includes
 * a complete independent countdown implementation to ensure reliability.
 */

(function() {
    console.log('Countdown stability fix loaded');
    
    // Function to stabilize a button during countdown
    function stabilizeButton(button) {
        if (!button) return;
        
        // Flag this button as being stabilized
        button.setAttribute('data-stabilized', 'true');
        
        // Apply stable classes
        button.classList.add('countdown-stable');
        
        // Store original button styles and attributes
        const originalStyle = Object.assign({}, button.style);
        const originalHTML = button.innerHTML;
        
        // Create and attach an observer to prevent unwanted style changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    // Check if style changes affect visibility
                    if (button.style.opacity !== '1' || 
                        button.style.display === 'none' || 
                        button.style.visibility === 'hidden') {
                        
                        console.log('Preventing button from becoming invisible during countdown');
                        
                        // Restore crucial visibility properties
                        button.style.opacity = '1';
                        button.style.display = originalStyle.display || 'inline-block';
                        button.style.visibility = 'visible';
                    }
                } else if (mutation.type === 'childList') {
                    // Ensure button text containing "Wait" is always visible
                    if (button.textContent.includes('Wait') && button.innerHTML !== originalHTML) {
                        // Only fix if content is being removed or changed incorrectly
                        if (!button.textContent.match(/View Results \(Wait \d+s\)/)) {
                            console.log('Fixing button text that was incorrectly changed');
                            button.innerHTML = originalHTML;
                        }
                    }
                }
            });
        });
        
        // Observe both style changes and content changes
        observer.observe(button, { 
            attributes: true, 
            attributeFilter: ['style', 'class'],
            childList: true,
            subtree: true
        });
        
        // Set stable inline styles that prevent flashing
        button.style.opacity = '1';
        button.style.visibility = 'visible';
        button.style.display = originalStyle.display || 'inline-block';
        
        // Prevent any animations that might cause flashing
        button.style.animation = 'none';
        button.style.transition = 'none';
    }
    
    // Independent countdown implementation - completely separate from any other countdown
    let backupCountdownActive = false;
    let backupCountdownStartTime = 0;
    let backupCountdownTotal = 15; // Default 15 seconds
    let backupCountdownInterval = null;
    
    function startBackupCountdown(button, container) {
        if (backupCountdownActive) {
            return; // Don't start if already running
        }
        
        console.log('Starting backup countdown system');
        
        // Store original button text
        const originalBtnText = button.getAttribute('data-original-text') || button.innerText.replace(/Wait.*/, 'View Results');
        button.setAttribute('data-original-text', originalBtnText);
        
        // Disable the button during countdown
        button.disabled = true;
        
        // Set initial values
        backupCountdownActive = true;
        backupCountdownStartTime = Date.now();
        
        // Stop any existing interval
        if (backupCountdownInterval) {
            clearInterval(backupCountdownInterval);
        }
        
        // Function to update countdown display
        function updateCountdown() {
            // Calculate remaining time
            const elapsedMs = Date.now() - backupCountdownStartTime;
            const elapsedSeconds = Math.floor(elapsedMs / 1000);
            const remainingSeconds = Math.max(0, backupCountdownTotal - elapsedSeconds);
            
            // Log for debugging
            console.log(`Backup countdown: ${remainingSeconds}s remaining`);
            
            // Update display
            if (remainingSeconds > 0) {
                // Update container text
                if (container) {
                    container.textContent = `Please wait ${remainingSeconds} seconds`;
                }
                
                // Update button text with multiple methods to ensure it works
                button.textContent = `Wait ${remainingSeconds}s`;
                button.innerText = `Wait ${remainingSeconds}s`;
                
                // Force disabled state
                button.disabled = true;
            } else {
                // Time's up! Enable the button
                if (container) {
                    container.textContent = 'You can now view your results!';
                }
                
                // Update button with multiple methods
                button.textContent = originalBtnText;
                button.innerText = originalBtnText;
                
                // Enable the button using multiple methods to ensure it works
                button.disabled = false;
                button.removeAttribute('disabled');
                
                // Add visual cue
                button.classList.add('btn-pulse');
                
                // Stop the countdown
                clearInterval(backupCountdownInterval);
                backupCountdownActive = false;
                console.log('Backup countdown completed!');
            }
        }
        
        // Start the interval
        backupCountdownInterval = setInterval(updateCountdown, 1000);
        
        // Run immediately
        updateCountdown();
    }
    
    // Function to detect and take over countdown 
    function detectAndFixCountdown() {
        const viewResultsBtn = document.getElementById('view-results-btn');
        const countdownContainer = document.getElementById('countdown-container');
        
        if (viewResultsBtn && viewResultsBtn.innerText.includes('Wait') && !backupCountdownActive) {
            // Extract the total countdown time if possible
            const timeMatch = viewResultsBtn.innerText.match(/Wait\s+(\d+)s/);
            if (timeMatch && timeMatch[1]) {
                backupCountdownTotal = parseInt(timeMatch[1], 10);
            }
            
            console.log(`Found stuck countdown button with ${backupCountdownTotal}s, taking over...`);
            startBackupCountdown(viewResultsBtn, countdownContainer);
        }
    }
    
    // Run on page load
    function initStabilization() {
        console.log('Initializing button stabilization');
        
        // Find all potential countdown buttons
        const countdownButtons = document.querySelectorAll('button.rounded-pill, #view-results-btn');
        
        countdownButtons.forEach(function(button) {
            if (button.textContent.includes('Wait')) {
                console.log('Stabilizing button:', button.textContent);
                stabilizeButton(button);
                
                // Check if this is a countdown that needs takeover
                detectAndFixCountdown();
            }
        });
        
        // Enhanced periodic check for new buttons and countdown issues
        setInterval(function() {
            const buttons = document.querySelectorAll('button');
            
            // Check for new buttons to stabilize
            buttons.forEach(function(button) {
                if (button.textContent.includes('Wait') && !button.hasAttribute('data-stabilized')) {
                    console.log('Found new countdown button:', button.textContent);
                    stabilizeButton(button);
                }
            });
            
            // Look for a specific pattern that indicates a frozen countdown
            const viewResultsBtn = document.getElementById('view-results-btn');
            if (viewResultsBtn && viewResultsBtn.innerText.includes('Wait') && 
                !backupCountdownActive && viewResultsBtn.disabled) {
                
                // If the button text hasn't changed for 3 seconds, assume countdown is stuck
                const currentText = viewResultsBtn.innerText;
                viewResultsBtn.setAttribute('data-last-text', currentText);
                
                setTimeout(() => {
                    if (viewResultsBtn.innerText === currentText && 
                        currentText === viewResultsBtn.getAttribute('data-last-text')) {
                        console.log('Detected frozen countdown, taking over');
                        detectAndFixCountdown();
                    }
                }, 3000);
            }
        }, 500); // Check every 500ms
        
        // Watch for ad overlay becoming visible
        const adOverlayResults = document.getElementById('ad-overlay-results');
        if (adOverlayResults) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                        if (adOverlayResults.style.display === 'flex') {
                            console.log('Ad overlay results became visible, checking countdown');
                            
                            // Wait a bit for the DOM to update
                            setTimeout(() => {
                                detectAndFixCountdown();
                            }, 500);
                        }
                    }
                });
            });
            
            // Start observing
            observer.observe(adOverlayResults, { attributes: true });
        }
        
        // Override any timers or animations that might affect the button
        const originalSetInterval = window.setInterval;
        window.setInterval = function(callback, time, ...args) {
            // Wrap the callback to check button state after each interval
            const wrappedCallback = function() {
                try {
                    // Run original callback
                    callback();
                } catch (e) {
                    console.error('Error in countdown interval:', e);
                }
                
                // Check for countdown buttons
                const countdownButtons = document.querySelectorAll('button');
                countdownButtons.forEach(function(button) {
                    if (button.textContent.includes('Wait')) {
                        // Ensure button is visible
                        button.style.opacity = '1';
                        button.style.visibility = 'visible';
                        button.style.display = button.style.display || 'inline-block';
                    }
                });
            };
            
            return originalSetInterval(wrappedCallback, time, ...args);
        };
    }
    
    // Run on document ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initStabilization);
    } else {
        initStabilization();
    }
})();