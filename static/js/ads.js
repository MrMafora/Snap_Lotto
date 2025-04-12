/**
 * Google AdSense integration for Snap Lotto
 * Handles displaying ads at strategic points during the ticket scanning process
 */

// Global ad manager object 
// Using window.AdManager instead of const AdManager to avoid duplicate declarations
window.AdManager = window.AdManager || {
    // Ad slots
    adSlots: {
        scannerPreloader: null,
        resultsInterstitial: null
    },

    // Note: init() is called at the end of this file
    init: function() {
        console.log('AdManager initialized from ads.js');
        
        // Create ad slots if Google AdSense is available
        if (window.adsbygoogle) {
            console.log('AdSense detected, initializing ad slots');
        } else {
            console.warn('AdSense not detected');
        }
        
        // Pre-create mock ads for immediate display
        this.createMockAd('ad-container-loader');
        this.createMockAd('ad-container-interstitial');
    },
    
    // Create a visible mock ad for testing
    createMockAd: function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Mock ad container ${containerId} not found`);
            return;
        }
        
        // Create a visible mock ad with bright colors and border
        container.innerHTML = `
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
    },

    // Load and display an ad in the specified container
    loadAd: function(containerId, callback) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Ad container ${containerId} not found`);
            if (callback) callback(false);
            return;
        }

        // Clear previous content
        container.innerHTML = '';

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
        
        container.appendChild(adContainer);
        
        // Simulate ad loading (would be handled by AdSense in production)
        setTimeout(() => {
            console.log(`Ad loaded in ${containerId}`);
            if (callback) callback(true);
        }, 2000); // 2 second delay to simulate ad loading
    },

    // Show the loading ad (before scan results are ready)
    showLoadingAd: function(callback) {
        console.log('AdManager: Showing loading ad');
        
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
                    document.body.style.position = 'fixed'; // Prevent mobile scroll
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
                document.body.style.position = 'fixed'; // Prevent mobile scroll
                document.body.style.width = '100%'; // Maintain width
                console.log('AdManager: Loading overlay shown via cssText manipulation');
            } else {
                console.error('AdManager: Loading overlay element not found!');
            }
        }
        
        this.loadAd('ad-container-loader', callback);
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
                    document.body.style.position = 'fixed'; // Prevent mobile scroll
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
                document.body.style.position = 'fixed'; // Prevent mobile scroll
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
        console.log('Hiding loading ad');
        const container = document.getElementById('ad-container-loader');
        if (container) {
            container.innerHTML = '';
        }
        
        // Also hide the entire overlay
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading) {
            adOverlayLoading.style.display = 'none';
            // Force restore scrolling on all elements
            document.body.style.overflow = 'auto';
            document.body.style.position = 'static';
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
        }
    },

    // Hide the interstitial ad (when viewing results)
    hideInterstitialAd: function() {
        console.log('Hiding interstitial ad');
        
        // Clear the ad container content
        const adContainerId = 'ad-container-interstitial';
        const container = document.getElementById(adContainerId);
        if (container) {
            container.innerHTML = '';
        }
        
        // Also hide the entire overlay - using ad-overlay-results as the element ID
        const overlayId = 'ad-overlay-results';
        const adOverlayResults = document.getElementById(overlayId);
        if (adOverlayResults) {
            adOverlayResults.style.display = 'none';
            // Force restore scrolling on all elements
            document.body.style.overflow = 'auto';
            document.body.style.position = 'static';
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
        } else {
            console.error(`${overlayId} element not found`);
        }
    }
};

// Initialize ads when DOM is loaded, but with a delay
document.addEventListener('DOMContentLoaded', function() {
    // Delay initialization to ensure DOM is fully loaded and processed
    setTimeout(function() {
        console.log('Delayed AdManager initialization after 1000ms');
        window.AdManager.init();
        
        // Force direct overlay styling to ensure visibility
        const loadingOverlay = document.getElementById('ad-overlay-loading');
        const resultsOverlay = document.getElementById('ad-overlay-results');
        
        if (loadingOverlay) {
            const loaderContainer = document.getElementById('ad-container-loader');
            if (loaderContainer) {
                window.AdManager.createMockAd('ad-container-loader');
                console.log('Successfully created mock ad in loader container');
            }
        }
        
        if (resultsOverlay) {
            const interstitialContainer = document.getElementById('ad-container-interstitial');
            if (interstitialContainer) {
                window.AdManager.createMockAd('ad-container-interstitial');
                console.log('Successfully created mock ad in interstitial container');
            }
        }
    }, 1000);
});