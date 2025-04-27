/**
 * Countdown Timer Module for Snap Lotto Ad System
 * This script handles the countdown timer display for ad viewing
 */

// Initialize countdown timer
function initCountdownTimer(containerID, seconds, onComplete = null) {
    const container = document.getElementById(containerID);
    if (!container) {
        console.error('Countdown container not found:', containerID);
        return;
    }
    
    console.log(`Starting ${seconds}-second countdown in container ${containerID}`);
    
    // Create timer display if it doesn't exist
    if (!container.querySelector('.countdown-timer')) {
        container.innerHTML = `
            <div class="countdown-timer">
                <span class="timer-value">${seconds}</span>
                <span class="timer-text">seconds</span>
            </div>
        `;
    }
    
    const timerElement = container.querySelector('.timer-value');
    const timerTextElement = container.querySelector('.timer-text');
    
    if (!timerElement || !timerTextElement) {
        console.error('Timer elements not created properly');
        return;
    }
    
    // Set initial value
    let currentSeconds = seconds;
    timerElement.textContent = currentSeconds;
    timerTextElement.textContent = currentSeconds === 1 ? 'second' : 'seconds';
    
    // Make container visible
    container.style.display = 'block';
    
    // Start countdown
    const intervalId = setInterval(() => {
        currentSeconds--;
        
        // Update display
        timerElement.textContent = currentSeconds;
        timerTextElement.textContent = currentSeconds === 1 ? 'second' : 'seconds';
        
        // Apply pulse effect in last 3 seconds
        if (currentSeconds <= 3) {
            timerElement.classList.add('text-danger', 'fw-bold');
            container.classList.add('pulse-animation');
        }
        
        // Stop when time is up
        if (currentSeconds <= 0) {
            clearInterval(intervalId);
            
            // Visual indication timer is complete
            container.classList.add('completed');
            container.innerHTML = '<span class="text-success"><i class="fas fa-check-circle me-1"></i> Ready to view results!</span>';
            
            // Execute callback if provided
            if (typeof onComplete === 'function') {
                onComplete();
            }
        }
    }, 1000);
    
    // Return interval ID for potential manual clearing
    return intervalId;
}

// Start countdown on second ad overlay automatically when shown
document.addEventListener('DOMContentLoaded', function() {
    // When results ad overlay is shown
    const resultsOverlay = document.getElementById('ad-overlay-results');
    const viewResultsBtn = document.getElementById('view-results-btn');
    const countdownContainer = document.getElementById('countdown-container');
    
    if (resultsOverlay && viewResultsBtn && countdownContainer) {
        // Create a MutationObserver to watch for style changes on the overlay
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'style' && 
                    resultsOverlay.style.display === 'flex') {
                    
                    console.log('Results overlay visible, starting countdown timer');
                    
                    // Start 15-second countdown when overlay becomes visible
                    initCountdownTimer('countdown-container', 15, function() {
                        // When timer completes, add pulse to button
                        if (viewResultsBtn) {
                            viewResultsBtn.classList.add('btn-pulse');
                        }
                    });
                    
                    // Once we've detected the overlay is visible and started the timer,
                    // we can disconnect the observer
                    observer.disconnect();
                }
            });
        });
        
        // Start observing resultsOverlay for style changes
        observer.observe(resultsOverlay, { attributes: true });
    }
});