/**
 * Ticket Submission Handler - Fixed Version April 2025
 * This script handles the ticket submission process with advertisement integration.
 * Modified to ensure proper transition between ads and display results correctly.
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

// Store ticket data globally for access after ads
let globalTicketData = null;

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
    
    // Get reference to the ad overlays
    const adOverlayLoading = document.getElementById('ad-overlay-loading');
    const adOverlayResults = document.getElementById('ad-overlay-results');
    
    // Track when we showed the first ad to ensure exactly 5 seconds
    const adStartTime = Date.now();
    
    // IMMEDIATELY show the first ad overlay with yellow badge
    if (adOverlayLoading) {
        // Add active class instead of setting inline styles
        adOverlayLoading.classList.add('active');
        console.log('FIRST ad overlay (yellow badge) is now visible at:', adStartTime);
        
        // Start the first countdown timer - 5 seconds
        initFirstCountdown(5);
        
        // Store the start time as a data attribute for tracking
        adOverlayLoading.dataset.adStartTime = adStartTime;
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
        
        // Process response based on content type
        const contentType = response.headers.get('content-type');
        console.log('Response content type:', contentType);
        
        return response.text().then(text => {
            try {
                // Try to parse as JSON
                return JSON.parse(text);
            } catch (e) {
                console.log('Response is HTML, not JSON');
                return { html_content: text };
            }
        });
    })
    .then(data => {
        console.log('Server processing complete');
        
        // Store the ticket data globally for later use
        globalTicketData = data;
        
        // If non-JSON response, store the HTML content
        if (data.html_content) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = data.html_content;
            
            const resultsContent = tempDiv.querySelector('#results-container');
            if (resultsContent) {
                globalTicketData.parsedResultsContent = resultsContent.innerHTML;
            } else {
                globalTicketData.parsedResultsContent = data.html_content;
            }
        }
        
        // Calculate how long the first ad has already been shown
        const currentTime = Date.now();
        const adStartTime = parseInt(adOverlayLoading.dataset.adStartTime || currentTime);
        const elapsedTime = currentTime - adStartTime;
        
        // Calculate remaining time to reach exactly 5 seconds total display time
        // If more than 5 seconds already passed, move on immediately
        const remainingTime = Math.max(0, 5000 - elapsedTime);
        
        console.log('Server response received, ad already shown for:', elapsedTime, 'ms');
        console.log('Will show first ad for', remainingTime, 'more ms to equal exactly 5 seconds total');
        
        // Use the calculated remaining time
        setTimeout(function() {
            console.log('First ad completed - exactly 5 seconds elapsed');
            
            // Create and show the "Process Results" button after the first ad
            // First, create a full-screen overlay just for the button
            const processButtonOverlay = document.createElement('div');
            processButtonOverlay.id = 'process-results-overlay';
            processButtonOverlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(255, 255, 255, 0.98); z-index: 10000; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;';
            
            // Add content to the overlay
            processButtonOverlay.innerHTML = `
                <h3 class="mb-4">First Step Complete!</h3>
                <p class="mb-4">Click the button below to process your ticket results</p>
                <div class="text-center mb-3">
                    <span class="d-inline-block" style="animation: bounce 1s infinite;">⬇️</span>
                </div>
                <button id="process-results-btn" class="btn btn-primary btn-lg" style="min-width: 220px; padding: 15px 30px; font-size: 20px; font-weight: bold; border-radius: 10px; box-shadow: 0 6px 10px rgba(0,123,255,0.3);">
                    <i class="fas fa-cogs me-2"></i> Process Results
                </button>
            `;
            
            // Add the overlay to the body
            document.body.appendChild(processButtonOverlay);
            
            // Hide the first ad overlay
            if (adOverlayLoading) {
                adOverlayLoading.classList.remove('active');
                console.log('First ad overlay hidden');
            }
            
            // Add click event to the Process Results button
            const processButton = document.getElementById('process-results-btn');
            if (processButton) {
                processButton.addEventListener('click', function() {
                    // Remove the process button overlay
                    document.body.removeChild(processButtonOverlay);
                    
                    // Show the second ad overlay (blue badge)
                    if (adOverlayResults) {
                        // Add active class to make it visible
                        adOverlayResults.classList.add('active');
                        console.log('Second ad overlay now visible');
                    }
                
                // Initially hide the View Results button and helper text
                const viewResultsBtn = document.getElementById('view-results-btn');
                const viewResultsHelper = document.querySelector('#ad-overlay-results .text-center.mt-4.mb-1');
                
                        if (viewResultsBtn) {
                            viewResultsBtn.disabled = true;
                            viewResultsBtn.style.display = 'none';
                        }
                        
                        if (viewResultsHelper) {
                            viewResultsHelper.style.display = 'none';
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
                            
                            // Show the View Results button and helper text
                            if (viewResultsBtn) {
                                viewResultsBtn.disabled = false;
                                viewResultsBtn.style.display = 'block'; 
                                viewResultsBtn.classList.add('btn-pulse');
                                
                                // Also display the helper text with arrow pointing to the button
                                if (viewResultsHelper) {
                                    viewResultsHelper.style.display = 'block';
                                }
                                
                                // Make sure the event listener is only added once
                                if (!viewResultsBtn._clickHandlerAdded) {
                                    viewResultsBtn._clickHandlerAdded = true;
                                    
                                    viewResultsBtn.addEventListener('click', function(e) {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        
                                        console.log('View Results button clicked');
                                        
                                        // Hide the overlay immediately when button is clicked using class
                                        adOverlayResults.classList.remove('active');
                                        
                                        // Show the actual results using our global ticket data
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
                            
                            // Also display the helper text in fallback case
                            if (viewResultsHelper) {
                                viewResultsHelper.style.display = 'block';
                            }
                            
                            // Add click handler
                            if (!viewResultsBtn._clickHandlerAdded) {
                                viewResultsBtn._clickHandlerAdded = true;
                                viewResultsBtn.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    adOverlayResults.classList.remove('active');
                                    displayTicketResults();
                                });
                            }
                        } else {
                            // Ultimate fallback if even button isn't found
                            adOverlayResults.classList.remove('active');
                            displayTicketResults();
                        }
                    }, 15000);
                }
            } else {
                console.error('Second ad overlay not found!');
                // Fallback display results directly
                displayTicketResults();
            }
        }, remainingTime); // Use exactly the remaining time to complete 5 seconds
    })
    .catch(error => {
        console.error('Error processing ticket:', error);
        
        // Hide the ad overlays using classes
        if (adOverlayLoading) adOverlayLoading.classList.remove('active');
        if (adOverlayResults) adOverlayResults.classList.remove('active');
        
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
    
    if (!globalTicketData) {
        console.error('No ticket data available');
        return;
    }
    
    // Display the results on the page
    console.log('Displaying results:', globalTicketData);
    
    // Store the results in window object for the template's handleTicketSubmission function
    window.ticketResults = globalTicketData;
    
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
        // Make sure results container is visible
        resultsContainer.classList.remove('d-none');
        resultsContainer.style.display = 'block';
        
        // If we have parsed HTML content, use it
        if (globalTicketData.parsedResultsContent) {
            resultsContainer.innerHTML = globalTicketData.parsedResultsContent;
        }
        // Otherwise use standard JSON display if we have ticket data
        else if (globalTicketData.ticket_info) {
            // Use window.displayResults if it exists (external function from template)
            if (typeof window.displayResults === 'function') {
                try {
                    window.displayResults(globalTicketData);
                    console.log('Called window.displayResults successfully');
                } catch (e) {
                    console.error('Error in window.displayResults:', e);
                }
            } else {
                console.log('No window.displayResults function - using fallback');
                
                // Basic display of ticket info
                const successContent = document.getElementById('success-content');
                if (successContent) {
                    successContent.classList.remove('d-none');
                    successContent.style.display = 'block';
                
                    // Display ticket info
                    const resultLotteryType = document.getElementById('result-lottery-type');
                    if (resultLotteryType) resultLotteryType.textContent = globalTicketData.ticket_info.game_type || '';
                    
                    const resultDrawNumber = document.getElementById('result-draw-number');
                    if (resultDrawNumber) resultDrawNumber.textContent = globalTicketData.ticket_info.draw_number || '';
                    
                    const resultDrawDate = document.getElementById('result-draw-date');
                    if (resultDrawDate) resultDrawDate.textContent = globalTicketData.ticket_info.draw_date || '';
                
                    // Display detected info
                    const detectedGameType = document.getElementById('detected-game-type');
                    if (detectedGameType) detectedGameType.textContent = globalTicketData.ticket_info.game_type || '';
                    
                    const detectedDrawNumber = document.getElementById('detected-draw-number');
                    if (detectedDrawNumber) detectedDrawNumber.textContent = globalTicketData.ticket_info.draw_number || '';
                    
                    const detectedDrawDate = document.getElementById('detected-draw-date');
                    if (detectedDrawDate) detectedDrawDate.textContent = globalTicketData.ticket_info.draw_date || '';
                }
            }
        }
        
        // Directly call the update ball matching function if it exists
        if (window.updateBallMatching && globalTicketData) {
            try {
                window.updateBallMatching(globalTicketData);
            } catch (e) {
                console.error('Error updating ball matches:', e);
            }
        }
    } else {
        console.error('Results container not found - cannot display results');
    }
    
    // Re-enable the scan button
    const scanButton = document.getElementById('scan-button');
    if (scanButton) {
        scanButton.disabled = false;
    }
    
    // Clean up any remaining overlays
    const processResultsOverlay = document.getElementById('process-results-overlay');
    if (processResultsOverlay) {
        document.body.removeChild(processResultsOverlay);
    }
}

// Handle file selection for preview
function handleFileSelection() {
    const fileInput = document.getElementById('ticket-image');
    const previewContainer = document.getElementById('preview-container');
    const ticketPreview = document.getElementById('ticket-preview');
    const scanButton = document.getElementById('scan-button');
    
    if (fileInput && fileInput.files && fileInput.files[0]) {
        console.log('File selection handler called');
        console.log('File selected:', fileInput.files[0].name, 'Type:', fileInput.files[0].type, 'Size:', fileInput.files[0].size, 'bytes');
        
        // Show preview
        if (previewContainer) previewContainer.style.display = 'block';
        
        // Try both methods of displaying the preview
        try {
            // Method 1: Create object URL for preview
            const objectURL = URL.createObjectURL(fileInput.files[0]);
            if (ticketPreview) {
                console.log('Created object URL for preview');
                ticketPreview.src = objectURL;
                ticketPreview.onload = function() {
                    console.log('Preview image loaded successfully');
                };
                ticketPreview.onerror = function(e) {
                    console.error('Error loading preview image', e);
                    // Fallback to FileReader if Object URL fails
                    useFileReader();
                };
            }
        } catch (e) {
            console.error('Error using Object URL:', e);
            // Fallback to FileReader
            useFileReader();
        }
        
        function useFileReader() {
            // Method 2: Use FileReader as fallback
            const reader = new FileReader();
            reader.onload = function(e) {
                if (ticketPreview) {
                    ticketPreview.src = e.target.result;
                    console.log('Using FileReader result as fallback');
                }
            };
            reader.onloadend = function() {
                console.log('Preview image loaded using FileReader fallback');
            };
            reader.readAsDataURL(fileInput.files[0]);
        }
        
        // Enable scan button
        if (scanButton) {
            scanButton.disabled = false;
            console.log('Preview displayed and scan button enabled');
        }
    }
}

// Make sure all components are ready when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Reset global ticket data
    globalTicketData = null;
    
    // Hide the ad overlays on page load to prevent them appearing when entering page
    const adOverlayLoading = document.getElementById('ad-overlay-loading');
    const adOverlayResults = document.getElementById('ad-overlay-results');
    
    // Make sure overlays are completely hidden when page loads
    if (adOverlayLoading) {
        adOverlayLoading.classList.remove('active');
        // Extra safety - reset inline styles
        adOverlayLoading.style.display = '';
        adOverlayLoading.style.opacity = '';
        adOverlayLoading.style.visibility = '';
    }
    
    if (adOverlayResults) {
        adOverlayResults.classList.remove('active');
        // Extra safety - reset inline styles
        adOverlayResults.style.display = '';
        adOverlayResults.style.opacity = '';
        adOverlayResults.style.visibility = '';
    }
    
    // Set up the remove image button
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
    
    // Attach form submit handler
    const ticketForm = document.getElementById('ticket-form');
    if (ticketForm) {
        // Make sure the form submission process uses our handler
        ticketForm.setAttribute('onsubmit', 'return handleTicketSubmission(event)');
    }
});