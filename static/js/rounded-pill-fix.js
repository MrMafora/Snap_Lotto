/**
 * Direct Fix for Rounded Pill Button
 * 
 * This script specifically targets the button format seen in the screenshot
 * with class="rounded-pill" and text "View Results (Wait 7s)"
 */

(function() {
    // Run immediately on script load
    console.log('Rounded-pill button fix loaded');
    
    // Direct fix for the specific button format
    function fixRoundedPillButton() {
        // IMPORTANT: Skip this fix on the ticket-scanner page where we have a better system
        if (window.location.pathname.includes('ticket-scanner')) {
            // Only log once per page load to avoid console spam
            if (!window.loggedTicketScannerSkip) {
                console.log('⚠️ SKIPPING rounded-pill fix on ticket-scanner page');
                window.loggedTicketScannerSkip = true;
            }
            return;
        }
        
        // Look for any button matching the format in the screenshot
        const buttons = document.querySelectorAll('button');
        
        buttons.forEach(function(btn) {
            // Check for the specific format "View Results (Wait Xs)"
            if (btn.textContent && btn.textContent.match(/View Results \(Wait \d+s\)/)) {
                console.log('Found View Results button with waiting text:', btn.textContent);
                
                // Check if we should override the button (15s elapsed since page load)
                const pageLoadTime = window.performance.timing.navigationStart;
                const timeNow = Date.now();
                const timeElapsed = timeNow - pageLoadTime;
                
                if (timeElapsed > 15000) {
                    console.log('Page loaded more than 15s ago, forcing button to active state');
                    
                    // Update button
                    btn.disabled = false;
                    btn.classList.remove('btn-secondary');
                    btn.classList.add('btn-success');
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                    btn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                    
                    // Add click handler
                    btn.addEventListener('click', function(e) {
                        // Force show results
                        const resultsContainer = document.getElementById('results-container');
                        if (resultsContainer) {
                            resultsContainer.classList.remove('d-none');
                            resultsContainer.style.display = 'block';
                        }
                        
                        // Hide ad overlay
                        const adOverlay = document.getElementById('ad-overlay-results');
                        if (adOverlay) {
                            adOverlay.style.display = 'none';
                        }
                        
                        // Store that we've shown results
                        window.inResultsMode = true;
                        window.adClosed = true;
                        window.viewResultsBtnClicked = true;
                        
                        e.preventDefault();
                        return false;
                    }, true);
                } else {
                    // Monitor this button to ensure it updates when the countdown completes
                    const countdownMatch = btn.textContent.match(/Wait (\d+)s/);
                    if (countdownMatch && countdownMatch[1]) {
                        const secondsRemaining = parseInt(countdownMatch[1], 10);
                        console.log('Button shows', secondsRemaining, 'seconds remaining');
                        
                        // Set a timeout to check this button when countdown should be complete
                        setTimeout(function() {
                            // IMPORTANT: Skip this check on the ticket-scanner page
                            if (window.location.pathname.includes('ticket-scanner')) {
                                console.log('⚠️ SKIPPING button update check on ticket-scanner page');
                                return;
                            }
                            
                            console.log('Checking if button has updated...');
                            
                            // Find the button again (might have been replaced)
                            const updatedBtn = document.querySelector('button.rounded-pill');
                            if (updatedBtn && updatedBtn.textContent.includes('Wait')) {
                                console.log('Button still shows Wait text after countdown should be complete!');
                                
                                // Force update
                                updatedBtn.disabled = false;
                                updatedBtn.classList.remove('btn-secondary');
                                updatedBtn.classList.add('btn-success');
                                updatedBtn.style.opacity = '1';
                                updatedBtn.style.cursor = 'pointer';
                                updatedBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                            }
                        }, (secondsRemaining + 1) * 1000);
                    }
                }
            }
        });
    }
    
    // Run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Only run this script on non-ticket-scanner pages
            if (!window.location.pathname.includes('ticket-scanner')) {
                fixRoundedPillButton();
                // Check periodically, but only on non-ticket-scanner pages
                setInterval(fixRoundedPillButton, 1000);
            } else {
                console.log('⚠️ DISABLED rounded-pill fix on ticket-scanner page');
            }
        });
    } else {
        // DOM already loaded
        // Only run this script on non-ticket-scanner pages
        if (!window.location.pathname.includes('ticket-scanner')) {
            fixRoundedPillButton();
            // Check periodically, but only on non-ticket-scanner pages
            setInterval(fixRoundedPillButton, 1000);
        } else {
            console.log('⚠️ DISABLED rounded-pill fix on ticket-scanner page');
        }
    }
})();