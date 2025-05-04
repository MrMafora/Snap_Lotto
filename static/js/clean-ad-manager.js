/**
 * Clean Advertisement Manager
 * 
 * A simplified two-tier advertisement system that works with clean-file-uploader.js
 * Maintains the dual advertisement structure:
 * 1. Public Service Announcement (5 seconds)
 * 2. Monetization Advertisement (15 seconds)
 * 
 * With clear separation of responsibilities and no manipulation of form data
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        debug: true,
        publicServiceAdDuration: 5,  // First ad (PSA) duration in seconds
        monetizationAdDuration: 15,  // Second ad (monetization) duration in seconds
        countdownInterval: 1000,     // Update interval in milliseconds
        publicServiceAdOverlayId: 'ad-overlay-loading',
        monetizationAdOverlayId: 'ad-overlay-results',
        publicServiceAdContainerId: 'ad-container-loader',
        monetizationAdContainerId: 'ad-container-interstitial',
        publicServiceCountdownId: 'first-countdown',
        monetizationCountdownId: 'countdown',
        viewResultsBtnId: 'view-results-btn',
        viewResultsBtnContainerId: 'view-results-btn-container',
        resultsContainerId: 'results-container'
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
        monetizationCountdownTimer: null,
        allTimers: []
    };

    // Element references
    let elements = {};

    // Debug logging
    function log(message, data) {
        if (CONFIG.debug) {
            const timestamp = new Date().toISOString();
            if (data !== undefined) {
                console.log(`[${timestamp}] CleanAdManager: ${message}`, data);
            } else {
                console.log(`[${timestamp}] CleanAdManager: ${message}`);
            }
        }
    }

    // Initialize when the DOM is ready
    document.addEventListener('DOMContentLoaded', initialize);

    // Main initialization function
    function initialize() {
        log('Initializing Clean Advertisement Manager');
        
        // Cache all required DOM elements
        cacheElements();
        
        // Set up all event handlers
        setupEventHandlers();
        
        // Make the ad manager functions available globally
        window.CleanAdManager = {
            showPublicServiceAd: showPublicServiceAd,
            showMonetizationAd: showMonetizationAd,
            hideAllAds: hideAllAds,
            resetAdState: resetAdState,
            clearAllTimers: clearAllTimers,
            processWithAds: processWithAds
        };
        
        // Maintain compatibility with old code
        window.DualAdManager = window.CleanAdManager;
        
        log('Clean Advertisement Manager initialized successfully');
    }

    // Cache references to all required DOM elements
    function cacheElements() {
        elements.publicServiceAdOverlay = document.getElementById(CONFIG.publicServiceAdOverlayId);
        elements.monetizationAdOverlay = document.getElementById(CONFIG.monetizationAdOverlayId);
        
        elements.publicServiceAdContainer = document.getElementById(CONFIG.publicServiceAdContainerId);
        elements.monetizationAdContainer = document.getElementById(CONFIG.monetizationAdContainerId);
        
        elements.publicServiceCountdown = document.getElementById(CONFIG.publicServiceCountdownId);
        elements.monetizationCountdown = document.getElementById(CONFIG.monetizationCountdownId);
        
        elements.viewResultsBtn = document.getElementById(CONFIG.viewResultsBtnId);
        elements.viewResultsBtnContainer = document.getElementById(CONFIG.viewResultsBtnContainerId);
        
        elements.resultsContainer = document.getElementById(CONFIG.resultsContainerId);
        
        log('Elements cached');
    }

    // Set up all event handlers
    function setupEventHandlers() {
        // Handle view results button click
        if (elements.viewResultsBtn) {
            // Create a fresh button to avoid conflicting event handlers
            const newButton = elements.viewResultsBtn.cloneNode(true);
            if (elements.viewResultsBtn.parentNode) {
                elements.viewResultsBtn.parentNode.replaceChild(newButton, elements.viewResultsBtn);
                elements.viewResultsBtn = newButton;
                
                newButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    log('View Results button clicked');
                    
                    // Check if the button is currently enabled by state
                    if (!state.viewResultsEnabled) {
                        log('View Results button clicked while disabled, ignoring');
                        return false;
                    }
                    
                    // Hide all ads
                    hideAllAds();
                    
                    // Display results
                    if (typeof window.showTicketResults === 'function') {
                        window.showTicketResults();
                    } else {
                        log('No showTicketResults function available');
                        if (elements.resultsContainer && window.lastResultsData) {
                            // Fallback display
                            elements.resultsContainer.innerHTML = '<pre>' + JSON.stringify(window.lastResultsData, null, 2) + '</pre>';
                            elements.resultsContainer.style.display = 'block';
                        }
                    }
                    
                    return false;
                });
                
                log('View Results button handler attached');
            }
        }
    }

    // Clear a single timer and remove it from tracking
    function clearTimer(timer) {
        if (timer) {
            clearTimeout(timer);
            clearInterval(timer);
            const index = state.allTimers.indexOf(timer);
            if (index !== -1) {
                state.allTimers.splice(index, 1);
            }
        }
    }

    // Clear all tracked timers
    function clearAllTimers() {
        log('Clearing all timers');
        
        // Clear specific named timers
        clearTimer(state.publicServiceCountdownTimer);
        state.publicServiceCountdownTimer = null;
        
        clearTimer(state.monetizationCountdownTimer);
        state.monetizationCountdownTimer = null;
        
        // Clear all tracked timers
        state.allTimers.forEach(timer => {
            clearTimeout(timer);
            clearInterval(timer);
        });
        state.allTimers = [];
    }

    // Track a timer for later cleanup
    function trackTimer(timer) {
        if (timer) {
            state.allTimers.push(timer);
        }
        return timer;
    }

    // Show the public service announcement ad
    function showPublicServiceAd() {
        log('Showing public service announcement ad');
        
        // Reset state for this ad
        state.publicServiceAdActive = true;
        state.publicServiceAdComplete = false;
        state.publicServiceAdStartTime = Date.now();
        
        // Clear any existing countdown timers
        clearAllTimers();
        
        // Show the public service ad overlay
        if (elements.publicServiceAdOverlay) {
            elements.publicServiceAdOverlay.style.display = 'flex';
        }
        
        // Hide the monetization ad overlay
        if (elements.monetizationAdOverlay) {
            elements.monetizationAdOverlay.style.display = 'none';
        }
        
        // Start the countdown
        startPublicServiceCountdown();
        
        // Schedule auto-transition to monetization ad
        const transitionTimer = setTimeout(() => {
            log('Public service announcement period completed');
            
            state.publicServiceAdComplete = true;
            state.publicServiceAdActive = false;
            
            // If we already have results data, proceed to show monetization ad
            // This handles cases where the API responds very quickly
            if (window.lastResultsData) {
                showMonetizationAd();
            }
            // Otherwise the monetization ad will be shown when results arrive
            
        }, CONFIG.publicServiceAdDuration * 1000);
        
        trackTimer(transitionTimer);
    }

    // Start the countdown for the public service ad
    function startPublicServiceCountdown() {
        // Only start if we have countdown element
        if (!elements.publicServiceCountdown) {
            return;
        }
        
        let remainingSeconds = CONFIG.publicServiceAdDuration;
        elements.publicServiceCountdown.textContent = remainingSeconds;
        
        state.publicServiceCountdownTimer = trackTimer(setInterval(() => {
            remainingSeconds--;
            
            if (remainingSeconds <= 0) {
                clearTimer(state.publicServiceCountdownTimer);
                state.publicServiceCountdownTimer = null;
                elements.publicServiceCountdown.textContent = '0';
            } else {
                elements.publicServiceCountdown.textContent = remainingSeconds;
            }
        }, CONFIG.countdownInterval));
    }

    // Show the monetization ad
    function showMonetizationAd() {
        log('Showing monetization ad');
        
        // Reset state for this ad
        state.monetizationAdActive = true;
        state.monetizationAdComplete = false;
        state.monetizationAdStartTime = Date.now();
        state.viewResultsEnabled = false;
        
        // Clear any existing countdown timers
        if (state.monetizationCountdownTimer) {
            clearTimer(state.monetizationCountdownTimer);
            state.monetizationCountdownTimer = null;
        }
        
        // Hide the public service ad overlay
        if (elements.publicServiceAdOverlay) {
            elements.publicServiceAdOverlay.style.display = 'none';
        }
        
        // Show the monetization ad overlay
        if (elements.monetizationAdOverlay) {
            elements.monetizationAdOverlay.style.display = 'flex';
        }
        
        // Disable View Results button initially
        if (elements.viewResultsBtn) {
            elements.viewResultsBtn.disabled = true;
        }
        
        // Start the countdown
        startMonetizationCountdown();
    }

    // Start the countdown for the monetization ad
    function startMonetizationCountdown() {
        // Only start if we have countdown element
        if (!elements.monetizationCountdown) {
            return;
        }
        
        let remainingSeconds = CONFIG.monetizationAdDuration;
        elements.monetizationCountdown.textContent = remainingSeconds;
        
        state.monetizationCountdownTimer = trackTimer(setInterval(() => {
            remainingSeconds--;
            
            if (remainingSeconds <= 0) {
                clearTimer(state.monetizationCountdownTimer);
                state.monetizationCountdownTimer = null;
                elements.monetizationCountdown.textContent = '0';
                
                // Enable the View Results button after countdown completes
                enableViewResultsButton();
            } else {
                elements.monetizationCountdown.textContent = remainingSeconds;
            }
        }, CONFIG.countdownInterval));
        
        // Schedule enabling of View Results button (backup safety measure)
        const enableTimer = setTimeout(() => {
            enableViewResultsButton();
        }, CONFIG.monetizationAdDuration * 1000);
        
        trackTimer(enableTimer);
    }

    // Enable the View Results button
    function enableViewResultsButton() {
        if (!state.viewResultsEnabled) {
            log('Enabling View Results button');
            
            state.viewResultsEnabled = true;
            state.monetizationAdComplete = true;
            state.adSequenceComplete = true;
            
            if (elements.viewResultsBtn) {
                elements.viewResultsBtn.disabled = false;
                
                // Add pulse animation to draw attention
                elements.viewResultsBtn.classList.add('btn-pulse');
                
                log('View Results button enabled and pulsing');
            }
            
            if (elements.viewResultsBtnContainer) {
                elements.viewResultsBtnContainer.style.display = 'block';
            }
        }
    }

    // Hide all ad overlays
    function hideAllAds() {
        log('Hiding all ad overlays');
        
        // Clear all timers
        clearAllTimers();
        
        // Hide ad overlays
        if (elements.publicServiceAdOverlay) {
            elements.publicServiceAdOverlay.style.display = 'none';
        }
        
        if (elements.monetizationAdOverlay) {
            elements.monetizationAdOverlay.style.display = 'none';
        }
        
        // Reset state
        resetAdState();
    }

    // Reset the ad state
    function resetAdState() {
        log('Resetting ad state');
        
        state.publicServiceAdActive = false;
        state.publicServiceAdComplete = false;
        state.publicServiceAdStartTime = null;
        
        state.monetizationAdActive = false;
        state.monetizationAdComplete = false;
        state.monetizationAdStartTime = null;
        
        state.viewResultsEnabled = false;
        state.adSequenceComplete = false;
    }

    // Main processing function - integrates with CleanFileUploader
    function processWithAds() {
        log('Processing with ads');
        
        // First show the public service ad
        showPublicServiceAd();
        
        // Then trigger the file processing via CleanFileUploader
        // This maintains separation of concerns - the ad manager doesn't handle files
        setTimeout(() => {
            if (window.CleanFileUploader?.beginImageProcessing) {
                const success = window.CleanFileUploader.beginImageProcessing();
                if (!success) {
                    log('ERROR: CleanFileUploader could not begin image processing');
                    // Clean up ad display
                    setTimeout(() => hideAllAds(), 1000);
                }
            } else {
                log('ERROR: CleanFileUploader not available');
                hideAllAds();
            }
        }, 100);
    }
})();