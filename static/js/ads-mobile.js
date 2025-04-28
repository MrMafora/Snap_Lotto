/**
 * Mobile-optimized Advertisement Manager Script
 * This is a lighter version of ads.js specifically for mobile devices
 * Reduces script size from ~28KB to ~5KB for faster loading
 */
(function() {
    'use strict';
    
    // Global variables
    let adDisplayActive = false;
    let adLoadingActive = false;
    window.adLoadingActive = false;
    
    // Mock ads in development environment
    const isDevelopment = window.location.hostname.includes('replit.dev') || 
                          window.location.hostname.includes('localhost') ||
                          window.location.hostname.includes('127.0.0.1');
    
    // Initialize advertisement manager
    function initAdManager() {
        console.log("AdManager initialized from ads-mobile.js");
        
        if (isDevelopment) {
            console.log("Development mode detected, using mock ads");
            createMockAds();
        }
        
        // Set up event handlers for the scanner page
        setupScanButtonHandlers();
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
                </div>
            </div>
        `;
    }
    
    // Set up scan button handlers
    function setupScanButtonHandlers() {
        const scanBtn = document.getElementById('scan-ticket-btn');
        
        if (scanBtn) {
            scanBtn.addEventListener('click', function(e) {
                // Only if we have a file selected
                const fileInput = document.getElementById('ticket-file');
                if (fileInput && fileInput.files.length > 0) {
                    showLoadingAdOverlay();
                }
            });
        }
    }
    
    // Loading ad overlay display
    function showLoadingAdOverlay() {
        const adOverlay = document.getElementById('ad-overlay-loading');
        if (adOverlay) {
            adOverlay.style.display = 'block';
            adLoadingActive = true;
            window.adLoadingActive = true;
            
            // Start countdown (shortened to 15 seconds for mobile)
            startCountdown(15, function() {
                enableViewResultsButton();
            });
        }
    }
    
    // Results ad overlay display
    function showResultsAdOverlay() {
        const resultsOverlay = document.getElementById('ad-overlay-results');
        if (resultsOverlay) {
            resultsOverlay.style.display = 'block';
            adDisplayActive = true;
        }
    }
    
    // Enable "View Results" button after countdown
    function enableViewResultsButton() {
        const viewBtn = document.getElementById('view-results-btn');
        if (viewBtn) {
            viewBtn.disabled = false;
            viewBtn.classList.add('btn-pulse');
            
            // Set up event listener for button
            viewBtn.addEventListener('click', function() {
                hideLoadingAdOverlay();
                showResultsAdOverlay();
                
                // Start second countdown for results ad
                startCountdown(15, function() {
                    enableContinueButton();
                });
            });
        }
    }
    
    // Enable "Continue" button after second countdown
    function enableContinueButton() {
        const continueBtn = document.getElementById('continue-btn');
        if (continueBtn) {
            continueBtn.disabled = false;
            continueBtn.classList.add('btn-pulse');
            
            // Set up event listener for continue button
            continueBtn.addEventListener('click', function() {
                hideResultsAdOverlay();
            });
        }
    }
    
    // Hide loading ad overlay
    function hideLoadingAdOverlay() {
        const adOverlay = document.getElementById('ad-overlay-loading');
        if (adOverlay) {
            adOverlay.style.display = 'none';
            adLoadingActive = false;
            window.adLoadingActive = false;
        }
    }
    
    // Hide results ad overlay
    function hideResultsAdOverlay() {
        const resultsOverlay = document.getElementById('ad-overlay-results');
        if (resultsOverlay) {
            resultsOverlay.style.display = 'none';
            adDisplayActive = false;
        }
    }
    
    // Countdown timer for ads
    function startCountdown(seconds, callback) {
        const countdownEl = document.getElementById('countdown');
        const countdownContainer = document.getElementById('countdown-container');
        
        if (countdownEl && countdownContainer) {
            countdownContainer.style.display = 'block';
            
            let timeLeft = seconds;
            countdownEl.textContent = timeLeft;
            
            const countdownInterval = setInterval(function() {
                timeLeft--;
                countdownEl.textContent = timeLeft;
                
                if (timeLeft <= 0) {
                    clearInterval(countdownInterval);
                    countdownContainer.style.display = 'none';
                    if (callback) callback();
                }
            }, 1000);
        } else {
            // If countdown element not found, still execute callback after delay
            setTimeout(callback, seconds * 1000);
        }
    }
    
    // Initialize with delay to avoid blocking initial page render
    setTimeout(initAdManager, 1000);
    console.log("Delayed AdManager initialization after 1000ms");
})();