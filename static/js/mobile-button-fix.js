/**
 * Mobile Button Fix for Snap Lotto
 * 
 * This script specifically addresses iOS/mobile button issues where the countdown text
 * doesn't update properly. It periodically checks for buttons with lock icons that 
 * still show "Wait" text after countdown completion and forces them to update.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Mobile button fix script loaded');
    
    // Check if using iOS (the one with the specific button format issue)
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    if (isIOS) {
        console.log('iOS device detected, applying special button handling');
        
        // Add iOS class to html for CSS targeting
        document.documentElement.classList.add('ios-detected');
        
        // iOS specific direct fix for the button format shown in screenshot
        // Instead of waiting for the countdown, we'll directly update any button with the format "View Results (Wait Xs)"
        
        // First setup a mutation observer to watch for these buttons
        const bodyObserver = new MutationObserver(function(mutations) {
            // Check for buttons with the specific format after each DOM change
            checkForIOSButtons();
        });
        
        // Start observing
        bodyObserver.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
        
        // Also set a timer to periodically check for these buttons
        setInterval(checkForIOSButtons, 1000);
        
        // Set a backup deadline for 15s after page load to force all buttons to active state
        setTimeout(function() {
            console.log('iOS 15s deadline reached, forcing all wait buttons to active state');
            forceMobileButtonsActive();
            
            // Set attribute on html to mark countdown as completed
            document.documentElement.setAttribute('data-countdown-completed', 'true');
        }, 16000);
    }
    
    // Function to check for iOS-specific button format
    function checkForIOSButtons() {
        // Find any button containing "View Results (Wait"
        const buttons = document.querySelectorAll('button');
        
        buttons.forEach(function(button) {
            if (button.innerText && button.innerText.includes('View Results (Wait')) {
                console.log('Found iOS wait button format:', button.innerText);
                
                // Check if countdown should be complete
                if (window.countdownStartTime && (Date.now() - window.countdownStartTime > 15000)) {
                    console.log('Countdown should be complete, updating button');
                    updateIOSButton(button);
                }
            }
        });
    }
    
    // Function to update a specific iOS button
    function updateIOSButton(button) {
        // Update button text and appearance
        button.disabled = false;
        button.style.opacity = '1';
        button.style.cursor = 'pointer';
        
        // Update icon from lock to checkmark
        const icon = button.querySelector('i.fa-lock');
        if (icon) {
            icon.classList.remove('fa-lock');
            icon.classList.add('fa-check-circle');
        }
        
        // Replace text
        button.innerText = button.innerText.replace(/View Results \(Wait \d+s\)/, 'View Results Now!');
        
        // Add visual indication
        button.classList.remove('btn-secondary');
        button.classList.add('btn-success');
        
        // Add click event that will immediately show results
        button.addEventListener('click', function(e) {
            // Hide ad overlay
            const adOverlay = document.getElementById('ad-overlay-results');
            if (adOverlay) {
                adOverlay.style.display = 'none';
            }
            
            // Show results
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.classList.remove('d-none');
                resultsContainer.style.display = 'block';
            }
            
            // Set state flags
            window.inResultsMode = true;
            window.adClosed = true;
            window.viewResultsBtnClicked = true;
            window.showingResultsAfterAd = true;
            
            // Display results if available
            if (window.lastResultsData && typeof displayResults === 'function') {
                displayResults(window.lastResultsData);
            }
        });
    }
    
    // Force ALL wait buttons to be active
    function forceMobileButtonsActive() {
        const allButtons = document.querySelectorAll('button');
        allButtons.forEach(function(btn) {
            if (btn.innerText && (btn.innerText.includes('Wait') || btn.disabled)) {
                console.log('Forcing button active:', btn.innerText);
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
                
                if (btn.innerText.includes('View Results (Wait')) {
                    // Replace text for view results button
                    btn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                    btn.classList.remove('btn-secondary');
                    btn.classList.add('btn-success');
                }
            }
        });
    }
    
    // Set a periodic check for mobile waiting buttons
    setInterval(() => {
        // Check if countdown should be completed (15 seconds after starting)
        if (window.countdownStartTime && (Date.now() - window.countdownStartTime > 15000)) {
            console.log('Mobile button check: More than 15s since countdown start, checking for stuck buttons');
            
            // Find all buttons on the page
            const allButtons = document.querySelectorAll('button');
            
            // Check each button for a waiting message
            allButtons.forEach(button => {
                if (button.innerText && button.innerText.includes('Wait')) {
                    console.log('Found mobile button still showing Wait message after 15s', button);
                    
                    // Force update the button
                    button.disabled = false;
                    button.style.opacity = '1';
                    button.style.cursor = 'pointer';
                    
                    // Add visual indication
                    button.classList.remove('btn-secondary');
                    button.classList.add('btn-success');
                    
                    // Update text and icon (lock to checkmark)
                    const lockIcon = button.querySelector('.fa-lock');
                    if (lockIcon) {
                        lockIcon.classList.remove('fa-lock');
                        lockIcon.classList.add('fa-check-circle');
                    }
                    
                    // Update any spans containing "Wait" text
                    const spans = button.querySelectorAll('span');
                    spans.forEach(span => {
                        if (span.textContent && span.textContent.includes('Wait')) {
                            span.textContent = 'View Results Now!';
                        }
                    });
                    
                    // Direct replacement if format is exactly like in screenshot
                    if (button.innerHTML.includes('View Results (Wait')) {
                        button.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                    }
                    
                    // Add click handler to force show results
                    button.addEventListener('click', function(e) {
                        console.log('Mobile fixed button clicked');
                        
                        // Force show results
                        const resultsContainer = document.getElementById('results-container');
                        if (resultsContainer) {
                            resultsContainer.classList.remove('d-none');
                            resultsContainer.style.display = 'block';
                        }
                        
                        // Hide ad overlays
                        document.querySelectorAll('[id^="ad-overlay"]').forEach(overlay => {
                            overlay.style.display = 'none';
                        });
                        
                        // Hide scan form
                        const scanForm = document.getElementById('scan-form-container');
                        if (scanForm) {
                            scanForm.classList.add('d-none');
                        }
                        
                        // Set global flags
                        window.inResultsMode = true;
                        window.viewResultsBtnClicked = true;
                        window.adClosed = true;
                        window.showingResultsAfterAd = true;
                        
                        // Display results if available
                        if (window.lastResultsData && typeof displayResults === 'function') {
                            displayResults(window.lastResultsData);
                        }
                        
                        e.preventDefault();
                        return false;
                    }, true);
                }
            });
        }
    }, 2000); // Check every 2 seconds
});