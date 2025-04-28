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
    
    // Setup countdown timer - improved reliability
    setupCountdown() {
        const countdownContainer = document.getElementById('countdown-container');
        const viewResultsBtn = document.getElementById('view-results-btn');
        
        if (!countdownContainer || !viewResultsBtn) {
            console.error('Missing countdown elements!');
            return;
        }
        
        // Store original button text and disable button
        viewResultsBtn.disabled = true;
        const originalBtnText = viewResultsBtn.innerText || 'View Results';
        viewResultsBtn.setAttribute('data-original-text', originalBtnText);
        
        // Clear any existing countdown interval
        if (window.countdownTimerInterval) {
            clearInterval(window.countdownTimerInterval);
        }
        
        // Set initial countdown
        let timeLeft = this.adDisplayTime;
        
        // Update text immediately for the first time
        countdownContainer.textContent = `Please wait ${timeLeft} seconds`;
        viewResultsBtn.textContent = `Wait ${timeLeft}s`;
        
        console.log('Found countdown button: ', viewResultsBtn.textContent);
        
        // Start the countdown
        window.countdownTimerInterval = setInterval(() => {
            timeLeft--;
            
            // Log every tick for debugging
            console.log(`Countdown: ${timeLeft} seconds left`);
            
            if (timeLeft > 0) {
                // Update countdown text on each tick
                countdownContainer.textContent = `Please wait ${timeLeft} seconds`;
                viewResultsBtn.textContent = `Wait ${timeLeft}s`;
                
                // Set a backup direct text update in case the normal update fails
                setTimeout(() => {
                    if (viewResultsBtn.textContent !== `Wait ${timeLeft}s`) {
                        console.log('Using backup text update method');
                        viewResultsBtn.innerText = `Wait ${timeLeft}s`;
                    }
                }, 50);
            } else {
                // COUNTDOWN COMPLETE - enable the button
                clearInterval(window.countdownTimerInterval);
                window.countdownTimerInterval = null;
                
                // Clear countdown container and update button text/state
                countdownContainer.textContent = 'You can now view your results!';
                viewResultsBtn.textContent = originalBtnText;
                viewResultsBtn.disabled = false;
                viewResultsBtn.classList.add('btn-pulse');
                
                // Force-enable the button after a small delay to be extra safe
                setTimeout(() => {
                    viewResultsBtn.disabled = false;
                    if (viewResultsBtn.textContent !== originalBtnText) {
                        viewResultsBtn.textContent = originalBtnText;
                    }
                }, 100);
                
                // Log completion for debugging
                console.log('Countdown completed! Button enabled.');
            }
        }, 1000);
        
        // Set up button click handler with enhanced error handling
        viewResultsBtn.onclick = (event) => {
            try {
                console.log('View Results button clicked');
                
                // Prevent default button behavior
                event.preventDefault();
                
                // Hide the ad overlay
                adOverlayResults.style.display = 'none';
                window.adResultsActive = false;
                
                // Show the results container if it's hidden
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.classList.remove('d-none');
                    console.log('Results container found and displayed');
                    
                    // For immediate scrolling to results
                    setTimeout(() => {
                        try {
                            resultsContainer.scrollIntoView({ behavior: 'smooth' });
                            console.log('Scrolled to results container');
                        } catch (scrollError) {
                            console.error('Error scrolling to results:', scrollError);
                        }
                    }, 100);
                } else {
                    console.error('Results container not found!');
                }
                
                // Display the results based on the cached data
                if (window.scanResults) {
                    console.log('Using cached scan results');
                    displayResults(window.scanResults);
                } else {
                    console.error('No scan results found in cache');
                }
            } catch (error) {
                console.error('Error in view results button handler:', error);
                alert('There was an error displaying your results. Please try again.');
            }
            
            // Return false to prevent any default actions
            return false;
        };
        
        // Helper function to display results
        function displayResults(results) {
            try {
                console.log('Displaying results:', results);
                
                // Find the results container
                const resultsContainer = document.getElementById('results-container');
                if (!resultsContainer) {
                    console.error('Results container not found');
                    return;
                }
                
                // Make sure it's visible
                resultsContainer.classList.remove('d-none');
                
                // Update the UI with the results
                const successContent = document.getElementById('success-content');
                const errorMessage = document.getElementById('error-message');
                const errorText = document.getElementById('error-text');
                
                if (results.error) {
                    // Show error message
                    if (successContent) successContent.classList.add('d-none');
                    if (errorMessage && errorText) {
                        errorText.textContent = results.error;
                        errorMessage.classList.remove('d-none');
                    }
                    return;
                }
                
                // Show success content
                if (errorMessage) errorMessage.classList.add('d-none');
                if (successContent) successContent.classList.remove('d-none');
                
                // Update lottery info
                document.getElementById('result-lottery-type').textContent = results.lottery_type || 'Unknown';
                document.getElementById('result-draw-number').textContent = results.draw_number || 'Latest';
                document.getElementById('result-draw-date').textContent = results.draw_date || 'Unknown';
                
                // Update detected info
                document.getElementById('detected-game-type').textContent = results.detected_type || 'Auto-detected';
                document.getElementById('detected-draw-number').textContent = results.detected_draw || 'Not detected';
                document.getElementById('detected-draw-date').textContent = results.detected_date || 'Not detected';
                
                // Update winning numbers display
                const winningNumbersContainer = document.getElementById('winning-numbers');
                if (winningNumbersContainer && results.winning_numbers) {
                    winningNumbersContainer.innerHTML = '';
                    results.winning_numbers.forEach(number => {
                        const numberBall = document.createElement('div');
                        numberBall.className = 'lottery-ball';
                        numberBall.textContent = number;
                        winningNumbersContainer.appendChild(numberBall);
                    });
                }
                
                // Update ticket numbers display
                const ticketNumbersContainer = document.getElementById('ticket-numbers');
                if (ticketNumbersContainer && results.ticket_numbers) {
                    ticketNumbersContainer.innerHTML = '';
                    results.ticket_numbers.forEach(number => {
                        const numberBall = document.createElement('div');
                        numberBall.className = 'lottery-ball ticket-ball';
                        numberBall.textContent = number;
                        ticketNumbersContainer.appendChild(numberBall);
                    });
                }
                
                // Update matched count
                const matchedCount = document.getElementById('matched-count');
                if (matchedCount && results.matched_count !== undefined) {
                    matchedCount.textContent = results.matched_count;
                }
                
                // Update matched numbers
                const matchedNumbersContainer = document.getElementById('matched-numbers');
                if (matchedNumbersContainer && results.matched_numbers) {
                    matchedNumbersContainer.innerHTML = '';
                    results.matched_numbers.forEach(number => {
                        const numberBall = document.createElement('div');
                        numberBall.className = 'lottery-ball match-ball';
                        numberBall.textContent = number;
                        matchedNumbersContainer.appendChild(numberBall);
                    });
                }
                
                // Update win status
                const winStatusElement = document.getElementById('win-status');
                if (winStatusElement) {
                    if (results.is_winner) {
                        winStatusElement.innerHTML = '<div class="alert alert-success"><i class="fas fa-trophy me-2"></i> Congratulations! You have a winning ticket!</div>';
                    } else {
                        winStatusElement.innerHTML = '<div class="alert alert-warning"><i class="fas fa-times-circle me-2"></i> Sorry, this is not a winning ticket.</div>';
                    }
                }
                
                console.log('Results displayed successfully');
            } catch (error) {
                console.error('Error displaying results:', error);
            }
        }
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