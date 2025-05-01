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
    
    // Current ad index in queue
    currentAdIndex: 0,
    
    // Flag to indicate if ads are in sequence mode
    inSequenceMode: false,
    
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
            
            // Create a visible mock ad with bright colors and border
            targetContainer.innerHTML = `
                <div style="width: 300px; height: 250px; background-color: #f8f9fa; border: 3px solid #0d6efd; border-radius: 10px; display: flex; flex-direction: column; justify-content: center; align-items: center; margin: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                    <div style="font-size: 24px; margin-bottom: 10px; color: #0d6efd;">
                        <i class="fas fa-ad"></i>
                    </div>
                    <div style="font-weight: bold; font-size: 18px; color: #212529; margin-bottom: 5px;">
                        Advertisement
                    </div>
                    <div style="color: #6c757d; font-size: 14px; text-align: center; padding: 0 20px;">
                        This placeholder helps keep the service free
                    </div>
                    <div style="margin-top: 20px; display: flex; gap: 10px;">
                        <div style="width: 12px; height: 12px; background-color: #dc3545; border-radius: 50%;"></div>
                        <div style="width: 12px; height: 12px; background-color: #ffc107; border-radius: 50%;"></div>
                        <div style="width: 12px; height: 12px; background-color: #198754; border-radius: 50%;"></div>
                    </div>
                </div>
            `;
            
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
    showLoadingAd: function(callback) {
        console.log('AdManager: Showing loading ad');
        
        // Get the ad for scanner placement to access its loading_duration
        // FIXED: Always use 5 seconds (hard-coded) for first ad duration as requested
        const ad = this.ads['scanner'] || { loading_duration: 5 }; 
        const loadingDuration = 5000; // Always use exactly 5 seconds (5000ms)
        
        console.log(`AdManager: Using fixed loading duration of 5 seconds`);
        
        // IMPORTANT: Set global flag to track loading state
        window.adLoadingActive = true;
        
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
                console.log(`AdManager: Auto-hiding loading overlay after ${ad.loading_duration} seconds`);
                this.hideLoadingAd();
                
                // CRITICAL: Reset loading state flag
                window.adLoadingActive = false;
                
                // Force display results if we have data but the callback wasn't run
                if (window.lastResultsData && !window.resultsDisplayed) {
                    console.log('AdManager: Force showing interstitial ad since we have results');
                    // Show the results ad immediately
                    this.showInterstitialAd(function() {
                        console.log('AdManager: Forced interstitial ad now showing');
                    });
                }
                
                // If there was a callback, call it again to ensure the ticket processing continues
                if (callback) callback(true);
            }
        }, loadingDuration);
    },

    // Queue multiple ads to be shown in sequence
    queueAds: function(adCount) {
        this.adQueue = [];
        this.currentAdIndex = 0;
        
        // For development mode, create mock ads to queue
        for (let i = 0; i < adCount; i++) {
            // Add different mock ads to the queue
            this.adQueue.push({
                id: i + 1000,
                name: `Sequential Ad ${i+1}`,
                duration: 10, // 10 seconds per ad
                placement: 'interstitial'
            });
        }
        
        console.log(`AdManager: Queued ${adCount} ads for sequential display`);
        return this.adQueue.length;
    },
    
    // Play the next ad in the queue
    playNextAd: function() {
        if (this.adQueue.length === 0 || this.currentAdIndex >= this.adQueue.length) {
            console.log('AdManager: No more ads in queue to play');
            // No more ads, show results
            this.hideInterstitialAd();
            return false;
        }
        
        const nextAd = this.adQueue[this.currentAdIndex];
        console.log(`AdManager: Playing ad ${this.currentAdIndex + 1} of ${this.adQueue.length}: ${nextAd.name}`);
        
        // Update ad display to show current ad number and duration
        const adOverlay = document.getElementById('ad-overlay-results');
        if (adOverlay) {
            const adCounter = adOverlay.querySelector('.ad-counter');
            if (adCounter) {
                adCounter.textContent = `Ad ${this.currentAdIndex + 1} of ${this.adQueue.length}`;
            } else {
                // Create ad counter if it doesn't exist
                const counterDiv = document.createElement('div');
                counterDiv.className = 'ad-counter';
                counterDiv.style.cssText = 'background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 4px; position: absolute; top: 10px; right: 10px; font-size: 12px;';
                counterDiv.textContent = `Ad ${this.currentAdIndex + 1} of ${this.adQueue.length}`;
                adOverlay.appendChild(counterDiv);
            }
            
            // We no longer need to create a separate countdown in the corner
            // This is now handled by the central countdown timer and ad-countdown-fix.js
            // Keeping only the ad counter for context
        }
        
        // Start the countdown for this ad
        this.startAdCountdown(nextAd.duration);
        
        // Increment the index for next time
        this.currentAdIndex++;
        return true;
    },
    
    // Start countdown for current ad
    startAdCountdown: function(duration) {
        let remainingTime = duration;
        
        // We don't need to use our own countdown element anymore
        // as this is now handled by the central countdown timer
        // But we'll keep a reference to the main countdown
        const mainCountdown = document.getElementById('countdown');
        
        // Get the View Results button and disable it during countdown
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            // Let ad-countdown-fix.js handle button states now
            console.log('AdManager: First ad complete, starting next ad or countdown');
        }
        
        // Clear any existing countdown interval
        if (window.adCountdownInterval) {
            clearInterval(window.adCountdownInterval);
        }
        
        // Set up the countdown interval - only for triggering next ad, not UI updates
        window.adCountdownInterval = setInterval(() => {
            remainingTime--;
            
            // Update the main countdown if it exists instead
            if (mainCountdown && remainingTime > 0) {
                // Only update this as a fallback - ad-countdown-fix.js should be handling it
                console.log('Starting second ad countdown sequence');
            }
            
            // When countdown reaches zero, play next ad or finish
            if (remainingTime <= 0) {
                clearInterval(window.adCountdownInterval);
                
                // Play the next ad or enable the View Results button if ad sequence complete
                if (!this.playNextAd()) {
                    console.log('AdManager: Ad sequence complete');
                    
                    // Enable the View Results button after countdown completes
                    if (viewResultsBtn) {
                        viewResultsBtn.disabled = false;
                        viewResultsBtn.classList.remove('disabled');
                        viewResultsBtn.style.opacity = '1';
                        viewResultsBtn.style.cursor = 'pointer';
                    }
                }
            }
        }, 1000);
    },
    
    // Show the interstitial ad (before showing results)
    showInterstitialAd: function(callback) {
        console.log('AdManager: Showing interstitial ad at ' + new Date().toISOString());
        
        // Set a flag to track that we're showing an ad - this prevents autohide timers
        window.currentlyShowingAd = true;
        window.adStartTime = Date.now();
        
        // SAFETY CHECK: If we're already in results mode, don't show the ad again
        if (window.inResultsMode || window.showingResultsAfterAd) {
            console.log('SAFETY: Already showing results, skipping ad overlay');
            if (callback) callback(false);
            return;
        }
        
        // Queue up two ads for sequential display
        this.queueAds(2);
        this.inSequenceMode = true;
        
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
        this.loadAd(adContainerId, (success) => {
            // First, call the original callback
            if (callback) callback(success);
            
            // Start playing the first ad with countdown
            if (success && this.inSequenceMode) {
                this.playNextAd();
            }
            
            // Add event listeners to the View Results button to ensure we handle clicks properly
            const viewResultsBtn = document.getElementById('view-results-btn');
            if (viewResultsBtn) {
                // Remove any existing click handlers
                const newBtn = viewResultsBtn.cloneNode(true);
                viewResultsBtn.parentNode.replaceChild(newBtn, viewResultsBtn);
                
                // Add our definitive handler
                newBtn.addEventListener('click', function forceKeepResults(e) {
                    // Log the click with timestamp
                    console.log('⭐ View Results button clicked at ' + new Date().toISOString());
                    
                    // If button is disabled (during countdown), prevent click
                    if (this.disabled || this.classList.contains('disabled')) {
                        console.log('View Results button clicked while disabled, ignoring');
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }
                    
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
                    window.showingResultsAfterAd = true;
                    
                    // Force-cancel any timers that might be redirecting
                    try {
                        for (let i = 1; i < 500; i++) {
                            clearTimeout(i);
                            clearInterval(i);
                        }
                    } catch (e) {}
                    
                    // Hide the ad overlay immediately
                    const adOverlay = document.getElementById('ad-overlay-results');
                    if (adOverlay) {
                        adOverlay.style.display = 'none';
                        adOverlay.style.visibility = 'hidden';
                    }
                    
                    // Force show results container and ensure it's visible
                    const resultsContainer = document.getElementById('results-container');
                    if (resultsContainer) {
                        resultsContainer.classList.remove('d-none');
                        resultsContainer.style.display = 'block';
                        resultsContainer.style.visibility = 'visible';
                        resultsContainer.style.opacity = '1';
                    }
                    
                    // Force hide scan form completely
                    const scanForm = document.getElementById('scan-form-container');
                    if (scanForm) {
                        scanForm.classList.add('d-none');
                        scanForm.style.display = 'none';
                        scanForm.style.visibility = 'hidden';
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
        
        // Clean up any ad sequence timers
        if (window.adCountdownInterval) {
            clearInterval(window.adCountdownInterval);
            window.adCountdownInterval = null;
        }
        
        // Reset ad sequence flags
        this.inSequenceMode = false;
        this.adQueue = [];
        this.currentAdIndex = 0;
        
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
        
        // Clean up any ad counters or countdown elements
        document.querySelectorAll('.ad-counter, .ad-countdown').forEach(element => {
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
        this.ads[placement] = {
            id: Math.floor(Math.random() * 1000),
            name: `${placement.charAt(0).toUpperCase() + placement.slice(1)} Ad Example`,
            file_url: '/static/ads/sample_video.mp4', // This should be a real sample video in production
            duration: 15,
            loading_duration: 5, // Changed from 10 to 5 seconds as requested
            custom_message: 'Processing your lottery ticket...', // Default custom message
            custom_image_path: null, // No custom image in mock data
            placement: placement,
            active: true
        };
        
        console.log(`Created mock video ad for ${placement}:`, this.ads[placement].name);
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
    }
};

// Initialize after a short delay to ensure DOM is fully loaded
setTimeout(function() {
    if (window.AdManager) {
        window.AdManager.init();
    }
}, 1000);

console.log('Delayed AdManager initialization after 1000ms');