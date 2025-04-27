/**
 * Ticket Submission Handler
 * This script handles the ticket submission process with advertisement integration.
 * FIXED VERSION - April 2025
 */

// Add a first countdown timer for the initial ad screen
function initFirstCountdown(seconds) {
    // Create container and add to the first ad overlay
    const adContainer = document.querySelector('#ad-overlay-loading .ad-container-wrapper');
    if (!adContainer) return;
    
    // Create timer element if it doesn't exist
    if (!document.getElementById('first-countdown-container')) {
        const countdownContainer = document.createElement('div');
        countdownContainer.id = 'first-countdown-container';
        countdownContainer.className = 'countdown-container text-center mt-3';
        countdownContainer.style.cssText = 'font-weight: bold; color: #495057; background-color: #f8f9fa; padding: 8px; border-radius: 5px; max-width: 350px; margin: 10px auto;';
        countdownContainer.innerHTML = `
            <div class="countdown-timer">
                <span class="timer-value">${seconds}</span>
                <span class="timer-text">seconds</span>
            </div>
        `;
        
        // Add after the ad container
        adContainer.parentNode.insertBefore(countdownContainer, adContainer.nextSibling);
    }
    
    // Get timer elements
    const countdownContainer = document.getElementById('first-countdown-container');
    const timerElement = countdownContainer.querySelector('.timer-value');
    const timerTextElement = countdownContainer.querySelector('.timer-text');
    
    // Set initial value
    let currentSeconds = seconds;
    timerElement.textContent = currentSeconds;
    timerTextElement.textContent = currentSeconds === 1 ? 'second' : 'seconds';
    
    // Start countdown
    const intervalId = setInterval(() => {
        currentSeconds--;
        
        // Update display
        timerElement.textContent = currentSeconds;
        timerTextElement.textContent = currentSeconds === 1 ? 'second' : 'seconds';
        
        // Apply pulse effect in last 3 seconds
        if (currentSeconds <= 3) {
            timerElement.classList.add('text-danger', 'fw-bold');
            countdownContainer.classList.add('pulse-animation');
        }
        
        // Stop when time is up
        if (currentSeconds <= 0) {
            clearInterval(intervalId);
        }
    }, 1000);
    
    return intervalId;
}

// Function to handle ticket form submission
function handleTicketSubmission(event) {
    // Prevent the default form submission
    event.preventDefault();
    
    console.log('Form submission intercepted for ad display');
    
    // Get form elements
    const form = document.getElementById('ticket-form');
    const fileInput = document.getElementById('ticket-image');
    const scannerLoading = document.getElementById('scanner-loading');
    
    // Validate that an image is selected
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert('Please select an image of your lottery ticket');
        return false;
    }
    
    // Check for empty file (zero bytes)
    if (fileInput.files[0].size === 0) {
        alert('The selected file is empty. Please select a valid image.');
        return false;
    }
    
    // Form data for submission
    const formData = new FormData(form);
    
    // Disable the scan button
    const scanButton = document.getElementById('scan-button');
    if (scanButton) {
        scanButton.disabled = true;
    }
    
    // Hide the normal loading indicator 
    if (scannerLoading) {
        scannerLoading.style.display = 'none';
    }
    
    // IMMEDIATELY show the first ad overlay with yellow badge
    const adOverlayLoading = document.getElementById('ad-overlay-loading');
    if (adOverlayLoading) {
        // Add active class instead of setting inline styles
        adOverlayLoading.classList.add('active');
        console.log('FIRST ad overlay (yellow badge) is now visible');
        
        // Start the first countdown timer - 5 seconds
        initFirstCountdown(5);
    }
    
    // For CSRF token safety
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    if (csrfToken) {
        formData.append('csrf_token', csrfToken.value);
    }
    
    // Submit the form to process the ticket
    console.log('Submitting ticket data to server...');
    
    fetch('/scan-ticket', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('Server response status:', response.status);
        if (!response.ok) {
            throw new Error('Server returned error status: ' + response.status);
        }
        // Parse based on content type
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            return response.text().then(text => {
                console.warn('Response was not JSON. Got content type:', contentType);
                return {
                    success: true,
                    message: 'Ticket processed successfully',
                    html_content: text
                };
            });
        }
    })
    .then(data => {
        console.log('Server processing complete, handling ads sequence...');
        
        // Store the results for later display
        window.ticketResults = data;
        
        // If non-JSON response, store the HTML content
        if (data.html_content) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = data.html_content;
            
            const resultsContent = tempDiv.querySelector('#results-container');
            if (resultsContent) {
                window.parsedResultsContent = resultsContent.innerHTML;
            } else {
                window.parsedResultsContent = data.html_content;
            }
        }
        
        // First ad was displayed when form was submitted
        // After 5 seconds, transition to second ad
        setTimeout(function() {
            console.log('First ad (yellow badge) completed - 5 seconds elapsed');
            
            // Hide the first ad overlay
            if (adOverlayLoading) {
                adOverlayLoading.classList.remove('active');
                console.log('First ad overlay hidden');
            }
            
            // Show the second ad overlay (blue badge)
            const adOverlayResults = document.getElementById('ad-overlay-results');
            if (adOverlayResults) {
                // Add active class to make it visible
                adOverlayResults.classList.add('active');
                console.log('SECOND ad overlay (blue badge) is now visible');
                
                // Initially hide the View Results button until countdown completes
                const viewResultsBtn = document.getElementById('view-results-btn');
                if (viewResultsBtn) {
                    viewResultsBtn.disabled = true;
                    viewResultsBtn.style.display = 'none';
                }
                
                // Show countdown timer in the second ad screen
                const countdownContainer = document.getElementById('countdown-container');
                if (countdownContainer) {
                    // Initialize a 15-second countdown
                    let seconds = 15;
                    countdownContainer.innerHTML = `
                        <div class="countdown-timer">
                            <span class="timer-value">${seconds}</span>
                            <span class="timer-text">seconds</span>
                        </div>
                    `;
                    
                    const timerElement = countdownContainer.querySelector('.timer-value');
                    const timerTextElement = countdownContainer.querySelector('.timer-text');
                    
                    // Make countdown visible
                    countdownContainer.style.display = 'block';
                    
                    // Start timer countdown
                    const timerInterval = setInterval(() => {
                        seconds--;
                        
                        // Update display
                        if (timerElement && timerTextElement) {
                            timerElement.textContent = seconds;
                            timerTextElement.textContent = seconds === 1 ? 'second' : 'seconds';
                            
                            // Apply pulse effect in last 3 seconds
                            if (seconds <= 3) {
                                timerElement.classList.add('text-danger', 'fw-bold');
                                countdownContainer.classList.add('pulse-animation');
                            }
                        }
                        
                        // When countdown completes
                        if (seconds <= 0) {
                            clearInterval(timerInterval);
                            
                            // Show completion message
                            countdownContainer.innerHTML = '<span class="text-success"><i class="fas fa-check-circle me-1"></i> Ready to view results!</span>';
                            
                            // Show the View Results button
                            if (viewResultsBtn) {
                                viewResultsBtn.disabled = false;
                                viewResultsBtn.style.display = 'block'; 
                                viewResultsBtn.classList.add('btn-pulse');
                                
                                // Make sure the event listener is only added once
                                if (!viewResultsBtn._clickHandlerAdded) {
                                    viewResultsBtn._clickHandlerAdded = true;
                                    
                                    viewResultsBtn.addEventListener('click', function(e) {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        
                                        console.log('View Results button clicked');
                                        
                                        // Hide the overlay immediately when button is clicked
                                        adOverlayResults.style.display = 'none';
                                        
                                        // Show the actual results
                                        displayTicketResults();
                                    });
                                }
                            }
                        }
                    }, 1000);
                } else {
                    console.error('Countdown container not found!');
                    // Fallback: Just show button after 15 seconds
                    setTimeout(() => {
                        if (viewResultsBtn) {
                            viewResultsBtn.disabled = false;
                            viewResultsBtn.style.display = 'block';
                            viewResultsBtn.classList.add('btn-pulse');
                            
                            // Add click handler
                            viewResultsBtn.addEventListener('click', function() {
                                adOverlayResults.style.display = 'none';
                                displayTicketResults();
                            });
                        } else {
                            // Ultimate fallback if even button isn't found
                            adOverlayResults.style.display = 'none';
                            displayTicketResults();
                        }
                    }, 15000);
                }
            } else {
                console.error('Second ad overlay not found!');
                // Fallback display results directly
                displayTicketResults();
            }
        }, 5000); // 5 seconds for first ad
    })
    .catch(error => {
        console.error('Error processing ticket:', error);
        
        // Hide the ad overlays
        if (adOverlayLoading) adOverlayLoading.style.display = 'none';
        const adOverlayResults = document.getElementById('ad-overlay-results');
        if (adOverlayResults) adOverlayResults.style.display = 'none';
        
        // Show error message
        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        if (errorMessage && errorText) {
            errorText.textContent = 'Error processing your ticket: ' + error.message;
            errorMessage.classList.remove('d-none');
        } else {
            alert('Error processing your ticket: ' + error.message);
        }
        
        // Re-enable the scan button
        if (scanButton) {
            scanButton.disabled = false;
        }
    });
    
    // Return false to prevent default form submission
    return false;
}

// Function to display ticket results
function displayTicketResults() {
    console.log('Displaying ticket results');
    
    if (typeof window.displayResults === 'function') {
        window.displayResults(window.ticketResults);
    } else {
        console.log('Using fallback results display logic');
        
        // Fallback logic for displaying results
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
            
            // If we have parsedResultsContent, add it to the container
            if (window.parsedResultsContent) {
                resultsContainer.innerHTML = window.parsedResultsContent;
            }
        }
    }
    
    // Re-enable the scan button
    const scanButton = document.getElementById('scan-button');
    if (scanButton) {
        scanButton.disabled = false;
    }
}

// Handle file selection for preview
function handleFileSelection() {
    const fileInput = document.getElementById('ticket-image');
    const previewContainer = document.getElementById('preview-container');
    const ticketPreview = document.getElementById('ticket-preview');
    const scanButton = document.getElementById('scan-button');
    
    if (fileInput && fileInput.files && fileInput.files[0]) {
        // Show preview
        if (previewContainer) previewContainer.style.display = 'block';
        
        // Create object URL for preview
        const objectURL = URL.createObjectURL(fileInput.files[0]);
        if (ticketPreview) ticketPreview.src = objectURL;
        
        // Enable scan button
        if (scanButton) scanButton.disabled = false;
    }
}

// Add remove image handler and ensure ad overlays are hidden on page load
document.addEventListener('DOMContentLoaded', function() {
    // Hide the ad overlays on page load to prevent them appearing when entering page
    const adOverlayLoading = document.getElementById('ad-overlay-loading');
    const adOverlayResults = document.getElementById('ad-overlay-results');
    
    // Make sure overlays are completely hidden when page loads
    if (adOverlayLoading) {
        adOverlayLoading.style.display = 'none';
        adOverlayLoading.style.opacity = '0';
        adOverlayLoading.style.visibility = 'hidden';
    }
    
    if (adOverlayResults) {
        adOverlayResults.style.display = 'none';
        adOverlayResults.style.opacity = '0';
        adOverlayResults.style.visibility = 'hidden';
    }
    
    const removeBtn = document.getElementById('remove-image');
    if (removeBtn) {
        removeBtn.addEventListener('click', function() {
            const fileInput = document.getElementById('ticket-image');
            const previewContainer = document.getElementById('preview-container');
            const scanButton = document.getElementById('scan-button');
            
            // Clear the file input
            if (fileInput) fileInput.value = '';
            
            // Hide preview
            if (previewContainer) previewContainer.style.display = 'none';
            
            // Disable scan button
            if (scanButton) scanButton.disabled = true;
        });
    }
});