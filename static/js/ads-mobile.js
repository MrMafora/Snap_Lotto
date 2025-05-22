/**
 * Mobile-optimized Advertisement Management Removed
 * This file provides stub functions to maintain compatibility with no ads
 */

// Global ad manager object with empty implementations
window.AdManager = window.AdManager || {
    // Empty placeholder objects
    ads: {},
    currentImpression: null,
    adQueue: [],
    
    // Initialization function (now does nothing)
    init: function() {
        console.log('Mobile AdManager initialized with all ads disabled');
    },
    
    // Load ad function replaced with immediate callback
    loadAd: function(containerId, callback) {
        if (callback) {
            setTimeout(callback, 0, true);
        }
        return true;
    },

    // Show loading screen (now without ads)
    showLoadingAd: function(callback) {
        window.adLoadingActive = false;
        if (callback) {
            setTimeout(callback, 0, true);
        }
        return true;
    },

    // Show interstitial ad (now disabled)
    showInterstitialAd: function(callback) {
        window.currentlyShowingAd = false;
        window.adStartTime = 0;
        if (callback) {
            setTimeout(callback, 0, true);
        }
        return true;
    },
    
    // Hide the loading ad (when results are ready)
    hideLoadingAd: function() {
        document.body.style.overflow = 'auto';
        document.body.style.position = 'static';
        document.documentElement.style.overflow = 'auto';
    },

    // Hide the interstitial ad (when viewing results)
    hideInterstitialAd: function() {
        window.inResultsMode = true;
        window.resultsShown = true;
        
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
            resultsContainer.style.display = 'block';
        }
    },
    
    // Empty ad impression recording function (disabled)
    recordAdImpression: function() {
        return false;
    },
    
    // Empty ad click recording function (disabled)
    recordAdClick: function() {
        return false;
    }
};

// Initialize after DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.AdManager) {
        window.AdManager.init();
    }
});