/**
 * Mobile-optimized Advertisement Manager Script
 * This is a lighter version of ads.js specifically for mobile devices
 * Reduces script size from ~28KB to ~5KB for faster loading
 * 
 * Version 2.0 - Enhanced with strict timing enforcement
 */
(function() {
    'use strict';
    
    // Global variables
    window.SnapLottoAds = {
        adDisplayActive: false,
        adLoadingActive: false,
        firstAdShown: false,
        secondAdShown: false,
        firstAdComplete: false,
        secondAdComplete: false,
        adMinimumTime: 15000, // 15 seconds in milliseconds
        adStartTime: null,
        adIntervals: [],
        adTimeouts: [],
        adQueue: [],           // Queue for sequencing ads
        currentAdIndex: 0      // Current ad in the sequence
    };
    
    // Mock ads in development environment
    const isDevelopment = window.location.hostname.includes('replit.dev') || 
                          window.location.hostname.includes('localhost') ||
                          window.location.hostname.includes('127.0.0.1');
    
    // Initialize advertisement manager
    function initAdManager() {
        console.log("AdManager v2.0 initialized from ads-mobile.js");
        
        if (isDevelopment) {
            console.log("Development mode detected, using mock ads");
            createMockAds();
        }
        
        // Set up event handlers for the scanner page
        setupScanButtonHandlers();
        
        // Expose the AdManager API globally
        window.AdManager = {
            showLoadingAd: function(callback) {
                showLoadingAdOverlay();
                
                // Return successful status
                if (typeof callback === 'function') {
                    setTimeout(function() {
                        callback(true);
                    }, 100);
                }
                
                return true;
            },
            
            showInterstitialAd: function(callback) {
                showResultsAdOverlay();
                
                // Return successful status
                if (typeof callback === 'function') {
                    setTimeout(function() {
                        callback(true);
                    }, 100);
                }
                
                return true;
            },
            
            hideAllAds: function() {
                hideLoadingAdOverlay();
                hideResultsAdOverlay();
                return true;
            },
            
            // Helper for debugging
            getAdStatus: function() {
                return {
                    adDisplayActive: window.SnapLottoAds.adDisplayActive,
                    adLoadingActive: window.SnapLottoAds.adLoadingActive,
                    firstAdShown: window.SnapLottoAds.firstAdShown,
                    secondAdShown: window.SnapLottoAds.secondAdShown,
                    firstAdComplete: window.SnapLottoAds.firstAdComplete,
                    secondAdComplete: window.SnapLottoAds.secondAdComplete
                };
            }
        };
    }
    
    // Create mock advertisements for development
    function createMockAds() {
        const loaderContainer = document.getElementById('ad-container-loader');
        const interstitialContainer = document.getElementById('ad-container-interstitial');
        
        if (loaderContainer) {
            loaderContainer.innerHTML = createMockAdHTML('Loading Advertisement');
            console.log("Mock ad created in ad-container-loader");
        }
        
        if (interstitialContainer) {
            interstitialContainer.innerHTML = createMockAdHTML('Results Advertisement');
            console.log("Mock ad created in ad-container-interstitial");
        }
    }
    
    // Generate mock ad HTML
    function createMockAdHTML(text) {
        return `
            <div class="mock-ad" style="width:100%; height:250px; background:#f0f0f0; 
                border:1px solid #ddd; border-radius:4px; display:flex; justify-content:center; 
                align-items:center; color:#333; text-align:center; padding:15px;">
                <div>
                    <h4 style="margin-bottom:10px;">${text}</h4>
                    <p style="margin-bottom:5px;">This is a mock advertisement shown during development.</p>
                    <small>In production, a real advertisement would be displayed here.</small>
                    <p style="margin-top:15px;"><strong>Strictly enforced 15-second viewing time</strong></p>
                </div>
            </div>
        `;
    }
    
    // Reset all ad timers
    function resetAdTimers() {
        // Clear all intervals
        window.SnapLottoAds.adIntervals.forEach(function(interval) {
            clearInterval(interval);
        });
        
        // Clear all timeouts
        window.SnapLottoAds.adTimeouts.forEach(function(timeout) {
            clearTimeout(timeout);
        });
        
        // Reset arrays
        window.SnapLottoAds.adIntervals = [];
        window.SnapLottoAds.adTimeouts = [];
    }
    
    // Set up scan button handlers
    function setupScanButtonHandlers() {
        const scanBtn = document.getElementById('scan-button');
        
        if (scanBtn) {
            scanBtn.addEventListener('click', function(e) {
                const fileInput = document.getElementById('ticket-image');
                
                // Only if we have a file selected
                if (fileInput && fileInput.files.length > 0) {
                    // Reset all ad states
                    resetAdState();
                    showLoadingAdOverlay();
                }
            });
        }
    }
    
    // Reset ad state completely
    function resetAdState() {
        resetAdTimers();
        
        // Reset ad states
        window.SnapLottoAds.adDisplayActive = false;
        window.SnapLottoAds.adLoadingActive = false;
        window.SnapLottoAds.firstAdShown = false;
        window.SnapLottoAds.secondAdShown = false;
        window.SnapLottoAds.firstAdComplete = false;
        window.SnapLottoAds.secondAdComplete = false;
        window.SnapLottoAds.adStartTime = null;
        window.SnapLottoAds.adQueue = [];
        window.SnapLottoAds.currentAdIndex = 0;
        
        console.log("Ad state completely reset");
    }
    
    // Loading ad overlay display
    function showLoadingAdOverlay() {
        const adOverlay = document.getElementById('ad-overlay-loading');
        if (adOverlay) {
            adOverlay.style.display = 'flex';
            
            // Update state and ensure any previous ads are reset
            resetAdTimers();
            window.SnapLottoAds.adLoadingActive = true;
            window.SnapLottoAds.firstAdShown = true;
            window.SnapLottoAds.firstAdComplete = false;
            window.SnapLottoAds.adStartTime = Date.now();
            
            // Add ad counter to show current ad in sequence
            const adCounter = adOverlay.querySelector('.ad-counter');
            if (adCounter) {
                adCounter.textContent = `Ad 1 of 2`;
            } else {
                // Create ad counter if it doesn't exist
                const counterDiv = document.createElement('div');
                counterDiv.className = 'ad-counter';
                counterDiv.style.cssText = 'background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 4px; position: absolute; top: 10px; right: 10px; font-size: 12px;';
                counterDiv.textContent = `Ad 1 of 2`;
                adOverlay.appendChild(counterDiv);
            }
            
            // Add or update countdown display
            const countdownDiv = adOverlay.querySelector('.ad-countdown');
            if (!countdownDiv) {
                const newCountdown = document.createElement('div');
                newCountdown.className = 'ad-countdown';
                newCountdown.style.cssText = 'background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 4px; position: absolute; bottom: 10px; right: 10px; font-size: 12px;';
                newCountdown.textContent = `View results in: 15s`;
                adOverlay.appendChild(newCountdown);
            }
            
            // Force-disable the view results button
            const viewBtn = document.getElementById('view-results-btn');
            if (viewBtn) {
                viewBtn.disabled = true;
                viewBtn.classList.remove('btn-pulse');
                viewBtn.classList.remove('btn-success');
                viewBtn.classList.add('btn-secondary');
                viewBtn.innerHTML = '<i class="fas fa-lock me-2"></i> View Results (Wait 15s)';
            }
            
            console.log("First ad shown at: " + new Date().toISOString());
            
            // Start our own countdown for this ad
            let remainingTime = 15; // 15 seconds
            const countdownElement = adOverlay.querySelector('.ad-countdown');
            
            // Update countdown display immediately
            if (countdownElement) {
                countdownElement.textContent = `View results in: ${remainingTime}s`;
            }
            
            // Set up the countdown interval
            window.adCountdownInterval = setInterval(() => {
                remainingTime--;
                
                // Update the countdown display
                if (countdownElement) {
                    if (remainingTime > 0) {
                        countdownElement.textContent = `View results in: ${remainingTime}s`;
                    } else {
                        countdownElement.textContent = 'Continue to next ad...';
                    }
                }
                
                // When countdown reaches zero, enable results button
                if (remainingTime <= 0) {
                    clearInterval(window.adCountdownInterval);
                    console.log('AdManager: First ad complete, enabling view results button');
                    window.SnapLottoAds.firstAdComplete = true;
                    enableViewResultsButton();
                }
            }, 1000);
            
            // Store the interval for cleanup
            window.SnapLottoAds.adIntervals.push(window.adCountdownInterval);
            
            // Safety timeout as a fallback if timer fails
            const safetyTimeout = setTimeout(function() {
                console.log("SAFETY: First ad fallback timeout reached - only used if timer failed");
                if (!window.SnapLottoAds.firstAdComplete) {
                    window.SnapLottoAds.firstAdComplete = true;
                    enableViewResultsButton();
                }
            }, window.SnapLottoAds.adMinimumTime + 2000); // 2 second buffer
            
            // Store the timeout for cleanup
            window.SnapLottoAds.adTimeouts.push(safetyTimeout);
        }
    }
    
    // Results ad overlay display
    function showResultsAdOverlay() {
        const resultsOverlay = document.getElementById('ad-overlay-results');
        if (resultsOverlay) {
            resultsOverlay.style.display = 'flex';
            
            // Hide all other overlays to ensure no conflicts
            const loadingOverlay = document.getElementById('ad-overlay-loading');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
            
            // Update state and ensure previous ad state is reset
            window.SnapLottoAds.adDisplayActive = true;
            window.SnapLottoAds.secondAdShown = true;
            window.SnapLottoAds.secondAdComplete = false;
            window.SnapLottoAds.adStartTime = Date.now();
            
            // Add ad counter to show current ad in sequence
            const adCounter = resultsOverlay.querySelector('.ad-counter');
            if (adCounter) {
                adCounter.textContent = `Ad 2 of 2`;
            } else {
                // Create ad counter if it doesn't exist
                const counterDiv = document.createElement('div');
                counterDiv.className = 'ad-counter';
                counterDiv.style.cssText = 'background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 4px; position: absolute; top: 10px; right: 10px; font-size: 12px;';
                counterDiv.textContent = `Ad 2 of 2`;
                resultsOverlay.appendChild(counterDiv);
            }
            
            // Add or update countdown display
            const countdownDiv = resultsOverlay.querySelector('.ad-countdown');
            if (!countdownDiv) {
                const newCountdown = document.createElement('div');
                newCountdown.className = 'ad-countdown';
                newCountdown.style.cssText = 'background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 4px; position: absolute; bottom: 10px; right: 10px; font-size: 12px;';
                newCountdown.textContent = `View results in: 15s`;
                resultsOverlay.appendChild(newCountdown);
            }
            
            // Force-disable the view results button for second ad
            const viewBtn = document.getElementById('view-results-btn');
            if (viewBtn) {
                viewBtn.disabled = true;
                viewBtn.classList.remove('btn-pulse');
                viewBtn.classList.remove('btn-success');
                viewBtn.classList.add('btn-secondary');
                viewBtn.innerHTML = '<i class="fas fa-lock me-2"></i> View Results (Wait 15s)';
                
                // Clone to remove any lingering event handlers
                const newBtn = viewBtn.cloneNode(true);
                if (viewBtn.parentNode) {
                    viewBtn.parentNode.replaceChild(newBtn, viewBtn);
                }
            }
            
            console.log("Second ad shown at: " + new Date().toISOString());
            
            // Clear any existing countdown state
            if (window.countdownInterval) {
                clearInterval(window.countdownInterval);
                window.countdownInterval = null;
            }
            
            // Start our own countdown for this ad
            let remainingTime = 15; // 15 seconds
            const countdownElement = document.querySelector('.ad-countdown');
            
            // Update countdown display immediately
            if (countdownElement) {
                countdownElement.textContent = `View results in: ${remainingTime}s`;
            }
            
            // Set up the countdown interval
            window.adCountdownInterval = setInterval(() => {
                remainingTime--;
                
                // Update the countdown display
                if (countdownElement) {
                    if (remainingTime > 0) {
                        countdownElement.textContent = `View results in: ${remainingTime}s`;
                    } else {
                        countdownElement.textContent = 'Loading results...';
                    }
                }
                
                // When countdown reaches zero, enable results button
                if (remainingTime <= 0) {
                    clearInterval(window.adCountdownInterval);
                    console.log('AdManager: Ad sequence complete, enabling results button');
                    window.SnapLottoAds.secondAdComplete = true;
                    enableContinueToResultsButton();
                }
            }, 1000);
            
            // Store the interval for cleanup
            window.SnapLottoAds.adIntervals.push(window.adCountdownInterval);
            
            // Safety timeout that will ONLY run if the central timer system fails
            const safetyTimeout = setTimeout(function() {
                console.log("SAFETY: Second ad fallback timeout reached - only used if timer failed");
                if (!window.SnapLottoAds.secondAdComplete) {
                    window.SnapLottoAds.secondAdComplete = true;
                    enableContinueToResultsButton();
                }
            }, window.SnapLottoAds.adMinimumTime + 2000); // 2 second buffer
            
            // Store the timeout for cleanup
            window.SnapLottoAds.adTimeouts.push(safetyTimeout);
        }
    }
    
    // Enable "View Results" button after first ad countdown
    function enableViewResultsButton() {
        const viewBtn = document.getElementById('view-results-btn');
        if (viewBtn) {
            // Style changes to make it obvious button is enabled
            viewBtn.disabled = false;
            viewBtn.classList.add('btn-pulse');
            viewBtn.classList.remove('btn-secondary');
            viewBtn.classList.add('btn-success');
            
            // Update inner text to indicate it's ready
            viewBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
            
            // Clear any existing event listeners by cloning the button
            const newViewBtn = viewBtn.cloneNode(true);
            viewBtn.parentNode.replaceChild(newViewBtn, viewBtn);
            
            // Set up event listener for button with reliable ordering
            newViewBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log("View Results button clicked at: " + new Date().toISOString());
                
                // Sequence:
                // 1. Hide first overlay
                hideLoadingAdOverlay();
                
                // 2. Make sure results container is visible 
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.classList.remove('d-none');
                }
                
                // 3. Show second ad with results
                showResultsAdOverlay();
                
                return false;
            });
        }
    }
    
    // Enable final "Continue to Results" button after second ad countdown
    function enableContinueToResultsButton() {
        const viewBtn = document.getElementById('view-results-btn');
        if (viewBtn) {
            // Style changes to make it obvious button is enabled
            viewBtn.disabled = false;
            viewBtn.classList.add('btn-pulse');
            viewBtn.classList.remove('btn-secondary');
            viewBtn.classList.add('btn-success');
            
            // Update inner text to indicate it's ready
            viewBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
            
            // Clear any existing event listeners by cloning the button
            const newViewBtn = viewBtn.cloneNode(true);
            viewBtn.parentNode.replaceChild(newViewBtn, viewBtn);
            
            // Set up event listener for final button
            newViewBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log("Continue to Results button clicked at: " + new Date().toISOString());
                
                // Hide the results overlay to show actual results
                hideResultsAdOverlay();
                
                return false;
            });
        }
    }
    
    // Hide loading ad overlay
    function hideLoadingAdOverlay() {
        const adOverlay = document.getElementById('ad-overlay-loading');
        if (adOverlay) {
            adOverlay.style.display = 'none';
            
            // Update state
            window.SnapLottoAds.adLoadingActive = false;
            
            console.log("First ad hidden at: " + new Date().toISOString());
        }
    }
    
    // Hide results ad overlay
    function hideResultsAdOverlay() {
        const resultsOverlay = document.getElementById('ad-overlay-results');
        if (resultsOverlay) {
            resultsOverlay.style.display = 'none';
            
            // Update state
            window.SnapLottoAds.adDisplayActive = false;
            
            console.log("Second ad hidden at: " + new Date().toISOString());
            
            // Make sure results are visible
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.classList.remove('d-none');
                resultsContainer.style.display = 'block';
            }
        }
    }
    
    // COMPLETELY REMOVED original countdown implementation
    // Now we use a placeholder function that delegates to critical-transition-fix.js
    function startCountdown(seconds, counterId, callback) {
        console.log("ads-mobile.js: Not starting countdown - deferring to critical-transition-fix.js");
        
        // Trigger event for critical-transition-fix.js to handle
        const phase = counterId === 'first-ad' ? 'first' : 'second';
        document.dispatchEvent(new CustomEvent('trigger-countdown', {
            detail: { phase: phase, seconds: seconds }
        }));
        
        // Safety timeout to ensure callback runs after the expected time
        // This is just a fallback in case the central system fails
        const safetyTimeout = setTimeout(function() {
            console.log(`ads-mobile.js: Safety callback executed after ${seconds} seconds`);
            if (callback) callback();
        }, seconds * 1000 + 1000);
        
        // Store timeout reference for cleanup
        window.SnapLottoAds.adTimeouts.push(safetyTimeout);
    }
    
    // Diagnostic function that can be called from console for debugging
    window.checkAdState = function() {
        const time = new Date().toISOString();
        console.log(`Ad State at ${time}:`, window.SnapLottoAds);
        
        // Check DOM state of overlays
        const loadingOverlay = document.getElementById('ad-overlay-loading');
        const resultsOverlay = document.getElementById('ad-overlay-results');
        
        console.log('Loading overlay display:', loadingOverlay ? loadingOverlay.style.display : 'not found');
        console.log('Results overlay display:', resultsOverlay ? resultsOverlay.style.display : 'not found');
        
        return window.SnapLottoAds;
    };
    
    // Initialize with delay to avoid blocking initial page render
    setTimeout(initAdManager, 500);
    console.log("AdManager v2.0 will initialize after 500ms");
})();