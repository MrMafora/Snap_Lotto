/**
 * Navigation Advertisement Manager
 * 
 * Implements a single 5-second public service announcement that shows
 * before redirecting to the ticket scanner page.
 * 
 * This separates the PSA from the monetization ad to create a smoother user flow.
 */

(function() {
    'use strict';

    // Configuration
    const config = {
        publicServiceAdDuration: 5,  // PSA duration in seconds (exactly 5 seconds)
        updateInterval: 1000,        // Update interval in milliseconds
        ticketScannerPath: '/ticket-scanner', // Path to redirect after ad
        debug: true                  // Enable debug logging
    };

    // State tracking
    let state = {
        adActive: false,
        adComplete: false,
        adStartTime: null,
        countdownTimer: null,
        destinationUrl: null
    };

    // DOM Elements (will be initialized when DOM is ready)
    let elements = {
        adOverlay: null,
        countdownElement: null
    };

    // Debug logging helper
    function log(message) {
        if (config.debug && console && console.log) {
            console.log(`[NavigationAd] ${message}`);
        }
    }

    // Initialize the ad manager
    function initialize() {
        log('Initializing Navigation Ad Manager');
        
        // Find the overlay element
        elements.adOverlay = document.getElementById('psa-ad-overlay');
        if (!elements.adOverlay) {
            log('WARNING: PSA ad overlay element not found - creating it dynamically');
            createAdOverlay();
        }
        
        // Set up event listeners for scanner links
        setupScannerLinks();
    }

    // Create the ad overlay dynamically if not present in HTML
    function createAdOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'psa-ad-overlay';
        overlay.className = 'psa-ad-overlay';
        overlay.style.display = 'none';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
        overlay.style.zIndex = '9999';
        overlay.style.display = 'none';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.flexDirection = 'column';
        overlay.style.padding = '20px';
        overlay.style.boxSizing = 'border-box';
        overlay.style.color = 'white';
        overlay.style.textAlign = 'center';
        
        // Public service announcement content
        const content = document.createElement('div');
        content.className = 'psa-content';
        content.innerHTML = `
            <h2 style="margin-bottom: 20px; font-size: 24px; color: white;">MISSING CHILDREN ALERT</h2>
            <div style="max-width: 600px; margin: 0 auto;">
                <p style="margin-bottom: 15px; font-size: 16px;">Help us find missing children in South Africa. If you have any information, please contact the South African Police Service immediately.</p>
                <div style="margin: 20px 0;">
                    <img src="/static/img/psa-missing-children.jpg" alt="Missing Children Alert" style="max-width: 100%; height: auto; border-radius: 8px;">
                </div>
                <p>This message is brought to you by Snap Lotto in partnership with Missing Children South Africa.</p>
            </div>
            <div class="countdown-container" style="margin-top: 20px; font-weight: bold;">
                <span>Advertisement: </span>
                <span id="psa-countdown">5</span>
                <span> seconds</span>
            </div>
        `;
        
        overlay.appendChild(content);
        document.body.appendChild(overlay);
        
        elements.adOverlay = overlay;
        elements.countdownElement = document.getElementById('psa-countdown');
    }

    // Set up event listeners for scanner links
    function setupScannerLinks() {
        // Find links to the ticket scanner
        const scannerLinks = document.querySelectorAll('a[href="/ticket-scanner"]');
        
        log(`Found ${scannerLinks.length} scanner links to intercept`);
        
        scannerLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Store the destination URL
                state.destinationUrl = this.getAttribute('href');
                log(`Intercepted click, will redirect to: ${state.destinationUrl}`);
                
                // Show the PSA ad
                showAd();
                
                return false;
            });
        });
    }

    // Show the PSA
    function showAd() {
        log('Showing PSA advertisement');
        
        // Reset state
        state.adActive = true;
        state.adComplete = false;
        state.adStartTime = Date.now();
        
        // Show the overlay
        if (elements.adOverlay) {
            elements.adOverlay.style.display = 'flex';
            log('PSA overlay displayed');
        } else {
            log('ERROR: PSA overlay element not found');
            // Fall back to immediate redirection
            redirectToScanner();
            return;
        }
        
        // Make sure we have the countdown element
        elements.countdownElement = document.getElementById('psa-countdown');
        
        // Start the countdown
        startCountdown(function() {
            // When countdown completes
            completeAd();
        });
    }

    // Start the countdown timer
    function startCountdown(callback) {
        // Clear any existing timer
        if (state.countdownTimer) {
            clearInterval(state.countdownTimer);
        }
        
        // Start with the full countdown time
        let secondsLeft = config.publicServiceAdDuration;
        if (elements.countdownElement) {
            elements.countdownElement.textContent = secondsLeft;
        }
        
        log(`Starting PSA countdown: ${secondsLeft} seconds`);
        
        // Start countdown timer
        state.countdownTimer = setInterval(function() {
            secondsLeft--;
            
            // Update the countdown display
            if (elements.countdownElement) {
                elements.countdownElement.textContent = secondsLeft;
            }
            
            // If countdown is complete
            if (secondsLeft <= 0) {
                // Clear the timer
                clearInterval(state.countdownTimer);
                state.countdownTimer = null;
                
                log('PSA countdown complete');
                
                // Call the callback immediately to prevent delays
                if (callback && typeof callback === 'function') {
                    callback();
                }
            }
        }, config.updateInterval);
    }

    // Mark the ad as complete
    function completeAd() {
        log('Completing PSA advertisement');
        
        // Update state
        state.adActive = false;
        state.adComplete = true;
        
        // Redirect to the scanner page
        redirectToScanner();
    }

    // Redirect to the ticket scanner
    function redirectToScanner() {
        log('Redirecting to ticket scanner');
        
        // Use the stored URL or fallback to the config path
        const destination = state.destinationUrl || config.ticketScannerPath;
        
        // Redirect
        window.location.href = destination;
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(initialize, 1);
    } else {
        document.addEventListener('DOMContentLoaded', initialize);
    }
    
    // Export API for global access
    window.NavigationAdManager = {
        showAd: showAd
    };
})();