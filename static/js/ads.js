/**
 * Advertisement Management Removed
 * This file now provides stub functions to maintain compatibility
 * with existing code but without displaying any advertisements
 */

// Global ad manager object with empty implementations
window.AdManager = window.AdManager || {
    // Empty placeholder objects
    ads: {},
    currentImpression: null,
    adQueue: [],
    
    // Initialization function (now does nothing)
    init: function() {
        console.log('AdManager initialized with all ads disabled');
    },
    
    // Empty function that previously created mock ads
    createMockAd: function(containerId) {
        // Advertisement functionality has been removed
        return false;
    },
    
    ensureContainerExists: function(containerId) {
        // Advertisement functionality has been removed
        return false;
    },

    // Load ad function replaced with immediate callback
    loadAd: function(containerId, callback) {
        // Skip all ad loading and immediately call the callback
        if (callback) {
            setTimeout(callback, 0, true);
        }
        return true;
    },

    // Show loading screen (now without ads)
    showLoadingAd: function(callback) {
        console.log('AdManager: Loading screen requested (ads disabled)');
        
        // Reset loading state flag
        window.adLoadingActive = false;
        
        // Execute callback immediately
        if (callback) {
            setTimeout(callback, 0, true);
        }
        
        return true;
    },

    // Show interstitial ad (now disabled)
    showInterstitialAd: function(callback) {
        console.log('AdManager: Interstitial ads are now disabled');
        
        // Reset ad flags
        window.currentlyShowingAd = false;
        window.adStartTime = 0;
        
        // Execute callback immediately
        if (callback) {
            setTimeout(callback, 0, true);
        }
        
        return true;
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

    // Empty ad impression recording function (disabled)
    recordAdImpression: function(adId) {
        return false;
    },
    
    // Empty ad click recording function (disabled)
    recordAdClick: function(impression) {
        return false;
    }
};

// Initialize after a short delay to ensure DOM is fully loaded
setTimeout(function() {
    if (window.AdManager) {
        window.AdManager.init();
    }
}, 1000);

console.log('Delayed AdManager initialization after 1000ms');