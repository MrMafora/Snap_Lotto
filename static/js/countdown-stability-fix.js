/**
 * Countdown Button Stability Fix
 * 
 * This script prevents the View Results button from flashing on/off during countdown 
 * by intercepting any modifications to its visibility, opacity, or display properties.
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
    
    // Run on page load
    function initStabilization() {
        console.log('Initializing button stabilization');
        
        // Find all potential countdown buttons
        const countdownButtons = document.querySelectorAll('button.rounded-pill, #view-results-btn');
        
        countdownButtons.forEach(function(button) {
            if (button.textContent.includes('Wait')) {
                console.log('Stabilizing button:', button.textContent);
                stabilizeButton(button);
            }
        });
        
        // Set up a periodic check for new buttons
        setInterval(function() {
            const buttons = document.querySelectorAll('button');
            
            buttons.forEach(function(button) {
                if (button.textContent.includes('Wait') && !button.hasAttribute('data-stabilized')) {
                    console.log('Found new countdown button:', button.textContent);
                    stabilizeButton(button);
                }
            });
        }, 500); // Check every 500ms
        
        // Override any timers or animations that might affect the button
        const originalSetInterval = window.setInterval;
        window.setInterval = function(callback, time, ...args) {
            // Wrap the callback to check button state after each interval
            const wrappedCallback = function() {
                // Run original callback
                callback();
                
                // Then check for countdown buttons
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