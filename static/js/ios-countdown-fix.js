/**
 * iOS Countdown Button Fix
 * 
 * This script specifically addresses the flashing button issue during countdown on iOS devices
 * Direct approach to prevent any visual flashing during the countdown
 */

(function() {
    // Execute immediately - highest priority
    console.log('iOS countdown button fix loaded');
    
    // Define the expected countdown button format in the screenshot
    const BUTTON_PATTERN = /View Results \(Wait \d+s\)/;
    
    // Detect iOS
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    
    if (isIOS) {
        // Set a data attribute on the body for CSS targeting
        document.documentElement.setAttribute('data-user-agent', navigator.userAgent);
        document.documentElement.classList.add('ios-device');
        
        // Create a style tag with critical CSS that will prevent any flashing
        const styleTag = document.createElement('style');
        styleTag.id = 'ios-button-critical-css';
        styleTag.innerHTML = `
            /* Critical CSS to prevent any button flashing */
            button.rounded-pill,
            button.btn.rounded-pill,
            button#view-results-btn,
            button.btn[id="view-results-btn"],
            button.btn-success.btn-lg,
            .btn.rounded-pill,
            #view-results-btn {
                opacity: 1 !important;
                visibility: visible !important;
                display: inline-block !important;
                animation: none !important;
                transition: none !important;
                transform: none !important;
                position: static !important;
                z-index: 10000 !important;
                -webkit-transform: translateZ(0);
                transform: translateZ(0);
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
            }
            
            /* Ensure countdown container is always visible */
            #countdown-container {
                opacity: 1 !important;
                visibility: visible !important;
                display: block !important;
            }
        `;
        
        // Add the style tag to the head with highest priority
        document.head.appendChild(styleTag);
        
        // Define a MutationObserver that will stabilize any countdown buttons
        const buttonObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' || mutation.type === 'attributes') {
                    // Look for any buttons matching the pattern
                    const buttons = document.querySelectorAll('button');
                    
                    buttons.forEach(function(btn) {
                        if (btn.textContent && BUTTON_PATTERN.test(btn.textContent)) {
                            console.log('Found countdown button:', btn.textContent);
                            stabilizeButton(btn);
                        }
                    });
                }
            });
        });
        
        // Start observing the document
        buttonObserver.observe(document.documentElement, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
        
        // Function to stabilize a countdown button
        function stabilizeButton(button) {
            // Add stable appearance by locking all visual properties
            button.style.setProperty('opacity', '1', 'important');
            button.style.setProperty('visibility', 'visible', 'important');
            button.style.setProperty('display', 'inline-block', 'important');
            button.style.setProperty('animation', 'none', 'important');
            button.style.setProperty('transition', 'none', 'important');
            button.style.setProperty('transform', 'none', 'important');
            button.style.setProperty('pointer-events', 'auto', 'important');
            button.style.setProperty('position', 'static', 'important');
            button.style.setProperty('z-index', '10000', 'important');
            
            // Add marker class
            button.classList.add('ios-stabilized');
            
            // Clear any existing timers or animations directly affecting this button
            if (button._intervalIds) {
                button._intervalIds.forEach(clearInterval);
            }
            button._intervalIds = [];
            
            // Create a protective observer for this specific button
            const buttonProtector = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                        // If style changed to make the button invisible, restore visibility
                        if (button.style.opacity !== '1' || 
                            button.style.display === 'none' || 
                            button.style.visibility === 'hidden') {
                            
                            console.log('Preventing button from hiding during countdown');
                            button.style.setProperty('opacity', '1', 'important');
                            button.style.setProperty('visibility', 'visible', 'important');
                            button.style.setProperty('display', 'inline-block', 'important');
                        }
                    }
                });
            });
            
            // Start protecting this button
            buttonProtector.observe(button, {
                attributes: true,
                attributeFilter: ['style', 'class']
            });
            
            // Store observer reference to disconnect later if needed
            button._protector = buttonProtector;
        }
        
        // Immediate check for existing buttons
        setTimeout(function() {
            const buttons = document.querySelectorAll('button');
            buttons.forEach(function(btn) {
                if (btn.textContent && BUTTON_PATTERN.test(btn.textContent)) {
                    console.log('Found countdown button on initial check:', btn.textContent);
                    stabilizeButton(btn);
                }
            });
        }, 0);
        
        // Set up periodical checks
        setInterval(function() {
            const buttons = document.querySelectorAll('button');
            buttons.forEach(function(btn) {
                if (btn.textContent && BUTTON_PATTERN.test(btn.textContent)) {
                    if (!btn.classList.contains('ios-stabilized')) {
                        console.log('Found new countdown button:', btn.textContent);
                        stabilizeButton(btn);
                    }
                }
            });
        }, 500);
    }
})();