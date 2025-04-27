/**
 * Advertisement Management for Snap Lotto
 * Handles displaying video ads at strategic points during the ticket scanning process
 * 
 * Features:
 * - Loads custom video advertisements from the database
 * - Tracks impressions and clicks
 * - Supports multiple ad placements (scanner, results, homepage)
 * - Supports timed display with countdown
 */

// Global ad manager object 
// Using window.AdManager instead of const AdManager to avoid duplicate declarations
window.AdManager = window.AdManager || {
    // Current ads loaded from server
    ads: {
        scanner: null,
        results: null,
        homepage: null
    },
    
    // Current active impression
    currentImpression: null,
    
    // Queue for ads to show
    adQueue: [],
    
    // Note: init() is called at the end of this file
    init: function() {
        console.log('AdManager initialized from ads.js');
        
        // Check if we're in development mode
        const isDevelopment = !document.querySelector('meta[name="ad-server"]');
        
        if (isDevelopment) {
            console.log('Development mode detected, using mock ads');
            // Pre-create mock ads for immediate display
            this.createMockAd('ad-container-loader');
            this.createMockAd('ad-container-interstitial');
        } else {
            console.log('Production mode detected, fetching available ads');
            // Production mode - fetch ads from API
            this.fetchAvailableAds();
        }
        
        // Listen for ad click events
        document.addEventListener('click', function(e) {
            const adElement = e.target.closest('.ad-container');
            if (adElement && AdManager.currentImpression) {
                AdManager.recordAdClick(AdManager.currentImpression);
            }
        });
    },
    
    // Create a visible mock ad for testing
    createMockAd: function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Mock ad container ${containerId} not found`);
            // Try to create the container if it doesn't exist
            const createdContainer = this.ensureContainerExists(containerId);
            if (!createdContainer) {
                return; // Still couldn't create it
            }
        }
        
        try {
            // Get the container again in case it was just created
            const targetContainer = document.getElementById(containerId);
            if (!targetContainer) return;
            
            // Check if the container already has content from the template
            if (targetContainer.children.length > 0) {
                console.log(`Container ${containerId} already has content, using existing ad`);
                return;
            }
            
            // Determine if this is the first ad (processing) or second ad (results)
            const isFirstAd = containerId === 'ad-container-loader';
            
            // Create a visual placeholder exactly matching the screenshots
            if (isFirstAd) {
                // First ad (yellow badge for Processing)
                targetContainer.innerHTML = `
                    <div style="width: 100%; background-color: #f3f3f3; border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 30px 15px; text-align: center;">
                        <div style="margin-bottom: 15px;">
                            <span style="background-color: #ffde00; color: #000; font-weight: bold; padding: 3px 10px; border-radius: 4px; font-size: 14px;">Ad</span>
                        </div>
                        <div style="font-size: 16px; color: #6c757d; margin-bottom: 15px; width: 100%; text-align: center;">
                            Advertisement
                        </div>
                        <div style="color: #6c757d; font-size: 14px; text-align: center; width: 100%; margin-top: 10px;">
                            To advertise here please contact us on:<br>+27 (61) 544-8311
                        </div>
                    </div>
                `;
            } else {
                // Second ad (blue badge for Results Ready)
                targetContainer.innerHTML = `
                    <div style="width: 100%; background-color: #f3f3f3; border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 30px 15px; text-align: center;">
                        <div style="margin-bottom: 15px;">
                            <span style="background-color: #0d6efd; color: #fff; font-weight: bold; padding: 3px 10px; border-radius: 4px; font-size: 14px;">Ad</span>
                        </div>
                        <div style="font-size: 16px; color: #6c757d; margin-bottom: 10px; width: 100%; text-align: center;">
                            Advertisement
                        </div>
                        <div style="color: #6c757d; font-size: 14px; text-align: center; width: 100%; margin-bottom: 10px;">
                            Your results are ready to view below
                        </div>
                        <div style="color: #6c757d; font-size: 14px; text-align: center; width: 100%;">
                            To advertise here please contact us on:<br>+27 (61) 544-8311
                        </div>
                    </div>
                `;
            }
            
            console.log(`Mock ad created in ${containerId}`);
        } catch (e) {
            console.warn(`Failed to create mock ad in ${containerId}:`, e);
        }
    },
    
    ensureContainerExists: function(containerId) {
        // Check if we're dealing with loader or interstitial
        const isLoader = containerId === 'ad-container-loader';
        const isInterstitial = containerId === 'ad-container-interstitial';
        
        if (!isLoader && !isInterstitial) return false;
        
        const overlayId = isLoader ? 'ad-overlay-loading' : 'ad-overlay-results';
        const overlay = document.getElementById(overlayId);
        
        if (!overlay) return false;
        
        // Find or create the ad container
        let adContainer = overlay.querySelector('.ad-container');
        if (!adContainer) {
            adContainer = document.createElement('div');
            adContainer.className = 'ad-container';
            adContainer.style.cssText = 'margin: 0 auto; background-color: #f8f9fa; border-radius: 10px; padding: 20px; max-width: 350px;';
            // Use safe append method
            try {
                overlay.appendChild(adContainer);
            } catch (e) {
                console.warn('Failed to append ad container to overlay:', e);
                return false;
            }
        }
        
        // Create the container with proper ID
        const container = document.createElement('div');
        container.id = containerId;
        container.style.cssText = 'width: 300px; margin: 0 auto;';
        
        try {
            adContainer.appendChild(container);
            return true;
        } catch (e) {
            console.warn(`Failed to create ${containerId}:`, e);
            return false;
        }
    },

    // Load and display an ad in the specified container
    loadAd: function(containerId, callback) {
        try {
            const container = document.getElementById(containerId);
            if (!container) {
                console.error(`Ad container ${containerId} not found`);
                // Try to create container if missing
                const created = this.ensureContainerExists(containerId);
                if (!created) {
                    if (callback) callback(false);
                    return;
                }
            }
            
            try {
                // Get fresh reference to container (in case it was just created)
                const targetContainer = document.getElementById(containerId);
                if (!targetContainer) {
                    if (callback) callback(false);
                    return;
                }
                
                // Check if the container already has content from the template
                if (targetContainer.children.length > 0) {
                    console.log(`Container ${containerId} already has content, using existing ad`);
                    // Consider the ad loaded immediately
                    if (callback) callback(true);
                    return;
                }
                
                // Create a new ad container
                const adContainer = document.createElement('div');
                adContainer.className = 'ad-container py-3';
                
                // In production, this would use real AdSense code
                // Here, we're creating a placeholder for the ad
                adContainer.innerHTML = `
                    <div class="text-center">
                        <div class="ad-placeholder">
                            <p><i class="fas fa-ad mb-2"></i></p>
                            <p class="mb-0">Advertisement</p>
                        </div>
                    </div>
                `;
                
                targetContainer.appendChild(adContainer);
                
                // Simulate ad loading (would be handled by AdSense in production)
                setTimeout(() => {
                    console.log(`Ad loaded in ${containerId}`);
                    if (callback) callback(true);
                }, 2000); // 2 second delay to simulate ad loading
            } catch (innerError) {
                console.warn(`Error loading ad content into ${containerId}:`, innerError);
                if (callback) callback(false);
            }
        } catch (e) {
            console.error(`Critical error in loadAd for ${containerId}:`, e);
            if (callback) callback(false);
        }
    },

    // Show the loading ad (before scan results are ready)
    showLoadingAd: function(seconds, callback) {
        console.log('AdManager: Showing loading ad');
        
        // If seconds is a function, it's the callback (old usage)
        if (typeof seconds === 'function') {
            callback = seconds;
            seconds = undefined;
        }
        
        // Get the ad for scanner placement to access its loading_duration
        const ad = this.ads['scanner'] || { loading_duration: 10 }; // Default to 10 seconds if no ad found
        
        // Use provided seconds parameter if available, otherwise use ad's loading_duration
        const displaySeconds = seconds || ad.loading_duration;
        const loadingDuration = displaySeconds * 1000; // Convert to milliseconds
        
        console.log(`AdManager: Showing first loading ad for ${displaySeconds} seconds`);
        
        // Use the enhanced showOverlay utility function if available
        if (typeof showOverlay === 'function') {
            if (showOverlay('ad-overlay-loading')) {
                console.log('AdManager: Loading overlay shown via enhanced showOverlay utility');
            } else {
                console.error('AdManager: Enhanced showOverlay failed, falling back to direct manipulation');
                // Fallback to direct DOM manipulation
                const adOverlayLoading = document.getElementById('ad-overlay-loading');
                if (adOverlayLoading) {
                    adOverlayLoading.style.display = 'flex';
                    adOverlayLoading.style.opacity = '1';
                    adOverlayLoading.style.visibility = 'visible';
                    adOverlayLoading.style.zIndex = '2147483647';
                    document.body.style.overflow = 'hidden'; // Prevent scrolling
                    // FIXED: Removed position:fixed that was causing mobile freeze
                    document.body.style.width = '100%'; // Maintain width
                    console.log('AdManager: Loading overlay shown via direct manipulation');
                } else {
                    console.error('AdManager: Loading overlay element not found!');
                }
            }
        } else {
            // Fallback if showOverlay function is not available
            const adOverlayLoading = document.getElementById('ad-overlay-loading');
            if (adOverlayLoading) {
                adOverlayLoading.style.cssText = 'display:flex !important; opacity:1 !important; visibility:visible !important; z-index:2147483647 !important;';
                document.body.style.overflow = 'hidden'; // Prevent scrolling
                // FIXED: Removed position:fixed that was causing mobile freeze
                document.body.style.width = '100%'; // Maintain width
                console.log('AdManager: Loading overlay shown via cssText manipulation');
            } else {
                console.error('AdManager: Loading overlay element not found!');
            }
        }
        
        // Find and update the loading message with the configured duration if available
        const loadingMessage = document.querySelector('#ad-overlay-loading .loading-message');
        if (loadingMessage && ad.custom_message) {
            loadingMessage.textContent = ad.custom_message;
        }
        
        // Load the ad in the container
        this.loadAd('ad-container-loader', callback);
        
        // Automatically hide the loading overlay after the configured duration
        // This ensures the loading overlay is shown for exactly the configured time
        setTimeout(() => {
            // Only auto-hide if it hasn't been closed by the ticket scanning process
            const adOverlayLoading = document.getElementById('ad-overlay-loading');
            if (adOverlayLoading && adOverlayLoading.style.display !== 'none') {
                console.log(`AdManager: Auto-hiding loading overlay after ${displaySeconds} seconds`);
                this.hideLoadingAd();
                // If there was a callback, call it again to ensure the ticket processing continues
                if (callback) callback(true);
            }
        }, loadingDuration);
    },

    // Show the interstitial ad (before showing results)
    showInterstitialAd: function(callback) {
        console.log('AdManager: Showing interstitial ad at ' + new Date().toISOString());
        
        // Set a flag to track that we're showing an ad - this prevents autohide timers
        window.currentlyShowingAd = true;
        window.adStartTime = Date.now();
        
        // Get available ads for scanner placement
        let availableAds = [];
        
        // Try to use getAdsByPlacement helper if available
        if (typeof window.getAdsByPlacement === 'function') {
            availableAds = window.getAdsByPlacement('scanner');
        } else if (this.ads && this.ads.scanner) {
            // Fallback to direct access
            if (Array.isArray(this.ads.scanner)) {
                availableAds = this.ads.scanner;
            } else {
                availableAds = [this.ads.scanner];
            }
        }
        
        console.log('Available ads:', availableAds);
        
        // Randomly select ad type (standard 15s or missing children 5s)
        // For demo purposes, alternate between missing children and standard ads
        const showMissingChildrenAd = Math.random() < 0.5; // 50% chance
        
        // Find the selected ad type or default to first ad
        let selectedAd = null;
        if (availableAds && availableAds.length > 0) {
            if (showMissingChildrenAd) {
                selectedAd = availableAds.find(ad => ad.type === 'missing_children') || availableAds[0];
            } else {
                selectedAd = availableAds.find(ad => ad.type === 'standard') || availableAds[0];
            }
        }
        
        // Set the ad display duration based on the selected ad or default to 15 seconds
        const adDisplayDuration = (selectedAd && selectedAd.duration) ? selectedAd.duration : 15;
        console.log('Selected ad duration:', adDisplayDuration, 'seconds');
        
        // SAFETY CHECK: If we're already in results mode, don't show the ad again
        if (window.inResultsMode || window.showingResultsAfterAd) {
            console.log('SAFETY: Already showing results, skipping ad overlay');
            if (callback) callback(false);
            return;
        }
        
        // Start the countdown timer for the ad with the appropriate duration
        this.startCountdownTimer(adDisplayDuration);
        
        // Use the enhanced showOverlay utility function if available
        if (typeof showOverlay === 'function') {
            if (showOverlay('ad-overlay-results')) {
                console.log('AdManager: Results overlay shown via enhanced showOverlay utility');
            } else {
                console.error('AdManager: Enhanced showOverlay failed, falling back to direct manipulation');
                // Fallback to direct DOM manipulation
                const adOverlayResults = document.getElementById('ad-overlay-results');
                if (adOverlayResults) {
                    adOverlayResults.style.display = 'flex';
                    adOverlayResults.style.opacity = '1';
                    adOverlayResults.style.visibility = 'visible';
                    adOverlayResults.style.zIndex = '2147483647';
                    document.body.style.overflow = 'hidden'; // Prevent scrolling
                    // FIXED: Removed position:fixed that was causing mobile freeze
                    document.body.style.width = '100%'; // Maintain width
                    console.log('AdManager: Results overlay shown via direct manipulation');
                } else {
                    console.error('AdManager: Results overlay element not found!');
                    if (callback) callback(false);
                    return;
                }
            }
        } else {
            // Fallback if showOverlay function is not available
            const adOverlayResults = document.getElementById('ad-overlay-results');
            if (adOverlayResults) {
                adOverlayResults.style.cssText = 'display:flex !important; opacity:1 !important; visibility:visible !important; z-index:2147483647 !important;';
                document.body.style.overflow = 'hidden'; // Prevent scrolling
                // FIXED: Removed position:fixed that was causing mobile freeze
                document.body.style.width = '100%'; // Maintain width
                console.log('AdManager: Results overlay shown via cssText manipulation');
            } else {
                console.error('AdManager: Results overlay element not found!');
                if (callback) callback(false);
                return;
            }
        }
        
        // Load ad in the container inside the overlay
        const adContainerId = 'ad-container-interstitial';
        this.loadAd(adContainerId, function(success) {
            // First, call the original callback
            if (callback) callback(success);
            
            // Add event listeners to the View Results button to ensure we handle clicks properly
            const viewResultsBtn = document.getElementById('view-results-btn');
            if (viewResultsBtn) {
                // Instead of replacing the button which can cause issues with the countdown timer
                // Clear any existing click handlers by using only one definitive handler
                // First, remove any existing click events (if possible)
                if (viewResultsBtn._clickHandlerAdded) {
                    return; // Skip adding another handler if we already added one
                }
                
                // Mark that we're adding a handler to prevent duplicates
                viewResultsBtn._clickHandlerAdded = true;
                
                // Add our definitive handler
                viewResultsBtn.addEventListener('click', function forceKeepResults(e) {
                    // Log the click with timestamp
                    console.log('⭐ View Results button clicked at ' + new Date().toISOString());
                    
                    // Prevent any default behavior or event bubbling
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Set ALL the flags to guarantee we stay in results mode
                    window.inResultsMode = true;
                    window.viewResultsBtnClicked = true;
                    window.currentlyShowingAd = false;
                    window.resultsShown = true;
                    window.hasCompletedAdFlow = true;
                    window.permanentResultsMode = true;
                    
                    // Force-cancel any timers that might be redirecting
                    try {
                        for (let i = 1; i < 500; i++) {
                            clearTimeout(i);
                        }
                    } catch (e) {}
                    
                    // Hide the ad overlay immediately
                    const adOverlay = document.getElementById('ad-overlay-results');
                    if (adOverlay) {
                        adOverlay.style.display = 'none';
                        adOverlay.style.visibility = 'hidden';
                    }
                    
                    // Force show results container
                    const resultsContainer = document.getElementById('results-container');
                    if (resultsContainer) {
                        resultsContainer.classList.remove('d-none');
                        resultsContainer.style.display = 'block';
                    }
                    
                    // Force hide scan form
                    const scanForm = document.getElementById('scan-form-container');
                    if (scanForm) {
                        scanForm.classList.add('d-none');
                        scanForm.style.display = 'none';
                    }
                    
                    // Double-check with a delay
                    setTimeout(() => {
                        // Force show results again in case something tried to hide it
                        if (resultsContainer) {
                            resultsContainer.classList.remove('d-none');
                            resultsContainer.style.display = 'block';
                        }
                    }, 100);
                    
                    // Return false to prevent any default action
                    return false;
                }, true); // Use capture phase to ensure our handler runs first
            }
        });
    },
    
    // Hide the loading ad (when results are ready)
    hideLoadingAd: function() {
        console.log('Hiding all loader ads');
        
        // Find and remove all direct ad elements with loader in the ID
        document.querySelectorAll('[id^="direct-ad-loader-"]').forEach(element => {
            element.remove();
        });
        
        // Force restore scrolling on all elements
        document.body.style.overflow = 'auto';
        document.body.style.position = 'static'; // Reset to static instead of fixed
        document.body.style.width = '';
        document.body.style.height = '';
        document.documentElement.style.overflow = 'auto';
        document.documentElement.style.position = 'static';
        document.body.style.touchAction = 'auto';
        
        // Re-enable zooming
        const viewportMeta = document.querySelector('meta[name="viewport"]');
        if (viewportMeta) {
            viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        }
        
        // Force update body and viewport
        setTimeout(function() {
            window.scrollTo(0, 0);
            window.scrollTo(0, 1);
        }, 100);
    },

    // Hide the interstitial ad (when viewing results)
    hideInterstitialAd: function() {
        console.log('🔄 Hiding all interstitial ads at ' + new Date().toISOString());
        
        // SET ALL THE FLAGS to remain in results mode
        window.inResultsMode = true;
        window.viewResultsBtnClicked = true;
        window.currentlyShowingAd = false;
        window.resultsShown = true;
        window.hasCompletedAdFlow = true;
        window.permanentResultsMode = true;
        
        // Find and hide any scan form container
        const scanForm = document.getElementById('scan-form-container');
        if (scanForm) {
            scanForm.classList.add('d-none');
            scanForm.style.display = 'none';
            console.log('Hiding scan form container');
        }
        
        // Make sure the results container is visible first to prevent "kicking out"
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
            resultsContainer.style.display = 'block';
            console.log('Ensuring results container is visible');
        }
        
        // Find and remove all direct ad elements with interstitial in the ID
        document.querySelectorAll('[id^="direct-ad-interstitial-"]').forEach(element => {
            element.remove();
        });
        
        // Get the ad overlay element
        const adOverlayResults = document.getElementById('ad-overlay-results');
        if (adOverlayResults) {
            // Just hide it without messing with other settings
            adOverlayResults.style.display = 'none';
            console.log('Ad overlay results hidden properly');
        }
        
        // Force restore scrolling on all elements
        document.body.style.overflow = 'auto';
        document.body.style.position = 'static'; // Reset to static instead of fixed
        document.body.style.width = '';
        document.body.style.height = '';
        document.documentElement.style.overflow = 'auto';
        document.documentElement.style.position = 'static';
        document.body.style.touchAction = 'auto';
        
        // Re-enable zooming
        const viewportMeta = document.querySelector('meta[name="viewport"]');
        if (viewportMeta) {
            viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        }
        
        // Force all ad overlays to be closed
        document.querySelectorAll('[id^="ad-overlay"]').forEach(overlay => {
            overlay.style.display = 'none';
        });
        
        // After a short delay, ensure we stay on the results page by:
        // 1. Making sure the results container is visible
        // 2. Scrolling to the results container
        setTimeout(function() {
            // Check if we're in results mode
            if (window.inResultsMode || window.resultsShown || window.permanentResultsMode) {
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    // Force the container visible (again)
                    resultsContainer.classList.remove('d-none');
                    resultsContainer.style.display = 'block';
                    
                    // Scroll to it
                    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    console.log('Scrolled to results container after ad closed');
                } else {
                    // If no results container, just scroll to top
                    window.scrollTo(0, 0);
                }
                
                // Once more force-hide the scan form
                const scanForm = document.getElementById('scan-form-container');
                if (scanForm) {
                    scanForm.classList.add('d-none');
                    scanForm.style.display = 'none';
                }
            }
        }, 200);
    },
    
    // Fetch available ads from the server API
    fetchAvailableAds: function() {
        try {
            // Fetch ads for each placement type
            this.fetchAdsByPlacement('scanner');
            this.fetchAdsByPlacement('results');
            this.fetchAdsByPlacement('homepage');
        } catch (e) {
            console.error('Error fetching available ads:', e);
        }
    },
    
    // Fetch ads by placement type
    fetchAdsByPlacement: function(placement) {
        // In a production environment, this would be an API call
        // For now, we'll simulate this with a setTimeout
        console.log(`Fetching ads for placement: ${placement}`);
        
        // Simulate API delay
        setTimeout(() => {
            // For development, just create mock ads
            this.createMockVideoAd(placement);
        }, 500);
    },
    
    // Create a mock video ad
    createMockVideoAd: function(placement) {
        // Create a mock ad object
        // For 'scanner' placement, create two types of ads - regular and missing children
        if (placement === 'scanner') {
            // This creates both ad types for scanner placement
            this.ads[placement] = [
                {
                    id: Math.floor(Math.random() * 1000),
                    name: `${placement.charAt(0).toUpperCase() + placement.slice(1)} Standard Ad`,
                    file_url: '/static/ads/sample_video.mp4', // This should be a real sample video in production
                    duration: 15,
                    loading_duration: 10, // Default loading overlay duration in seconds
                    custom_message: 'Processing your lottery ticket...', // Default custom message
                    custom_image_path: null, // No custom image in mock data
                    placement: placement,
                    active: true,
                    type: 'standard'
                },
                {
                    id: Math.floor(Math.random() * 1000),
                    name: `${placement.charAt(0).toUpperCase() + placement.slice(1)} Missing Children Ad`,
                    file_url: null, // No video for this ad type
                    image_url: '/static/ads/missing_children.jpg', // Image ad for missing children
                    duration: 5, // Shorter duration (5 seconds) for missing children ads
                    loading_duration: 5,
                    custom_message: 'Help find missing children in South Africa',
                    custom_image_path: '/static/ads/missing_children.jpg',
                    placement: placement,
                    active: true,
                    type: 'missing_children'
                }
            ];
            
            console.log(`Created ${this.ads[placement].length} ads for ${placement} placement`);
        } else {
            // For other placements, create a standard ad
            this.ads[placement] = [{
                id: Math.floor(Math.random() * 1000),
                name: `${placement.charAt(0).toUpperCase() + placement.slice(1)} Ad Example`,
                file_url: '/static/ads/sample_video.mp4',
                duration: 15,
                loading_duration: 10,
                custom_message: 'Processing your lottery ticket...',
                custom_image_path: null,
                placement: placement,
                active: true,
                type: 'standard'
            }];
            
            console.log(`Created standard ad for ${placement} placement`);
        }
    },

    // Record ad impression
    recordAdImpression: function(adId) {
        // Create a new impression
        this.currentImpression = {
            id: 'imp-' + Math.floor(Math.random() * 1000000),
            ad_id: adId,
            timestamp: new Date(),
            duration_viewed: 0,
            was_clicked: false
        };
        
        // Start tracking duration
        const durationInterval = setInterval(() => {
            if (this.currentImpression) {
                this.currentImpression.duration_viewed++;
            } else {
                clearInterval(durationInterval);
            }
        }, 1000);
        
        // In production, send this to the server
        console.log('Ad impression recorded:', this.currentImpression);
    },
    
    // Record ad click
    recordAdClick: function(impression) {
        // Mark impression as clicked
        impression.was_clicked = true;
        
        // In production, send to server
        console.log('Ad click recorded:', impression);
    },
    
    // Start countdown timer for advertisement viewing
    startCountdownTimer: function(seconds) {
        console.log('Starting countdown timer for ' + seconds + ' seconds');
        
        // Get the countdown container
        const countdownContainer = document.getElementById('countdown-container');
        if (!countdownContainer) {
            console.error('Countdown container not found');
            return;
        }
        
        // Get the view results button
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (!viewResultsBtn) {
            console.error('View Results button not found');
            return;
        }
        
        // Disable the button at first - both ways to ensure cross-browser compatibility
        viewResultsBtn.disabled = true;
        viewResultsBtn.setAttribute('disabled', 'disabled');
        viewResultsBtn.classList.remove('btn-pulse');
        
        // Initialize the timer
        let timeLeft = seconds;
        countdownContainer.textContent = 'Please wait ' + timeLeft + ' seconds';
        
        // Create and start the interval
        const countdownTimer = setInterval(function() {
            timeLeft--;
            console.log('Countdown timer: ' + timeLeft + ' seconds remaining');
            
            if (timeLeft <= 0) {
                // Time's up - enable the button
                clearInterval(countdownTimer);
                console.log('Countdown complete - enabling View Results button');
                countdownContainer.textContent = 'You can now view your results!';
                
                // Enable the button - both ways to ensure it works across all browsers
                viewResultsBtn.disabled = false;
                viewResultsBtn.removeAttribute('disabled');
                viewResultsBtn.classList.add('btn-pulse');
                
                // Force a button style update by modifying the DOM
                viewResultsBtn.style.opacity = "0.99";
                setTimeout(() => {
                    viewResultsBtn.style.opacity = "1";
                }, 10);
                
                // Add event listener to ensure the button works
                viewResultsBtn.addEventListener('click', function(e) {
                    console.log('⭐ View Results button clicked at ' + new Date().toISOString());
                    
                    // Hide the ad overlay
                    const adOverlay = document.getElementById('ad-overlay-results');
                    if (adOverlay) {
                        adOverlay.style.display = 'none';
                        adOverlay.style.visibility = 'hidden';
                    }
                    
                    // Make sure results container is shown
                    const resultsContainer = document.getElementById('results-container');
                    if (resultsContainer) {
                        resultsContainer.classList.remove('d-none');
                        resultsContainer.style.display = 'block';
                        
                        // If we have stored results content, display it
                        if (window.parsedResultsContent) {
                            resultsContainer.innerHTML = window.parsedResultsContent;
                        }
                    }
                    
                    // Hide scan form
                    const scanForm = document.getElementById('scan-form-container');
                    if (scanForm) {
                        scanForm.classList.add('d-none');
                        scanForm.style.display = 'none';
                    }
                    
                    // Then call the original hideInterstitialAd function
                    window.AdManager.hideInterstitialAd();
                });
            } else {
                // Update the countdown
                countdownContainer.textContent = 'Please wait ' + timeLeft + ' seconds';
            }
        }, 1000);
        
        // Store the timer ID for potential clearing later
        this.countdownTimerId = countdownTimer;
    }
};

// Initialize after a short delay to ensure DOM is fully loaded
setTimeout(function() {
    if (window.AdManager) {
        window.AdManager.init();
    }
}, 1000);

console.log('Delayed AdManager initialization after 1000ms');