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
        adTimeouts: []
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
            
            // CRITICAL: Force minimum display time for the first ad
            const startTime = Date.now();
            const countdownTimeout = setTimeout(function() {
                // Only enable the button if minimum time has actually passed
                const elapsedTime = Date.now() - startTime;
                console.log("First ad timeout reached after: " + elapsedTime + "ms");
                
                if (elapsedTime >= window.SnapLottoAds.adMinimumTime) {
                    window.SnapLottoAds.firstAdComplete = true;
                    enableViewResultsButton();
                    console.log("First ad completed at: " + new Date().toISOString());
                } else {
                    // If somehow the timer fired too early, set another one
                    console.log("Timer fired too early, resetting...");
                    setTimeout(function() {
                        window.SnapLottoAds.firstAdComplete = true;
                        enableViewResultsButton();
                        console.log("First ad completed after reset at: " + new Date().toISOString());
                    }, window.SnapLottoAds.adMinimumTime - elapsedTime);
                }
            }, window.SnapLottoAds.adMinimumTime);
            
            // Store the timeout for cleanup
            window.SnapLottoAds.adTimeouts.push(countdownTimeout);
            
            // DEFERRED COUNTDOWN: We now defer to critical-transition-fix.js
            // which handles all countdown functionality to prevent conflicts
            console.log("First ad countdown deferred to critical-transition-fix.js");
        }
    }
    
    // Results ad overlay display
    function showResultsAdOverlay() {
        const resultsOverlay = document.getElementById('ad-overlay-results');
        if (resultsOverlay) {
            resultsOverlay.style.display = 'flex';
            
            // Update state and ensure previous ad state is reset
            window.SnapLottoAds.adDisplayActive = true;
            window.SnapLottoAds.secondAdShown = true;
            window.SnapLottoAds.secondAdComplete = false;
            window.SnapLottoAds.adStartTime = Date.now();
            
            // Force-disable the view results button for second ad
            const viewBtn = document.getElementById('view-results-btn');
            if (viewBtn) {
                viewBtn.disabled = true;
                viewBtn.classList.remove('btn-pulse');
                viewBtn.classList.remove('btn-success');
                viewBtn.classList.add('btn-secondary');
                viewBtn.innerHTML = '<i class="fas fa-lock me-2"></i> Continue to Results (Wait 15s)';
            }
            
            console.log("Second ad shown at: " + new Date().toISOString());
            
            // CRITICAL: Force minimum display time for the second ad
            const startTime = Date.now();
            const countdownTimeout = setTimeout(function() {
                // Only enable the button if minimum time has actually passed
                const elapsedTime = Date.now() - startTime;
                console.log("Second ad timeout reached after: " + elapsedTime + "ms");
                
                if (elapsedTime >= window.SnapLottoAds.adMinimumTime) {
                    window.SnapLottoAds.secondAdComplete = true;
                    enableContinueToResultsButton();
                    console.log("Second ad completed at: " + new Date().toISOString());
                } else {
                    // If somehow the timer fired too early, set another one
                    console.log("Second ad timer fired too early, resetting...");
                    setTimeout(function() {
                        window.SnapLottoAds.secondAdComplete = true;
                        enableContinueToResultsButton();
                        console.log("Second ad completed after reset at: " + new Date().toISOString());
                    }, window.SnapLottoAds.adMinimumTime - elapsedTime);
                }
            }, window.SnapLottoAds.adMinimumTime);
            
            // Store the timeout for cleanup
            window.SnapLottoAds.adTimeouts.push(countdownTimeout);
            
            // DEFERRED COUNTDOWN: We now defer to critical-transition-fix.js
            // which handles all countdown functionality to prevent conflicts
            console.log("Second ad countdown deferred to critical-transition-fix.js");
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
            viewBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> Continue to Results!';
            
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
    
    // Countdown timer with stronger enforcement and proper state tracking
    function startCountdown(seconds, counterId, callback) {
        // Determine which button to control based on ad phase
        const viewResultsBtn = document.getElementById('view-results-btn');
        
        // Keep button disabled until countdown completes
        if (viewResultsBtn) {
            viewResultsBtn.disabled = true;
            
            // Add countdown indicator to button text
            if (counterId === 'first-ad') {
                viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${seconds}s)`;
            } else {
                viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> Continue to Results (Wait ${seconds}s)`;
            }
        }
        
        // Get countdown elements - support multiple counter IDs
        const countdownEl = document.getElementById('countdown');
        const countdownContainer = document.getElementById('countdown-container');
        
        if (countdownContainer) {
            countdownContainer.style.display = 'block';
        }
        
        if (countdownEl) {
            countdownEl.textContent = seconds;
        }
        
        // Store the expected completion time
        const startTime = Date.now();
        const expectedEndTime = startTime + (seconds * 1000);
        
        // Create countdown interval
        const countdownInterval = setInterval(function() {
            // Calculate remaining time based on actual elapsed time to prevent manipulation
            const remainingSeconds = Math.max(0, Math.ceil((expectedEndTime - Date.now()) / 1000));
            
            // Update countdown display
            if (countdownEl) {
                countdownEl.textContent = remainingSeconds;
            }
            
            // Update button text during countdown
            if (viewResultsBtn) {
                if (counterId === 'first-ad') {
                    viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> View Results (Wait ${remainingSeconds}s)`;
                } else {
                    viewResultsBtn.innerHTML = `<i class="fas fa-lock me-2"></i> Continue to Results (Wait ${remainingSeconds}s)`;
                }
            }
            
            // Only complete when we've genuinely reached zero
            if (remainingSeconds <= 0) {
                clearInterval(countdownInterval);
                
                // When finished, execute callback
                if (callback) callback();
            }
        }, 250); // Check more frequently for accurate countdown
        
        // Store interval reference for cleanup
        window.SnapLottoAds.adIntervals.push(countdownInterval);
        
        // Safety timeout to ensure callback runs even if interval fails
        const safetyTimeout = setTimeout(function() {
            const elapsedTime = Date.now() - startTime;
            
            // Only execute if minimum time truly passed
            if (elapsedTime >= seconds * 1000) {
                if (callback) callback();
            }
        }, seconds * 1000 + 500); // Add a small buffer to ensure interval completes first
        
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