/**
 * Google AdSense integration for Snap Lotto
 * Handles displaying ads at strategic points during the ticket scanning process
 */

// Global ad manager object
const AdManager = {
    // Ad slots
    adSlots: {
        scannerPreloader: null,
        resultsInterstitial: null
    },

    // Initialize ad slots
    init: function() {
        // Create ad slots if Google AdSense is available
        if (window.adsbygoogle) {
            console.log('AdSense detected, initializing ad slots');
        } else {
            console.warn('AdSense not detected');
        }
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
        console.log('Showing loading ad');
        
        // Ensure overlay is visible
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading) {
            adOverlayLoading.style.display = 'flex';
            adOverlayLoading.style.opacity = '1';
            adOverlayLoading.style.visibility = 'visible';
            document.body.style.overflow = 'hidden'; // Prevent scrolling
            console.log('Loading overlay is now visible');
        } else {
            console.error('Loading overlay element not found!');
        }
        
        this.loadAd('ad-container-loader', callback);
    },

    // Show the interstitial ad (before showing results)
    showInterstitialAd: function(callback) {
        console.log('Showing interstitial ad');
        
        // Ensure results overlay is visible
        const adOverlayResults = document.getElementById('ad-overlay-results');
        if (adOverlayResults) {
            adOverlayResults.style.display = 'flex';
            adOverlayResults.style.opacity = '1';
            adOverlayResults.style.visibility = 'visible';
            document.body.style.overflow = 'hidden'; // Prevent scrolling
            console.log('Results overlay is now visible');
        } else {
            console.error('Results overlay element not found!');
        }
        
        this.loadAd('ad-container-interstitial', callback);
    }
};

// Initialize ads when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    AdManager.init();
});