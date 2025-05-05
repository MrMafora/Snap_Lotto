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
    function log(message, obj) {
        if (config.debug && console && console.log) {
            if (obj !== undefined) {
                console.log(`[NavigationAd] ${message}`, obj);
            } else {
                console.log(`[NavigationAd] ${message}`);
            }
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
        
        // Public service announcement content with enhanced contact information
        const content = document.createElement('div');
        content.className = 'psa-content';
        content.innerHTML = `
            <h2 style="margin-bottom: 20px; font-size: 24px; color: white;">MISSING CHILDREN ALERT</h2>
            <div style="max-width: 600px; margin: 0 auto;">
                <p style="margin-bottom: 15px; font-size: 16px;">Help us find missing children in South Africa. If you have any information, please contact:</p>
                
                <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px; text-align: left;">
                    <p style="margin-bottom: 10px; font-weight: bold;">Contact Information:</p>
                    <ul style="list-style-type: none; padding-left: 0; margin-bottom: 10px;">
                        <li style="margin-bottom: 5px;"><i class="fas fa-phone-alt" style="width: 20px; text-align: center; margin-right: 8px;"></i> Emergency Hotline: <strong>116 000</strong></li>
                        <li style="margin-bottom: 5px;"><i class="fas fa-phone-alt" style="width: 20px; text-align: center; margin-right: 8px;"></i> SAPS: <strong>08600 10111</strong></li>
                        <li style="margin-bottom: 5px;"><i class="fas fa-envelope" style="width: 20px; text-align: center; margin-right: 8px;"></i> Email: <strong>info@missingchildren.org.za</strong></li>
                    </ul>
                    <p style="margin-bottom: 0;">To report a missing child or submit information about a missing child case, please <a href="/missing-children-form" style="color: #fff; text-decoration: underline; font-weight: bold;">click here</a> to use our secure online form.</p>
                </div>
                
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
        // Find all links that might lead to the ticket scanner
        // This handles both direct "/ticket-scanner" links and Flask's url_for() generated links
        const allLinks = document.querySelectorAll('a');
        const scannerLinks = [];
        
        // Filter links that point to the ticket scanner page
        allLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href) {
                // Check for direct match or URL ending with /ticket-scanner
                // Also check for Flask's url_for generated paths which might include a domain
                if (href === '/ticket-scanner' || 
                    href.endsWith('/ticket-scanner') || 
                    href.includes('/ticket_scanner') ||
                    href.includes('/ticket-scanner')) {
                    scannerLinks.push(link);
                    log(`Found scanner link: ${href}`, link);
                }
            }
        });
        
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
    function initializeWithRetry() {
        initialize();
        
        // Check if we found any links - if not, we'll retry after a short delay
        // This helps with dynamically loaded content or slower page loads
        const links = document.querySelectorAll('a');
        if (links.length > 0) {
            log(`Found ${links.length} total links on page`);
            
            // If we couldn't find any scanner links but we know there should be some,
            // schedule a delayed initialization
            if (document.querySelector('a[href="/ticket-scanner"]') || 
                document.querySelector(`a[href*="ticket_scanner"]`) || 
                document.querySelector(`a[href*="ticket-scanner"]`)) {
                log('Found scanner links in document - scheduling delayed initialization');
                setTimeout(initialize, 500); // Try again after 500ms
            }
        } else {
            log('No links found on page yet - scheduling delayed initialization');
            setTimeout(initialize, 500); // Try again after 500ms
        }
    }
    
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(initializeWithRetry, 1);
    } else {
        document.addEventListener('DOMContentLoaded', initializeWithRetry);
    }
    
    // Also initialize on window load to catch any dynamically added links
    window.addEventListener('load', function() {
        log('Window loaded - running final initialization');
        setTimeout(initialize, 100);
    });
    
    // Export API for global access
    window.NavigationAdManager = {
        showAd: showAd
    };
})();