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
    
    // Create a direct ad that doesn't require container elements
    createMockAd: function(containerId) {
        // Instead of looking for existing containers, we'll create a direct ad element
        console.log(`Creating direct ad for ${containerId}`);
        
        // Create a direct ad for the page
        this.createDirectAdElement(containerId === 'ad-container-loader' ? 'loader' : 'interstitial');
    },
    
    // Create a direct ad element on the page
    createDirectAdElement: function(adType) {
        // Create a unique ID for this ad
        const adId = 'direct-ad-' + adType + '-' + Date.now();
        
        // Check if an ad with this ID already exists
        if (document.getElementById(adId)) {
            console.log(`Ad ${adId} already exists, not creating duplicate`);
            return;
        }
        
        // Different styling based on ad type
        const borderColor = adType === 'loader' ? '#0d6efd' : '#198754';
        const iconColor = adType === 'loader' ? '#0d6efd' : '#198754';
        const title = adType === 'loader' ? 'PROCESSING YOUR TICKET' : 'YOUR RESULTS ARE READY';
        
        // Create a direct ad element
        const directAdElement = document.createElement('div');
        directAdElement.id = adId;
        directAdElement.className = 'direct-ad-element';
        directAdElement.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.9); display: flex; justify-content: center; align-items: center; z-index: 9999999; padding: 20px;';
        
        // Create the ad content with appropriate styling
        directAdElement.innerHTML = `
            <div style="background-color: white; border-radius: 10px; padding: 20px; max-width: 400px; text-align: center; box-shadow: 0 0 30px rgba(255,255,255,0.2);">
                <div style="font-size: 24px; color: ${iconColor}; margin-bottom: 15px;"><i class="fas fa-ad"></i></div>
                <div style="font-size: 20px; font-weight: bold; margin-bottom: 15px;">${title}</div>
                <div style="border: 3px solid ${borderColor}; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <div style="color: #333; font-size: 16px;">
                        This advertisement helps keep our lottery scanning service free for everyone!
                    </div>
                    <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                        <div style="text-align: center;">
                            <div style="font-size: 24px; color: #28a745;"><i class="fas fa-ticket-alt"></i></div>
                            <div style="font-size: 14px;">Scan Tickets</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 24px; color: #007bff;"><i class="fas fa-search"></i></div>
                            <div style="font-size: 14px;">Check Results</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 24px; color: #ffc107;"><i class="fas fa-trophy"></i></div>
                            <div style="font-size: 14px;">Win Prizes</div>
                        </div>
                    </div>
                </div>
                <button id="ad-continue-btn-${adId}" style="background-color: ${borderColor}; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; cursor: pointer;">Continue to ${adType === 'loader' ? 'Processing' : 'Results'}</button>
            </div>
        `;
        
        // Add to body
        document.body.appendChild(directAdElement);
        console.log(`Direct ad element created with ID ${adId}`);
        document.body.style.overflow = 'hidden';
        
        // Return the ad element ID for future reference
        return adId;
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
        
        // Create a direct ad element for the loader
        const adId = this.createDirectAdElement('loader');
        
        // Setup button event handler with delay
        setTimeout(() => {
            const continueBtn = document.getElementById(`ad-continue-btn-${adId}`);
            if (continueBtn) {
                continueBtn.addEventListener('click', () => {
                    // Remove the ad
                    const adElement = document.getElementById(adId);
                    if (adElement) {
                        adElement.remove();
                    }
                    
                    // Enable scrolling
                    document.body.style.overflow = 'auto';
                    
                    // Call the callback function if provided
                    if (callback) callback(true);
                });
            }
        }, 100);
        
        return adId;
    },

    // Show the interstitial ad (before showing results)
    showInterstitialAd: function(callback) {
        console.log('AdManager: Showing interstitial ad');
        
        // Create a direct ad element for the interstitial
        const adId = this.createDirectAdElement('interstitial');
        
        // Setup button event handler with delay
        setTimeout(() => {
            const continueBtn = document.getElementById(`ad-continue-btn-${adId}`);
            if (continueBtn) {
                continueBtn.addEventListener('click', () => {
                    // Remove the ad
                    const adElement = document.getElementById(adId);
                    if (adElement) {
                        adElement.remove();
                    }
                    
                    // Enable scrolling
                    document.body.style.overflow = 'auto';
                    
                    // Call the callback function if provided
                    if (callback) callback(true);
                });
            }
        }, 100);
        
        // Auto-close after 2.5 seconds to ensure the user sees results
        setTimeout(() => {
            // Remove the ad
            const adElement = document.getElementById(adId);
            if (adElement) {
                adElement.remove();
            }
            
            // Enable scrolling
            document.body.style.overflow = 'auto';
            
            // Call the callback function if provided
            if (callback) callback(true);
        }, 2500);
        
        return adId;
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
    },

    // Hide the interstitial ad (when viewing results)
    hideInterstitialAd: function() {
        console.log('Hiding all interstitial ads');
        
        // Find and remove all direct ad elements with interstitial in the ID
        document.querySelectorAll('[id^="direct-ad-interstitial-"]').forEach(element => {
            element.remove();
        });
        
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