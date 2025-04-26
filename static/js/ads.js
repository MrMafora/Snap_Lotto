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
        const ad = this.ads['scanner'] || { loading_duration: 10 }; // Default to 10 seconds if no ad found
        const loadingDuration = ad.loading_duration * 1000; // Convert to milliseconds
        
        console.log(`AdManager: Using loading duration of ${ad.loading_duration} seconds`);
        
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
                // If there was a callback, call it again to ensure the ticket processing continues
                if (callback) callback(true);
            }
        }, loadingDuration);
    },

    // Show the interstitial ad (before showing results)
    showInterstitialAd: function(callback) {
        console.log('AdManager: Showing interstitial ad');
        
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
            }
        }
        
        // Load ad in the container inside the overlay
        const adContainerId = 'ad-container-interstitial';
        this.loadAd(adContainerId, callback);
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
        console.log('Hiding all interstitial ads');
        
        // Make sure the results container is visible first to prevent "kicking out"
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
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
        
        // After a short delay, ensure we stay on the results page by:
        // 1. Making sure the results container is visible
        // 2. Scrolling to the results container
        setTimeout(function() {
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.classList.remove('d-none');
                resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                console.log('Scrolled to results container after ad closed');
            } else {
                // If no results container, just scroll to top
                window.scrollTo(0, 0);
            }
        }, 100);
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
            loading_duration: 10, // Default loading overlay duration in seconds
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