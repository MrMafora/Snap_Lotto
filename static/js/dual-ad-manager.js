/**
 * Dual Advertisement Manager
 * 
 * Implements a streamlined two-tier advertisement system:
 * 1. Public Service Announcement (5 seconds)
 * 2. Monetization Advertisement (15 seconds)
 * 
 * This is a simplified implementation that follows the original design intent
 * and eliminates overlapping or conflicting advertisement systems.
 */

(function() {
    'use strict';

    // Configuration
    const config = {
        publicServiceAdDuration: 5,  // First ad (PSA) duration in seconds (exactly 5 seconds)
        monetizationAdDuration: 15,  // Second ad (monetization) duration in seconds (minimum 15 seconds)
        updateInterval: 1000,        // Update interval in milliseconds
        debug: true                  // Enable debug logging
    };

    // State tracking
    let state = {
        publicServiceAdActive: false,
        publicServiceAdComplete: false,
        publicServiceAdStartTime: null,
        
        monetizationAdActive: false,
        monetizationAdComplete: false,
        monetizationAdStartTime: null,
        
        viewResultsEnabled: false,
        adSequenceComplete: false,
        
        // Timers
        publicServiceCountdownTimer: null,
        monetizationCountdownTimer: null
    };

    // DOM Elements (will be initialized when DOM is ready)
    let elements = {
        // Overlay containers
        publicServiceAdOverlay: null,
        monetizationAdOverlay: null,
        
        // Ad containers
        publicServiceAdContainer: null,
        monetizationAdContainer: null,
        
        // Countdown elements
        publicServiceCountdown: null,
        monetizationCountdown: null,
        
        // Button elements
        viewResultsButton: null,
        viewResultsButtonContainer: null,
        
        // Results container
        resultsContainer: null
    };

    // Log messages with timestamp if debug is enabled
    function log(message) {
        if (config.debug) {
            console.log(`[${new Date().toISOString()}] DualAdManager: ${message}`);
        }
    }

    // Initialize when document is ready
    document.addEventListener('DOMContentLoaded', initialize);

    // Main initialization function
    function initialize() {
        log('Initializing dual advertisement manager');
        
        // Initialize DOM elements
        elements.publicServiceAdOverlay = document.getElementById('ad-overlay-loading');
        elements.monetizationAdOverlay = document.getElementById('ad-overlay-results');
        
        elements.publicServiceAdContainer = document.getElementById('ad-container-loader');
        elements.monetizationAdContainer = document.getElementById('ad-container-interstitial');
        
        elements.publicServiceCountdown = document.getElementById('first-countdown');
        elements.monetizationCountdown = document.getElementById('countdown');
        
        elements.viewResultsButton = document.getElementById('view-results-btn');
        elements.viewResultsButtonContainer = document.getElementById('view-results-btn-container');
        
        elements.resultsContainer = document.getElementById('results-container');
        
        // Set up event listeners
        setupEventListeners();
        
        // Expose public methods
        window.DualAdManager = {
            showPublicServiceAd: showPublicServiceAd,
            showMonetizationAd: showMonetizationAd,
            hideAllAds: hideAllAds,
            resetAdState: resetAdState
        };
        
        log('Dual advertisement manager initialized');
    }

    // Set up all event listeners
    function setupEventListeners() {
        // When the ticket form is submitted, we'll show the first ad
        const ticketForm = document.getElementById('ticket-form');
        if (ticketForm) {
            // Remove any existing onsubmit handler, we want to control it entirely
            ticketForm.onsubmit = null;
            
            // Add our event listener as the sole form submission handler
            ticketForm.addEventListener('submit', function(event) {
                // Always prevent the default form submission
                event.preventDefault();
                
                log('Form submission intercepted by DualAdManager');
                
                // Reset ad state before starting a new sequence
                resetAdState();
                
                // Start our ad sequence and handle the form submission
                processTicketWithAds();
                return false;
            });
            
            log('Ticket form submit handler configured');
        }
        
        // Set up the View Results button
        if (elements.viewResultsButton) {
            // Remove existing listeners and add our own by replacing the button
            // This ensures no stale event handlers are present
            const newButton = elements.viewResultsButton.cloneNode(true);
            if (elements.viewResultsButton.parentNode) {
                elements.viewResultsButton.parentNode.replaceChild(newButton, elements.viewResultsButton);
                elements.viewResultsButton = newButton;
                
                // Add the event listener to the fresh button
                elements.viewResultsButton.addEventListener('click', handleViewResultsClick);
                log('View Results button event handler attached');
            }
        }
    }
    
    // Separate handler function for the View Results button click
    function handleViewResultsClick(event) {
        event.preventDefault();
        
        // Check if the button is currently disabled or not enabled by state
        if (this.disabled || !state.viewResultsEnabled) {
            log('View Results button clicked while disabled or not enabled, ignoring');
            return false;
        }
        
        log('View Results button clicked, preparing to show results');
        
        // Force enable button in case it's still disabled despite state saying it should be enabled
        this.disabled = false;
        
        // Hide all ad overlays immediately
        hideAllAds();
        
        // Set global flags for compatibility with other code
        window.inResultsMode = true;
        window.adClosed = true;
        window.viewResultsBtnClicked = true;
        window.resultsDisplayed = true;
        
        // Set state
        state.adSequenceComplete = true;
        
        // Show results container with slight delay to ensure overlays are hidden
        setTimeout(function() {
            if (elements.resultsContainer) {
                elements.resultsContainer.classList.remove('d-none');
                elements.resultsContainer.style.display = 'block';
                log('Results container displayed');
            } else {
                log('ERROR: Results container not found!');
            }
        }, 100);
        
        return false;
    }

    // Show the first ad (Public Service Announcement)
    function showPublicServiceAd(callback) {
        log('Showing public service announcement ad');
        
        // Reset state for this ad
        state.publicServiceAdActive = true;
        state.publicServiceAdComplete = false;
        state.publicServiceAdStartTime = Date.now();
        
        // Show the overlay
        if (elements.publicServiceAdOverlay) {
            elements.publicServiceAdOverlay.style.display = 'flex';
            log('Public service announcement overlay displayed');
        } else {
            log('ERROR: Public service announcement overlay element not found');
        }
        
        // Only create countdown if it doesn't already exist
        if (!document.getElementById('first-countdown-container')) {
            // Create a dynamic countdown element
            let countdownContainer = document.createElement('div');
            countdownContainer.id = 'first-countdown-container';
            countdownContainer.className = 'text-center mt-3 mb-2';
            countdownContainer.style.fontWeight = 'bold';
            countdownContainer.style.color = '#495057';
            countdownContainer.style.backgroundColor = '#f8f9fa';
            countdownContainer.style.padding = '8px';
            countdownContainer.style.borderRadius = '5px';
            countdownContainer.style.maxWidth = '350px';
            countdownContainer.style.marginLeft = 'auto';
            countdownContainer.style.marginRight = 'auto';
            
            let countdownText = document.createElement('span');
            countdownText.id = 'first-countdown';
            countdownText.textContent = config.publicServiceAdDuration;
            
            countdownContainer.innerHTML = 'Please wait ';
            countdownContainer.appendChild(countdownText);
            countdownContainer.innerHTML += ' seconds';
            
            // Find the container to append this countdown
            const appendContainer = elements.publicServiceAdOverlay.querySelector('.mt-3');
            if (appendContainer) {
                appendContainer.appendChild(countdownContainer);
            }
        }
        
        // Always make sure we have a reference to the countdown element
        elements.publicServiceCountdown = document.getElementById('first-countdown');
        
        // Start the countdown
        startPublicServiceCountdown(function() {
            // When countdown completes
            completePublicServiceAd();
            
            // Call the callback if provided
            if (callback && typeof callback === 'function') {
                callback();
            }
        });
    }

    // Start countdown for the public service announcement
    function startPublicServiceCountdown(callback) {
        // Clear any existing timer
        if (state.publicServiceCountdownTimer) {
            clearInterval(state.publicServiceCountdownTimer);
        }
        
        // Start with the full countdown time
        let secondsLeft = config.publicServiceAdDuration;
        if (elements.publicServiceCountdown) {
            elements.publicServiceCountdown.textContent = secondsLeft;
        }
        
        log(`Starting public service announcement countdown: ${secondsLeft} seconds`);
        
        // Start countdown timer
        state.publicServiceCountdownTimer = setInterval(function() {
            secondsLeft--;
            
            // Update the countdown display
            if (elements.publicServiceCountdown) {
                elements.publicServiceCountdown.textContent = secondsLeft;
            }
            
            // If countdown is complete
            if (secondsLeft <= 0) {
                // Clear the timer
                clearInterval(state.publicServiceCountdownTimer);
                state.publicServiceCountdownTimer = null;
                
                log('Public service announcement countdown complete');
                
                // Call the callback immediately to prevent delays
                if (callback && typeof callback === 'function') {
                    callback();
                }
            }
        }, config.updateInterval);
    }

    // Mark the public service announcement as complete
    function completePublicServiceAd() {
        log('Completing public service announcement ad');
        
        // Update state
        state.publicServiceAdActive = false;
        state.publicServiceAdComplete = true;
        
        // IMPORTANT: Always show the second ad immediately after the first completes
        // This eliminates any gap between advertisements
        log('Transitioning directly to monetization ad');
        showMonetizationAd();
        
        // We'll handle the results later when they're available
        // The monetization ad will be visible during the entire processing time
    }

    // CRITICAL FIX: Function to kill all timers to prevent ad flashing
    function clearAllTimers() {
        log('Clearing all advertisement timers to prevent flashing/conflicts');
        
        // Clear our specific timers first
        if (state.publicServiceCountdownTimer) {
            clearInterval(state.publicServiceCountdownTimer);
            state.publicServiceCountdownTimer = null;
            log('Cleared public service countdown timer');
        }
        
        if (state.monetizationCountdownTimer) {
            clearInterval(state.monetizationCountdownTimer);
            state.monetizationCountdownTimer = null;
            log('Cleared monetization countdown timer');
        }
        
        // Clear any animation timers we might be storing
        if (window.adTransitionTimer) {
            clearTimeout(window.adTransitionTimer);
            window.adTransitionTimer = null;
            log('Cleared ad transition timer');
        }
        
        // Force all ad overlays to have clean CSS
        document.querySelectorAll('[id^="ad-overlay"]').forEach(overlay => {
            overlay.style.transition = '';
            log('Reset transition style on overlay: ' + overlay.id);
        });
    }

    // Show the second ad (Monetization Advertisement)
    function showMonetizationAd(callback) {
        log('Showing monetization ad with enhanced reliability');
        
        // CRITICAL FIX: First clear all timers to prevent interference
        clearAllTimers();
        
        // Reset state for this ad
        state.monetizationAdActive = true;
        state.monetizationAdComplete = false;
        state.monetizationAdStartTime = Date.now();
        state.viewResultsEnabled = false;
        
        // First make sure the second ad is ready to display
        if (elements.monetizationAdOverlay) {
            // Prepare the ad but don't display it yet 
            elements.monetizationAdOverlay.style.opacity = '0';
            elements.monetizationAdOverlay.style.display = 'flex';
            
            // Make sure button is properly set up initially - grey without lock icon
            if (elements.viewResultsButton) {
                // CRITICAL FIX: Make absolute sure the button attributes are properly set
                elements.viewResultsButton.disabled = true;
                elements.viewResultsButton.removeAttribute('data-has-direct-handler'); // Will be re-added by view-results-direct.js
                elements.viewResultsButton.classList.remove('btn-success', 'btn-pulse', 'btn-pulse-subtle', 'btn-glow');
                elements.viewResultsButton.classList.add('btn-secondary');
                elements.viewResultsButton.innerHTML = `Continue to Results (Wait ${config.monetizationAdDuration}s)`;
                log('Reset View Results button to initial state');
            }
            
            // Show button container but with button disabled
            if (elements.viewResultsButtonContainer) {
                elements.viewResultsButtonContainer.style.display = 'block';
            }
        }
        
        // Store the transition timer globally so we can cancel it if needed
        window.adTransitionTimer = setTimeout(function() {
            // Hide first ad completely first, so there's no possibility of overlap
            if (elements.publicServiceAdOverlay) {
                elements.publicServiceAdOverlay.style.transition = '';
                elements.publicServiceAdOverlay.style.display = 'none';
                log('First ad hidden (clean transition)');
            }
            
            // CRITICAL FIX: Small pause before showing second ad to avoid visual overlap
            setTimeout(function() {
                // Show second ad with clean display approach
                if (elements.monetizationAdOverlay) {
                    // Use a fresh, clean transition
                    elements.monetizationAdOverlay.style.transition = 'opacity 0.3s ease';
                    elements.monetizationAdOverlay.style.opacity = '1';
                    log('Monetization ad overlay displayed (clean transition)');
                    
                    // Start the countdown after ensuring smooth transition
                    startMonetizationCountdown(function() {
                        // When countdown completes
                        completeMonetizationAd();
                        
                        // Call the callback if provided
                        if (callback && typeof callback === 'function') {
                            callback();
                        }
                    });
                } else {
                    log('ERROR: Monetization ad overlay element not found');
                }
            }, 100); // Brief pause for clean sequence
        }, 100); // Very brief initial timer
    }

    // Start countdown for the monetization advertisement
    function startMonetizationCountdown(callback) {
        // Clear any existing timer to ensure we don't have multiple countdowns
        if (state.monetizationCountdownTimer) {
            clearInterval(state.monetizationCountdownTimer);
        }
        
        // Start with the full countdown time
        let secondsLeft = config.monetizationAdDuration;
        
        // Update the SINGLE countdown display
        if (elements.monetizationCountdown) {
            elements.monetizationCountdown.textContent = secondsLeft;
        }
        
        log(`Starting monetization ad countdown: ${secondsLeft} seconds`);
        
        // Make sure button starts in properly disabled state with no lock icon
        if (elements.viewResultsButton) {
            // Set disabled state
            elements.viewResultsButton.disabled = true;
            
            // Remove any existing styling classes
            elements.viewResultsButton.classList.remove(
                'btn-success', 'btn-pulse', 'btn-pulse-subtle', 'btn-glow'
            );
            
            // Add disabled appearance
            elements.viewResultsButton.classList.add('btn-secondary');
            
            // Set initial button text - NO lock icon, just text with timer
            elements.viewResultsButton.innerHTML = `Continue to Results (Wait ${secondsLeft}s)`;
        }
        
        // Show button container
        if (elements.viewResultsButtonContainer) {
            elements.viewResultsButtonContainer.style.display = 'block';
        }
        
        // Start countdown timer
        state.monetizationCountdownTimer = setInterval(function() {
            secondsLeft--;
            
            // Always synchronize the countdown display
            if (elements.monetizationCountdown) {
                elements.monetizationCountdown.textContent = secondsLeft;
            }
            
            // Keep button text clean and consistent - no countdown in the button text
            if (elements.viewResultsButton && secondsLeft > 0) {
                // Just show 'Continue to Results' without the wait time
                elements.viewResultsButton.innerHTML = 'Continue to Results';
            }
            
            // Start visual transition during the last 3 seconds
            if (secondsLeft <= 3 && secondsLeft > 0 && elements.viewResultsButton) {
                // Add a subtle pulse effect as we get closer to enabling the button
                elements.viewResultsButton.classList.add('btn-pulse-subtle');
            }
            
            // If countdown is complete
            if (secondsLeft <= 0) {
                // Clear the timer
                clearInterval(state.monetizationCountdownTimer);
                state.monetizationCountdownTimer = null;
                
                log('Monetization ad countdown complete');
                
                // Update state
                state.viewResultsEnabled = true;
                
                // Hide the countdown container once it reaches zero
                if (document.getElementById('countdown-container')) {
                    document.getElementById('countdown-container').style.display = 'none';
                }
                
                // ENHANCED: Multiple approaches to ensure button is enabled
                if (elements.viewResultsButton) {
                    // First, aggressively remove all classes that might interfere
                    elements.viewResultsButton.classList.remove(
                        'btn-secondary', 'btn-pulse-subtle', 'disabled'
                    );
                    
                    // Force the button to be enabled using multiple approaches
                    elements.viewResultsButton.disabled = false;
                    elements.viewResultsButton.removeAttribute('disabled');
                    
                    // Remove any inline styles that might override
                    elements.viewResultsButton.style.pointerEvents = 'auto';
                    elements.viewResultsButton.style.opacity = '1';
                    
                    // First add only success styling (no animation yet)
                    elements.viewResultsButton.classList.add('btn-success');
                    
                    // Update button text - ONLY a checkmark icon and "View Results" text
                    elements.viewResultsButton.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results';
                    
                    log('View Results button FORCEFULLY enabled by countdown');
                    
                    // Log the current state of the button for debugging
                    log(`Button state check: disabled=${elements.viewResultsButton.disabled}, classList=${elements.viewResultsButton.className}`);
                    
                    // Force a second update to add animations after a small delay
                    // This creates a cleaner visual transition from disabled to enabled
                    setTimeout(function() {
                        if (elements.viewResultsButton) {
                            // Double-check disabled state is false and add event listener
                            elements.viewResultsButton.disabled = false;
                            elements.viewResultsButton.removeAttribute('disabled');
                            
                            // Add pulse and glow effects in sequence
                            elements.viewResultsButton.classList.add('btn-pulse');
                            
                            // Force browser to repaint the button
                            elements.viewResultsButton.offsetHeight;
                            
                            // Add glow effect after a tiny delay for better visual effect
                            setTimeout(function() {
                                elements.viewResultsButton.classList.add('btn-glow');
                                
                                // Add a direct click handler as backup
                                elements.viewResultsButton.addEventListener('click', function clickHandler(e) {
                                    log('Direct click handler engaged');
                                    hideAllAds();
                                    // Remove this event listener after first use
                                    elements.viewResultsButton.removeEventListener('click', clickHandler);
                                });
                            }, 200);
                        }
                    }, 50);
                }
                
                // Call the callback
                if (callback && typeof callback === 'function') {
                    callback();
                }
            }
        }, config.updateInterval);
    }

    // Mark the monetization advertisement as complete
    function completeMonetizationAd() {
        log('Completing monetization ad');
        
        // Update state
        state.monetizationAdActive = false;
        state.monetizationAdComplete = true;
        state.viewResultsEnabled = true;
        
        // Hide the countdown container completely
        if (document.getElementById('countdown-container')) {
            document.getElementById('countdown-container').style.display = 'none';
        }
        
        // Enable the View Results button with proper styling
        if (elements.viewResultsButton) {
            // Ensure button is enabled
            elements.viewResultsButton.disabled = false;
            
            // Remove disabled appearance
            elements.viewResultsButton.classList.remove('btn-secondary', 'btn-pulse-subtle');
            
            // Add active/enabled styling
            elements.viewResultsButton.classList.add('btn-success', 'btn-pulse', 'btn-glow');
            
            // Set final button text - only checkmark icon and "View Results" text
            elements.viewResultsButton.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results';
            
            log('View Results button enabled');
        }
    }

    // Hide all advertisement overlays
    function hideAllAds() {
        log('Hiding all ad overlays');
        
        // Hide first ad overlay
        if (elements.publicServiceAdOverlay) {
            elements.publicServiceAdOverlay.style.display = 'none';
        }
        
        // Hide second ad overlay
        if (elements.monetizationAdOverlay) {
            elements.monetizationAdOverlay.style.display = 'none';
        }
        
        // Clear all timers
        if (state.publicServiceCountdownTimer) {
            clearInterval(state.publicServiceCountdownTimer);
            state.publicServiceCountdownTimer = null;
        }
        
        if (state.monetizationCountdownTimer) {
            clearInterval(state.monetizationCountdownTimer);
            state.monetizationCountdownTimer = null;
        }
    }

    // Reset all ad state
    function resetAdState() {
        log('Resetting ad state');
        
        // Hide all ads
        hideAllAds();
        
        // Reset state object
        state.publicServiceAdActive = false;
        state.publicServiceAdComplete = false;
        state.publicServiceAdStartTime = null;
        
        state.monetizationAdActive = false;
        state.monetizationAdComplete = false;
        state.monetizationAdStartTime = null;
        
        state.viewResultsEnabled = false;
        state.adSequenceComplete = false;
        
        // Reset countdown displays
        if (elements.publicServiceCountdown) {
            elements.publicServiceCountdown.textContent = config.publicServiceAdDuration;
        }
        
        if (elements.monetizationCountdown) {
            elements.monetizationCountdown.textContent = config.monetizationAdDuration;
        }
        
        // Show the countdown container and ensure it's visible
        if (document.getElementById('countdown-container')) {
            document.getElementById('countdown-container').style.display = 'block';
        }
        
        // Reset CSS transitions
        if (elements.publicServiceAdOverlay) {
            elements.publicServiceAdOverlay.style.transition = '';
            elements.publicServiceAdOverlay.style.opacity = '1';
        }
        
        if (elements.monetizationAdOverlay) {
            elements.monetizationAdOverlay.style.transition = '';
            elements.monetizationAdOverlay.style.opacity = '1';
        }
        
        // Reset button state completely
        if (elements.viewResultsButton) {
            // Reset all button properties
            elements.viewResultsButton.disabled = true;
            
            // Remove all possible classes
            elements.viewResultsButton.classList.remove(
                'btn-success', 'btn-pulse', 'btn-pulse-subtle', 
                'btn-glow', 'btn-primary'
            );
            
            // Add only the initial classes
            elements.viewResultsButton.classList.add('btn-secondary');
            
            // Reset button text to initial state - simple text, no icons
            elements.viewResultsButton.innerHTML = 'Continue to Results';
        }
        
        // Hide button container
        if (elements.viewResultsButtonContainer) {
            elements.viewResultsButtonContainer.style.display = 'none';
        }
        
        // Reset global flags for compatibility with other code
        window.inResultsMode = false;
        window.adClosed = false;
        window.viewResultsBtnClicked = false;
        window.resultsDisplayed = false;
    }

    // Default ticket processing function (used if no other handler exists)
    function processTicketWithAds() {
        log('Processing ticket with ads');
        
        // Show first ad (Public Service Announcement)
        showPublicServiceAd();
        
        // Process the ticket after a small delay to ensure ad is visible
        setTimeout(function() {
            // Process the form directly
            const form = document.getElementById('ticket-form');
            if (form) {
                // Create FormData from form
                const formData = new FormData(form);
                
                // DEBUG: Log the file input and formData values
                const fileInput = document.getElementById('ticket-image');
                console.log('DEBUG: File input value:', fileInput ? fileInput.value : 'not found');
                console.log('DEBUG: File input files:', fileInput && fileInput.files ? fileInput.files.length : 'no files');
                
                // Ensuring file data is included
                // First check if we have a file from the unified handler
                if (window.lastSelectedTicketFile) {
                    // Remove any previous file entries
                    formData.delete('ticket_image');
                    // Add the file from our unified handler
                    formData.append('ticket_image', window.lastSelectedTicketFile);
                    console.log('DEBUG: File from unified handler added to FormData:', window.lastSelectedTicketFile.name);
                }
                // Fallback to regular file input if needed
                else if (fileInput && fileInput.files && fileInput.files.length > 0) {
                    // Remove any previous file entries (just in case)
                    formData.delete('ticket_image');
                    // Re-add the file explicitly
                    formData.append('ticket_image', fileInput.files[0]);
                    console.log('DEBUG: File added to FormData from file input:', fileInput.files[0].name);
                } else {
                    console.error('DEBUG: No file selected, submission will likely fail');
                }
                
                // Log all form data for debugging
                console.log('DEBUG: Form data contents:');
                for (const pair of formData.entries()) {
                    console.log(`DEBUG: ${pair[0]}: ${pair[1] instanceof File ? pair[1].name : pair[1]}`);
                }
                
                // Get CSRF token - critical for Snap Lotto security
                const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
                
                // Create headers with CSRF token
                const headers = {
                    'X-Requested-With': 'XMLHttpRequest'
                };
                
                // Add CSRF token if available
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                    log('CSRF token added to request headers');
                } else {
                    log('WARNING: No CSRF token found!');
                }
                
                fetch(form.action || '/scan-ticket', {
                    method: 'POST',
                    body: formData,
                    headers: headers
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    log('Ticket scan successful, results received');
                    
                    // Store the results globally for later display
                    window.lastResultsData = data;
                    
                    // Check if the first ad is complete
                    if (state.publicServiceAdComplete) {
                        // If first ad is already done, show second ad immediately
                        log('First ad already complete, showing monetization ad now');
                        showMonetizationAd();
                    } else {
                        // Otherwise wait for first ad to complete
                        log('Waiting for public service announcement to complete before showing monetization ad');
                    }
                })
                .catch(error => {
                    console.error('Error scanning ticket:', error);
                    // Hide ads and show error
                    hideAllAds();
                    alert('Error scanning ticket. Please try again.');
                });
            }
        }, 500); // Reduced to 500ms for better responsiveness
    }
})();