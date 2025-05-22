/**
 * iOS-Specific Button Fix
 * 
 * This script specifically targets the iOS button format seen in the screenshot
 * with the rounded-pill class and "View Results (Wait 7s)" text.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('iOS-specific button fix loaded');
    
    // Check if using iOS device
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    
    if (isIOS) {
        console.log('iOS device detected - applying specific fixes');
        
        // Add a class to html for CSS targeting
        document.documentElement.classList.add('ios-device');
        
        // Direct targeting of the exact button format shown in screenshot
        setInterval(function() {
            // Find buttons with the specific format in screenshot
            const buttons = document.querySelectorAll('button.rounded-pill');
            
            buttons.forEach(function(btn) {
                if (btn.textContent && btn.textContent.includes('View Results (Wait')) {
                    // Check if 15 seconds have passed or if original countdown should be complete
                    if (window.countdownStartTime && (Date.now() - window.countdownStartTime > 15000)) {
                        console.log('iOS: Force-updating rounded-pill button', btn.textContent);
                        
                        // Update button appearance
                        btn.disabled = false;
                        btn.classList.remove('btn-secondary');
                        btn.classList.add('btn-success');
                        btn.style.opacity = '1';
                        btn.style.cursor = 'pointer';
                        
                        // Replace the content for this specific iOS format
                        btn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                        
                        // Add a direct click handler to ensure it works
                        btn.addEventListener('click', function(e) {
                            console.log('iOS-specific button clicked');
                            
                            // Handle all needed state changes
                            window.inResultsMode = true;
                            window.viewResultsBtnClicked = true;
                            window.adClosed = true;
                            window.showingResultsAfterAd = true;
                            
                            // Hide any ad overlays
                            document.querySelectorAll('[id^="ad-overlay"]').forEach(overlay => {
                                overlay.style.display = 'none';
                            });
                            
                            // Show results
                            const resultsContainer = document.getElementById('results-container');
                            if (resultsContainer) {
                                resultsContainer.classList.remove('d-none');
                                resultsContainer.style.display = 'block';
                                
                                // Display results if we have them
                                if (window.lastResultsData && typeof displayResults === 'function') {
                                    displayResults(window.lastResultsData);
                                }
                            }
                            
                            e.preventDefault();
                            return false;
                        }, true);
                    }
                }
            });
        }, 1000); // Check every second
    }
    
    // Add immediate check for existing buttons with the format "View Results (Wait 7s)" - directly fix the image format
    if (isIOS) {
        // Directly search for the button format shown in screenshot (within first 1 second)
        setTimeout(function() {
            // Direct search for the button using exact format
            console.log('Performing immediate check for iOS View Results buttons...');
            
            // Recursively check until we find the button or hit a limit
            let checkCount = 0;
            function checkForMobileButton() {
                if (checkCount++ > 20) return; // limit to 20 tries
                
                const allButtons = document.querySelectorAll('button');
                let foundButton = false;
                
                allButtons.forEach(function(btn) {
                    // Check for the exact format in screenshot "View Results (Wait 7s)"
                    if (btn.textContent && /View Results \(Wait \d+s\)/.test(btn.textContent)) {
                        console.log('FOUND THE BUTTON:', btn.textContent);
                        foundButton = true;
                        
                        // Create a direct event listener for when countdown completes
                        // This ensures that once the countdown reaches zero, the button updates
                        const originalSetTimeout = window.setTimeout;
                        window.setTimeout = function(callback, time) {
                            console.log('setTimeout intercepted:', time);
                            
                            // Check if this might be the countdown completion timer
                            if (time >= 14000 && time <= 16000) {
                                console.log('Detected countdown timeout, adding our hook');
                                const wrappedCallback = function() {
                                    // Call original callback
                                    callback();
                                    
                                    // Then force our button to update
                                    console.log('Running our hook to ensure button updates');
                                    const refreshedButton = document.querySelector('button.rounded-pill');
                                    if (refreshedButton && refreshedButton.textContent.includes('Wait')) {
                                        console.log('Button still shows Wait text, forcing update!');
                                        refreshedButton.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                                        refreshedButton.disabled = false;
                                        refreshedButton.classList.remove('btn-secondary');
                                        refreshedButton.classList.add('btn-success');
                                        refreshedButton.style.opacity = '1';
                                        refreshedButton.style.cursor = 'pointer';
                                    }
                                };
                                
                                return originalSetTimeout(wrappedCallback, time);
                            }
                            
                            return originalSetTimeout(callback, time);
                        };
                    }
                });
                
                if (!foundButton) {
                    // Try again after a short delay
                    setTimeout(checkForMobileButton, 500);
                }
            }
            
            // Start checking
            checkForMobileButton();
        }, 500);
    }
    
    // Add a global backup for any button after 16 seconds, regardless of device
    setTimeout(function() {
        // Find any buttons with "Wait" text and force them active
        const allButtons = document.querySelectorAll('button');
        
        allButtons.forEach(function(btn) {
            if (btn.textContent && btn.textContent.includes('Wait')) {
                console.log('Global 16s timeout reached - forcing button active:', btn.textContent);
                
                // Update button appearance
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
                
                // Apply success styling
                btn.classList.remove('btn-secondary');
                btn.classList.add('btn-success');
                
                // Update icon if present
                const icon = btn.querySelector('i.fa-lock');
                if (icon) {
                    icon.classList.remove('fa-lock');
                    icon.classList.add('fa-check-circle');
                }
                
                // Direct text replacement for "View Results (Wait Xs)" format
                if (btn.textContent.match(/View Results \(Wait \d+s\)/)) {
                    btn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
                }
            }
        });
    }, 16000); // 16 seconds after page load
});