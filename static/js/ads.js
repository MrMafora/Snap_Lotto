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
        
        // Real implementation would use fetch API:
        /*
        fetch(`/api/ads?placement=${placement}`)
            .then(response => response.json())
            .then(data => {
                if (data && data.ad) {
                    this.ads[placement] = data.ad;
                    console.log(`Loaded ad for ${placement}:`, data.ad.name);
                }
            })
            .catch(error => {
                console.error(`Error fetching ads for ${placement}:`, error);
            });
        */
    },
    
    // Create a mock video ad
    createMockVideoAd: function(placement) {
        // Create a mock ad object
        this.ads[placement] = {
            id: Math.floor(Math.random() * 1000),
            name: `${placement.charAt(0).toUpperCase() + placement.slice(1)} Ad Example`,
            file_url: '/static/ads/sample_video.mp4', // This should be a real sample video in production
            duration: 30,
            placement: placement,
            active: true
        };
        
        console.log(`Created mock video ad for ${placement}:`, this.ads[placement].name);
    },
    
    // Display a video ad in the specified container
    displayVideoAd: function(containerId, placement, callback) {
        const ad = this.ads[placement];
        if (!ad) {
            console.log(`No ad available for placement: ${placement}`);
            if (callback) callback(false);
            return;
        }
        
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            if (callback) callback(false);
            return;
        }
        
        try {
            // Create video element
            const videoContainer = document.createElement('div');
            videoContainer.className = 'video-ad-container';
            
            // Video element
            const video = document.createElement('video');
            video.className = 'ad-video';
            video.width = 640;
            video.height = 360;
            video.style.maxWidth = '100%';
            video.controls = false;
            video.autoplay = true;
            video.muted = false;
            video.playsInline = true;
            
            // Add source
            const source = document.createElement('source');
            source.src = ad.file_url;
            source.type = 'video/mp4';
            video.appendChild(source);
            
            // Create countdown timer
            const countdown = document.createElement('div');
            countdown.className = 'ad-countdown mt-2';
            countdown.innerHTML = `<span class="badge bg-secondary">Ad: <span id="countdown-timer">${ad.duration}</span>s</span>`;
            
            // Controls
            const controls = document.createElement('div');
            controls.className = 'ad-controls mt-2';
            controls.innerHTML = `
                <button class="btn btn-sm btn-outline-primary me-2" id="ad-mute-button">
                    <i class="fas fa-volume-up"></i>
                </button>
                <button class="btn btn-sm btn-outline-secondary" id="ad-skip-button" disabled>
                    Skip Ad in <span id="skip-countdown">30</span>s
                </button>
            `;
            
            // Append elements
            videoContainer.appendChild(video);
            videoContainer.appendChild(countdown);
            videoContainer.appendChild(controls);
            
            // Clear container and add new content
            container.innerHTML = '';
            container.appendChild(videoContainer);
            
            // Record impression
            this.recordAdImpression(ad.id);
            
            // Set up countdown timer
            let secondsLeft = ad.duration;
            const countdownTimer = setInterval(() => {
                secondsLeft--;
                
                // Update countdown displays
                const timerElement = document.getElementById('countdown-timer');
                const skipElement = document.getElementById('skip-countdown');
                
                if (timerElement) timerElement.textContent = secondsLeft;
                if (skipElement) skipElement.textContent = secondsLeft;
                
                // Enable skip button after 5 seconds
                if (secondsLeft <= 25) {
                    const skipButton = document.getElementById('ad-skip-button');
                    if (skipButton) {
                        skipButton.disabled = false;
                        skipButton.innerHTML = '<i class="fas fa-forward"></i> Skip Ad';
                        skipButton.classList.remove('btn-outline-secondary');
                        skipButton.classList.add('btn-outline-primary');
                    }
                }
                
                // When time is up
                if (secondsLeft <= 0) {
                    clearInterval(countdownTimer);
                    if (callback) callback(true);
                }
            }, 1000);
            
            // Handle video ending
            video.addEventListener('ended', () => {
                clearInterval(countdownTimer);
                if (callback) callback(true);
            });
            
            // Setup mute button
            const muteButton = document.getElementById('ad-mute-button');
            if (muteButton) {
                muteButton.addEventListener('click', () => {
                    video.muted = !video.muted;
                    muteButton.innerHTML = video.muted ? 
                        '<i class="fas fa-volume-mute"></i>' : 
                        '<i class="fas fa-volume-up"></i>';
                });
            }
            
            // Setup skip button
            const skipButton = document.getElementById('ad-skip-button');
            if (skipButton) {
                skipButton.addEventListener('click', () => {
                    if (!skipButton.disabled) {
                        clearInterval(countdownTimer);
                        if (callback) callback(true);
                    }
                });
            }
            
            console.log(`Displaying video ad: ${ad.name} (${ad.duration}s)`);
            return true;
        } catch (e) {
            console.error('Error displaying video ad:', e);
            if (callback) callback(false);
            return false;
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
        
        // Real implementation would use fetch API:
        /*
        fetch('/api/record-impression', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ad_id: adId,
                duration: 0 // Initial duration
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.currentImpression = {
                    id: data.impression_id,
                    ad_id: adId,
                    timestamp: new Date(),
                    duration_viewed: 0
                };
                console.log('Impression recorded successfully:', this.currentImpression);
            }
        })
        .catch(error => {
            console.error('Error recording impression:', error);
        });
        */
    },
    
    // Record ad click
    recordAdClick: function(impression) {
        // Mark impression as clicked
        impression.was_clicked = true;
        
        // In production, send to server
        console.log('Ad click recorded:', impression);
        
        // Real implementation would use fetch API:
        /*
        fetch('/api/record-click', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                impression_id: impression.id,
                duration: impression.duration_viewed
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Click recorded successfully');
            }
        })
        .catch(error => {
            console.error('Error recording click:', error);
        });
        */
    }
};

// Create fallback ad containers if they don't exist
function ensureAdContainersExist() {
    let loaderCreated = false;
    let interstitialCreated = false;
    
    try {
        // Check and create loader container if needed
        let loaderContainer = document.getElementById('ad-container-loader');
        if (!loaderContainer) {
            console.log('Creating missing ad-container-loader');
            const loadingOverlay = document.getElementById('ad-overlay-loading');
            if (loadingOverlay) {
                // Find the ad-container div
                let adContainer = loadingOverlay.querySelector('.ad-container');
                if (!adContainer) {
                    adContainer = document.createElement('div');
                    adContainer.className = 'ad-container';
                    adContainer.style.cssText = 'margin: 0 auto; background-color: #f8f9fa; border-radius: 10px; padding: 20px; max-width: 350px;';
                    loadingOverlay.appendChild(adContainer);
                }
                
                // Create the loader container
                loaderContainer = document.createElement('div');
                loaderContainer.id = 'ad-container-loader';
                loaderContainer.style.cssText = 'width: 300px; margin: 0 auto;';
                adContainer.appendChild(loaderContainer);
                loaderCreated = true;
            }
        } else {
            loaderCreated = true;
        }
    } catch (e) {
        console.warn('Error creating loader container:', e);
        // If there's an error, try a simpler approach with minimal DOM operations
        try {
            if (!document.getElementById('ad-container-loader')) {
                const loadingOverlay = document.getElementById('ad-overlay-loading');
                if (loadingOverlay) {
                    // Create a simple container directly
                    const container = document.createElement('div');
                    container.id = 'ad-container-loader';
                    container.style.cssText = 'width: 300px; margin: 0 auto;';
                    loadingOverlay.appendChild(container);
                    loaderCreated = true;
                }
            } else {
                loaderCreated = true;
            }
        } catch (err) {
            console.error('Failed to create loader container with fallback method:', err);
        }
    }
    
    try {
        // Check and create interstitial container if needed
        let interstitialContainer = document.getElementById('ad-container-interstitial');
        if (!interstitialContainer) {
            console.log('Creating missing ad-container-interstitial');
            const resultsOverlay = document.getElementById('ad-overlay-results');
            if (resultsOverlay) {
                // Find the ad-container div
                let adContainer = resultsOverlay.querySelector('.ad-container');
                if (!adContainer) {
                    adContainer = document.createElement('div');
                    adContainer.className = 'ad-container';
                    adContainer.style.cssText = 'margin: 0 auto; background-color: #f8f9fa; border-radius: 10px; padding: 20px; max-width: 350px;';
                    resultsOverlay.appendChild(adContainer);
                }
                
                // Create the interstitial container
                interstitialContainer = document.createElement('div');
                interstitialContainer.id = 'ad-container-interstitial';
                interstitialContainer.style.cssText = 'width: 300px; margin: 0 auto;';
                adContainer.appendChild(interstitialContainer);
                interstitialCreated = true;
            }
        } else {
            interstitialCreated = true;
        }
    } catch (e) {
        console.warn('Error creating interstitial container:', e);
        // If there's an error, try a simpler approach with minimal DOM operations
        try {
            if (!document.getElementById('ad-container-interstitial')) {
                const resultsOverlay = document.getElementById('ad-overlay-results');
                if (resultsOverlay) {
                    // Create a simple container directly
                    const container = document.createElement('div');
                    container.id = 'ad-container-interstitial';
                    container.style.cssText = 'width: 300px; margin: 0 auto;';
                    resultsOverlay.appendChild(container);
                    interstitialCreated = true;
                }
            } else {
                interstitialCreated = true;
            }
        } catch (err) {
            console.error('Failed to create interstitial container with fallback method:', err);
        }
    }
    
    return {
        loaderExists: loaderCreated,
        interstitialExists: interstitialCreated
    };
}

// Initialize ads when DOM is loaded, but with a delay
document.addEventListener('DOMContentLoaded', function() {
    // Delay initialization to ensure DOM is fully loaded and processed
    setTimeout(function() {
        try {
            console.log('Delayed AdManager initialization after 1000ms');
            
            // First ensure the containers exist
            const containersStatus = ensureAdContainersExist();
            
            // Then initialize the ad manager
            if (typeof window.AdManager === 'object' && typeof window.AdManager.init === 'function') {
                window.AdManager.init();
                
                // Force direct overlay styling to ensure visibility
                const loadingOverlay = document.getElementById('ad-overlay-loading');
                const resultsOverlay = document.getElementById('ad-overlay-results');
                
                if (loadingOverlay && containersStatus.loaderExists) {
                    try {
                        window.AdManager.createMockAd('ad-container-loader');
                        console.log('Successfully created mock ad in loader container');
                    } catch (err) {
                        console.warn('Failed to create mock loader ad:', err);
                    }
                }
                
                if (resultsOverlay && containersStatus.interstitialExists) {
                    try {
                        window.AdManager.createMockAd('ad-container-interstitial');
                        console.log('Successfully created mock ad in interstitial container');
                    } catch (err) {
                        console.warn('Failed to create mock interstitial ad:', err);
                    }
                }
            } else {
                console.warn('AdManager not available or init method missing');
            }
        } catch (e) {
            console.error('Error during AdManager initialization:', e);
        }
    }, 1000);
});