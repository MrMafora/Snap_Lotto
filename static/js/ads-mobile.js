/**
 * Mobile-optimized Ads Script
 * Streamlined version of ads.js for faster mobile loading
 */

// State tracking for the ad system
window.adLoadingActive = false;
window.adResultsActive = false;

// Create simpler AdManager for mobile
class AdManager {
    constructor() {
        console.log('Mobile AdManager initializing');
        this.adDisplayTime = 15; // seconds
        this.initialized = false;
        
        // Delayed initialization to ensure DOM is ready
        setTimeout(() => this.initialize(), 500);
    }
    
    initialize() {
        if (this.initialized) return;
        
        // Get ad containers
        this.loaderAdContainer = document.getElementById('ad-container-loader');
        this.interstitialAdContainer = document.getElementById('ad-container-interstitial');
        
        // Prepare ad content (simplified for mobile)
        if (this.loaderAdContainer) {
            this.loaderAdContainer.innerHTML = '<div class="ad-placeholder"><p><i class="fas fa-ad mb-2"></i></p><p class="mb-1">Advertisement</p></div>';
        }
        
        if (this.interstitialAdContainer) {
            this.interstitialAdContainer.innerHTML = '<div class="ad-placeholder"><p><i class="fas fa-ad mb-2 fa-2x text-primary"></i></p><p class="mb-1 fw-bold">Advertisement</p></div>';
        }
        
        this.initialized = true;
        console.log('Mobile AdManager initialized');
    }
    
    // Display the loading ad
    showLoadingAd() {
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading) {
            adOverlayLoading.style.display = 'flex';
            window.adLoadingActive = true;
        }
    }
    
    // Display the results ad with countdown
    showResultsAd() {
        // Hide the loading ad first
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading) {
            adOverlayLoading.style.display = 'none';
            window.adLoadingActive = false;
        }
        
        // Show the results ad
        const adOverlayResults = document.getElementById('ad-overlay-results');
        if (adOverlayResults) {
            adOverlayResults.style.display = 'flex';
            window.adResultsActive = true;
            
            // Set up countdown
            this.setupCountdown();
        }
    }
    
    // Setup countdown timer
    setupCountdown() {
        const countdownContainer = document.getElementById('countdown-container');
        const viewResultsBtn = document.getElementById('view-results-btn');
        
        if (!countdownContainer || !viewResultsBtn) return;
        
        // Disable button during countdown
        viewResultsBtn.disabled = true;
        const originalBtnText = viewResultsBtn.innerText;
        viewResultsBtn.setAttribute('data-original-text', originalBtnText);
        
        // Set initial countdown
        let timeLeft = this.adDisplayTime;
        countdownContainer.textContent = `Please wait ${timeLeft} seconds`;
        viewResultsBtn.textContent = `Wait ${timeLeft}s`;
        
        // Start countdown
        const countdownInterval = setInterval(() => {
            timeLeft--;
            
            // Update countdown text
            if (timeLeft > 0) {
                countdownContainer.textContent = `Please wait ${timeLeft} seconds`;
                viewResultsBtn.textContent = `Wait ${timeLeft}s`;
            } else {
                // Enable the button when countdown is complete
                clearInterval(countdownInterval);
                countdownContainer.textContent = 'You can now view your results!';
                viewResultsBtn.textContent = originalBtnText;
                viewResultsBtn.disabled = false;
                viewResultsBtn.classList.add('btn-pulse');
                
                // Log completion for debugging
                console.log('Countdown completed, button enabled');
            }
        }, 1000);
        
        // Set up button click handler
        viewResultsBtn.onclick = () => {
            adOverlayResults.style.display = 'none';
            window.adResultsActive = false;
            
            // For immediate scrolling to results
            setTimeout(() => {
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.scrollIntoView({ behavior: 'smooth' });
                }
            }, 100);
        };
    }
}

// Initialize the ad manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.adManager = new AdManager();
    console.log('Mobile ads system ready');
});

// Function to process the ticket with ads (mobile optimized)
function processTicketWithAds() {
    try {
        console.log('Processing ticket with ads (mobile optimized)');
        
        // Get form and elements
        const ticketForm = document.getElementById('ticket-form');
        const ticketImageInput = document.getElementById('ticket-image');
        const scanButton = document.getElementById('scan-button');
        
        // Check if image is selected
        if (!ticketImageInput.files || ticketImageInput.files.length === 0) {
            alert('Please select a ticket image first');
            return;
        }
        
        // Show loading overlay with ad
        if (window.adManager) {
            window.adManager.showLoadingAd();
        } else {
            console.error('Ad manager not initialized');
            
            // Fallback if ad manager isn't ready
            const adOverlayLoading = document.getElementById('ad-overlay-loading');
            if (adOverlayLoading) {
                adOverlayLoading.style.display = 'flex';
                window.adLoadingActive = true;
            }
        }
        
        // Prepare form data
        const formData = new FormData(ticketForm);
        
        // Send form data
        fetch('/scan-ticket', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Show the results ad with countdown
            if (window.adManager) {
                window.adManager.showResultsAd();
            } else {
                // Fallback if ad manager isn't ready
                const adOverlayLoading = document.getElementById('ad-overlay-loading');
                const adOverlayResults = document.getElementById('ad-overlay-results');
                
                if (adOverlayLoading) {
                    adOverlayLoading.style.display = 'none';
                    window.adLoadingActive = false;
                }
                
                if (adOverlayResults) {
                    adOverlayResults.style.display = 'flex';
                    window.adResultsActive = true;
                }
            }
            
            // Save the data for later display
            window.scanResults = data;
        })
        .catch(error => {
            console.error('Error during scan:', error);
            
            // Hide all ad overlays
            const adOverlayLoading = document.getElementById('ad-overlay-loading');
            const adOverlayResults = document.getElementById('ad-overlay-results');
            
            if (adOverlayLoading) {
                adOverlayLoading.style.display = 'none';
                window.adLoadingActive = false;
            }
            
            if (adOverlayResults) {
                adOverlayResults.style.display = 'none';
                window.adResultsActive = false;
            }
            
            // Show error
            const errorContainer = document.getElementById('error-message');
            const errorText = document.getElementById('error-text');
            
            if (errorContainer && errorText) {
                errorText.textContent = 'Failed to scan ticket. Please try again.';
                errorContainer.classList.remove('d-none');
            } else {
                alert('Failed to scan ticket. Please try again.');
            }
        });
    } catch (error) {
        console.error('Error in processTicketWithAds:', error);
        alert('An error occurred. Please try again.');
    }
}