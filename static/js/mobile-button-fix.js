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
        
        // Disable the automatic force-enable of buttons
        // We'll now respect the ad system's countdown
        setTimeout(function() {
            console.log('iOS 15s deadline reached, but NOT forcing buttons - respecting ad system');
            // Don't call forceMobileButtonsActive() here anymore
            
            // Still set the attribute for compatibility with other scripts
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
                
                // DISABLED: No longer forcing button update
                // We'll respect the countdown from the ads-mobile.js script
                
                // Log but don't take action
                if (window.countdownStartTime && (Date.now() - window.countdownStartTime > 15000)) {
                    console.log('Old system would have forced button update, but now respecting ad system.');
                    // Do not call updateIOSButton(button) anymore
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
    
    // Set a periodic check for mobile waiting buttons - COMPLETELY DISABLED for ticket scanner
    setInterval(() => {
        // IMPORTANT! We ONLY check on non-ticket-scanner pages now
        if (!window.location.pathname.includes('ticket-scanner')) {
            // On non-ticket scanner pages, we can still help with stuck buttons
            console.log('Mobile button check: Non-ticket-scanner page, checking for stuck buttons');
            
            // Check only on non-scanner pages
            const allButtons = document.querySelectorAll('button');
            
            // Only process buttons on non-ticket-scanner pages
            allButtons.forEach(button => {
                if (button.innerText && button.innerText.includes('Wait')) {
                    console.log('Found View Results button with waiting text on non-scanner page');
                    
                    // Only unstick if not in an ad system
                    if (!window.SnapLottoAds || !window.SnapLottoAds.adDisplayActive) {
                        console.log('Non-ticket-scanner page: Unsticking button as normal');
                        button.disabled = false;
                        button.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                        button.classList.remove('btn-secondary');
                        button.classList.add('btn-success');
                    }
                }
            });
        } else {
            // Just diagnostic logging for ticket scanner page
            console.log('On ticket scanner page - mobile-button-fix is NOT modifying any buttons');
        }
    }, 2000); // Check every 2 seconds
});