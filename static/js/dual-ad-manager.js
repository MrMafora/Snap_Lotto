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
            // We'll add our handler but keep the existing one
            const originalSubmit = ticketForm.onsubmit;
            ticketForm.onsubmit = function(event) {
                // Always prevent the default form submission
                event.preventDefault();
                
                // Reset ad state before starting a new sequence
                resetAdState();
                
                // Call the original handler if it exists
                if (typeof originalSubmit === 'function') {
                    return originalSubmit.call(this, event);
                }
                
                // If no original handler, use our default process
                processTicketWithAds();
                return false;
            };
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
                
                // Call the callback
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
        
        // Only hide the first ad overlay if we're not immediately showing the second one
        // This prevents the flicker/gap between ads
        if (!window.lastResultsData || window.resultsDisplayed) {
            if (elements.publicServiceAdOverlay) {
                elements.publicServiceAdOverlay.style.display = 'none';
            }
        }
        
        // Show the second ad if results are ready
        if (window.lastResultsData && !window.resultsDisplayed) {
            log('Ticket results ready, showing monetization ad');
            showMonetizationAd();
        } else {
            log('Waiting for ticket results before showing monetization ad');
        }
    }

    // Show the second ad (Monetization Advertisement)
    function showMonetizationAd(callback) {
        log('Showing monetization ad');
        
        // Reset state for this ad
        state.monetizationAdActive = true;
        state.monetizationAdComplete = false;
        state.monetizationAdStartTime = Date.now();
        state.viewResultsEnabled = false;
        
        // Hide first ad overlay if it was visible
        // Only hide it after making sure the second ad is ready to be shown
        if (elements.publicServiceAdOverlay && 
            elements.publicServiceAdOverlay.style.display !== 'none') {
            log('First ad was visible, hiding it now before showing second ad');
            elements.publicServiceAdOverlay.style.display = 'none';
        }
        
        // Show the overlay with a small delay for smoother transition
        setTimeout(function() {
            if (elements.monetizationAdOverlay) {
                elements.monetizationAdOverlay.style.display = 'flex';
                log('Monetization ad overlay displayed');
            } else {
                log('ERROR: Monetization ad overlay element not found');
            }
            
            // Make sure button is disabled initially
            if (elements.viewResultsButton) {
                elements.viewResultsButton.disabled = true;
                elements.viewResultsButton.classList.remove('btn-success', 'btn-pulse', 'btn-pulse-subtle');
                elements.viewResultsButton.classList.add('btn-secondary');
                elements.viewResultsButton.innerHTML = `<i class="fas fa-lock me-2"></i> Continue to Results (Wait ${config.monetizationAdDuration}s)`;
            }
            
            // Show button container but with button disabled
            if (elements.viewResultsButtonContainer) {
                elements.viewResultsButtonContainer.style.display = 'block';
            }
            
            // Start the countdown
            startMonetizationCountdown(function() {
                // When countdown completes
                completeMonetizationAd();
                
                // Call the callback if provided
                if (callback && typeof callback === 'function') {
                    callback();
                }
            });
        }, 50); // Short delay for smoother transition
    }

    // Start countdown for the monetization advertisement
    function startMonetizationCountdown(callback) {
        // Clear any existing timer
        if (state.monetizationCountdownTimer) {
            clearInterval(state.monetizationCountdownTimer);
        }
        
        // Start with the full countdown time
        let secondsLeft = config.monetizationAdDuration;
        if (elements.monetizationCountdown) {
            elements.monetizationCountdown.textContent = secondsLeft;
        }
        
        log(`Starting monetization ad countdown: ${secondsLeft} seconds`);
        
        // Make sure button is disabled initially
        if (elements.viewResultsButton) {
            elements.viewResultsButton.disabled = true;
            elements.viewResultsButton.classList.remove('btn-success', 'btn-pulse');
            elements.viewResultsButton.classList.add('btn-secondary');
            elements.viewResultsButton.innerHTML = `<i class="fas fa-lock me-2"></i> Continue to Results (Wait ${secondsLeft}s)`;
        }
        
        // Start countdown timer
        state.monetizationCountdownTimer = setInterval(function() {
            secondsLeft--;
            
            // Update the countdown display
            if (elements.monetizationCountdown) {
                elements.monetizationCountdown.textContent = secondsLeft;
            }
            
            // Update button text
            if (elements.viewResultsButton && secondsLeft > 0) {
                elements.viewResultsButton.innerHTML = `<i class="fas fa-lock me-2"></i> Continue to Results (Wait ${secondsLeft}s)`;
            }
            
            // Start visual transition during the last 3 seconds
            if (secondsLeft <= 3 && secondsLeft > 0 && elements.viewResultsButton) {
                // Add a pulse effect as we get closer to enabling the button
                elements.viewResultsButton.classList.add('btn-pulse-subtle');
            }
            
            // If countdown is complete
            if (secondsLeft <= 0) {
                // Clear the timer
                clearInterval(state.monetizationCountdownTimer);
                state.monetizationCountdownTimer = null;
                
                log('Monetization ad countdown complete');
                
                // Double-check that button is properly enabled
                if (elements.viewResultsButton) {
                    elements.viewResultsButton.disabled = false;
                    elements.viewResultsButton.classList.remove('btn-secondary', 'btn-pulse-subtle');
                    elements.viewResultsButton.classList.add('btn-success', 'btn-pulse');
                    elements.viewResultsButton.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results';
                    log('View Results button enabled by countdown');
                    
                    // Force DOM update to ensure button is enabled
                    setTimeout(function() {
                        if (elements.viewResultsButton) {
                            elements.viewResultsButton.disabled = false;
                        }
                    }, 100);
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
        
        // Enable the View Results button
        if (elements.viewResultsButton) {
            elements.viewResultsButton.disabled = false;
            elements.viewResultsButton.classList.remove('btn-secondary');
            elements.viewResultsButton.classList.add('btn-success', 'btn-pulse');
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
        
        // Reset button state
        if (elements.viewResultsButton) {
            elements.viewResultsButton.disabled = true;
            elements.viewResultsButton.classList.remove('btn-success', 'btn-pulse');
            elements.viewResultsButton.classList.add('btn-secondary');
            elements.viewResultsButton.innerHTML = `<i class="fas fa-lock me-2"></i> Continue to Results (Wait ${config.monetizationAdDuration}s)`;
        }
        
        // Hide button container
        if (elements.viewResultsButtonContainer) {
            elements.viewResultsButtonContainer.style.display = 'none';
        }
        
        // Reset global flags for compatibility
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
                const formData = new FormData(form);
                
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