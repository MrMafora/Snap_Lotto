/**
 * Emergency Button Fix with Advertisement Integration
 * This is a critical emergency fix for the file selection button
 * that uses a completely isolated approach to avoid all conflicts
 * while preserving the advertisement system
 */

// Run this script as late as possible to override any other scripts
document.addEventListener('DOMContentLoaded', function() {
    console.log('[EMERGENCY] Emergency button fix initializing with ad integration');
    
    // Use setTimeout to ensure this runs after all other scripts
    setTimeout(function() {
        directlyFixButton();
    }, 500);
    
    // Also set up a periodic check to ensure the button always works
    setInterval(function() {
        directlyFixButton();
    }, 2000);
    
    function directlyFixButton() {
        console.log('[EMERGENCY] Directly fixing file select button');
        
        // Find the original button and remove it completely
        const originalBtn = document.getElementById('file-select-btn');
        if (originalBtn) {
            const container = originalBtn.parentNode;
            if (container) {
                // Create a completely new button with a different ID to avoid conflicts
                const newBtn = document.createElement('button');
                newBtn.id = 'emergency-file-select-btn';
                newBtn.className = originalBtn.className; // Copy all classes
                newBtn.innerHTML = originalBtn.innerHTML; // Copy inner HTML
                newBtn.type = 'button';
                
                // Add a very explicit style to ensure it's visible
                newBtn.style.display = 'inline-block';
                newBtn.style.padding = '10px 20px';
                newBtn.style.fontSize = '16px';
                newBtn.style.cursor = 'pointer';
                
                // Add clear debugging information for diagnostics
                console.log('[EMERGENCY] Adding emergency button with direct click handler');
                
                // Use the most direct approach possible to handle clicks
                newBtn.onclick = function(e) {
                    // Prevent default behavior and stop propagation
                    e.preventDefault();
                    e.stopPropagation();
                    
                    console.log('[EMERGENCY] Emergency file select button clicked');
                    
                    // Reset any file dialog state
                    if (window.fileDialogState) {
                        window.fileDialogState.isSelectingFile = false;
                        window.fileDialogState.lastDialogTime = 0;
                    }
                    
                    // Find the file input element
                    const fileInput = document.getElementById('ticket-image');
                    if (fileInput) {
                        console.log('[EMERGENCY] Found file input, directly triggering click');
                        
                        // Use the most direct method to trigger the file input
                        try {
                            // Use native DOM method to create a trusted click event
                            const clickEvent = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            fileInput.dispatchEvent(clickEvent);
                        } catch (error) {
                            console.error('[EMERGENCY] Error triggering file input:', error);
                            
                            // Fallback method
                            try {
                                console.log('[EMERGENCY] Using fallback click method');
                                fileInput.click();
                            } catch (fallbackError) {
                                console.error('[EMERGENCY] Fallback also failed:', fallbackError);
                            }
                        }
                    } else {
                        console.error('[EMERGENCY] Could not find file input element (ticket-image)');
                    }
                    
                    return false;
                };
                
                // Replace the original button with our emergency version
                container.replaceChild(newBtn, originalBtn);
                console.log('[EMERGENCY] Replaced original button with emergency version');
                
                // Add a directive click handler on the parent container too for redundancy
                container.addEventListener('click', function(e) {
                    if (e.target && e.target.id === 'emergency-file-select-btn') {
                        console.log('[EMERGENCY] Container-level click detected');
                    }
                }, true);
            }
        } else {
            console.warn('[EMERGENCY] Could not find original file select button');
        }
    }
    
    // CRITICAL ADVERTISEMENT SYSTEM INTEGRATION
    // We need to hook into the file upload completion to trigger ads
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;
    
    // Intercept all XHR requests to check for ticket scanning completion
    XMLHttpRequest.prototype.open = function() {
        this._ticketScannerUrl = arguments[1];
        return originalXHROpen.apply(this, arguments);
    };
    
    XMLHttpRequest.prototype.send = function() {
        // Only hook into ticket scanner requests
        if (this._ticketScannerUrl && this._ticketScannerUrl.includes('/scan-ticket')) {
            this.addEventListener('load', function() {
                if (this.status === 200) {
                    console.log('[EMERGENCY] Ticket scan completed successfully, triggering ad system');
                    try {
                        const response = JSON.parse(this.responseText);
                        
                        // Store the results data for later use
                        window.lastResultsData = response;
                        
                        // First trigger the public service announcement (5 seconds)
                        const adOverlayLoading = document.getElementById('ad-overlay-loading');
                        if (adOverlayLoading) {
                            console.log('[EMERGENCY] Showing 5-second public service announcement');
                            adOverlayLoading.style.display = 'flex';
                            document.body.style.overflow = 'hidden';
                            
                            // Then show the monetization ad after 5 seconds
                            setTimeout(function() {
                                console.log('[EMERGENCY] Public service announcement completed, switching to monetization ad');
                                adOverlayLoading.style.display = 'none';
                                
                                const adOverlayResults = document.getElementById('ad-overlay-results');
                                if (adOverlayResults) {
                                    // Show the monetization ad (15 seconds)
                                    adOverlayResults.style.display = 'flex';
                                    
                                    // Update the countdown display
                                    const countdownElement = document.getElementById('countdown');
                                    if (countdownElement) {
                                        let remainingSeconds = 15;
                                        countdownElement.textContent = remainingSeconds;
                                        
                                        const intervalId = setInterval(function() {
                                            remainingSeconds--;
                                            countdownElement.textContent = remainingSeconds;
                                            
                                            if (remainingSeconds <= 0) {
                                                clearInterval(intervalId);
                                                
                                                // Enable the View Results button
                                                const viewResultsBtn = document.getElementById('view-results-btn');
                                                if (viewResultsBtn) {
                                                    viewResultsBtn.disabled = false;
                                                    viewResultsBtn.classList.remove('btn-secondary');
                                                    viewResultsBtn.classList.add('btn-success');
                                                    viewResultsBtn.classList.add('btn-pulse');
                                                }
                                                
                                                // Show the View Results button container
                                                const viewResultsBtnContainer = document.getElementById('view-results-btn-container');
                                                if (viewResultsBtnContainer) {
                                                    viewResultsBtnContainer.style.display = 'block';
                                                }
                                            }
                                        }, 1000);
                                    }
                                } else {
                                    console.error('[EMERGENCY] Could not find monetization ad overlay');
                                }
                            }, 5000);
                        } else {
                            console.error('[EMERGENCY] Could not find public service announcement overlay');
                        }
                    } catch (error) {
                        console.error('[EMERGENCY] Error processing scan response:', error);
                    }
                }
            });
        }
        return originalXHRSend.apply(this, arguments);
    };
    
    // Make sure view results button works properly
    setTimeout(function() {
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            viewResultsBtn.addEventListener('click', function() {
                console.log('[EMERGENCY] View Results button clicked');
                
                // Hide all ad overlays
                const adOverlays = document.querySelectorAll('[id^="ad-overlay"]');
                adOverlays.forEach(function(overlay) {
                    overlay.style.display = 'none';
                });
                
                // Show the results container
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.classList.remove('d-none');
                    resultsContainer.style.display = 'block';
                }
                
                // Re-enable scrolling
                document.body.style.overflow = '';
                
                // Process results if they exist
                if (window.lastResultsData && typeof processTicketScanResults === 'function') {
                    processTicketScanResults(window.lastResultsData);
                }
            });
        }
    }, 1000);
});

// Also add a global function that can be called from the console for manual fixes
window.emergencyTriggerFileInput = function() {
    console.log('[EMERGENCY] Manual emergency file input trigger called');
    const fileInput = document.getElementById('ticket-image');
    if (fileInput) {
        // Reset any state trackers
        if (window.fileDialogState) {
            window.fileDialogState.isSelectingFile = false;
            window.fileDialogState.lastDialogTime = 0;
        }
        
        // Try the dispatchEvent method
        try {
            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            fileInput.dispatchEvent(clickEvent);
            return 'Triggered file input via dispatchEvent';
        } catch (error) {
            console.error('[EMERGENCY] Error in manual trigger:', error);
            
            // Fall back to the click method
            try {
                fileInput.click();
                return 'Triggered file input via click method';
            } catch (fallbackError) {
                console.error('[EMERGENCY] Fallback also failed:', fallbackError);
                return 'Failed to trigger file input: ' + fallbackError.message;
            }
        }
    } else {
        return 'Could not find file input element (ticket-image)';
    }
};