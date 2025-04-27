/**
 * Ticket Submission Handler
 * This script handles the ticket submission process with advertisement integration
 * and countdown timer functionality.
 */

// Function to handle ticket form submission
function handleTicketSubmission(event) {
    // Prevent the default form submission
    event.preventDefault();
    
    console.log('Form submission intercepted for ad display');
    
    // Get form elements
    const form = document.getElementById('ticket-form');
    const formData = new FormData(form);
    const scannerLoading = document.getElementById('scanner-loading');
    
    // IMMEDIATELY show the ad overlay before anything else
    if (window.AdManager) {
        // Show ad overlay immediately
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading) {
            adOverlayLoading.style.display = 'flex';
            console.log('Ad overlay displayed IMMEDIATELY');
        }
    } else {
        // Fallback to regular spinner if AdManager isn't available
        if (scannerLoading) {
            scannerLoading.style.display = 'block';
        }
    }
    
    // For local development and improved reliability
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    if (csrfToken) {
        formData.append('csrf_token', csrfToken.value);
    }
    
    // First, submit the form to process the ticket
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
        // Check the content type to determine how to parse it
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            // If not JSON, get the text and attempt to create a default response
            return response.text().then(text => {
                console.warn('Response was not JSON. Got content type:', contentType);
                // Return a simple object with basic information
                return {
                    success: true,
                    message: 'Ticket processed successfully',
                    html_content: text
                };
            });
        }
    })
    .then(data => {
        console.log('Scan ticket response received:', data);
        
        // Hide the loading indicator
        if (scannerLoading) {
            scannerLoading.style.display = 'none';
        }
        
        // Store the HTML content for later display after ad is closed
        window.ticketResults = data;
        
        // If we have HTML content from a non-JSON response, store it for later
        if (data.html_content) {
            // Create a temporary div to parse the HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = data.html_content;
            
            // Try to extract the results content from the HTML
            const resultsContent = tempDiv.querySelector('#results-container');
            if (resultsContent) {
                window.parsedResultsContent = resultsContent.innerHTML;
            } else {
                // Fallback to using the full HTML
                window.parsedResultsContent = data.html_content;
            }
        }
        
        // Check if we have the AdManager for showing ads
        if (window.AdManager) {
            console.log('Using AdManager to show ads sequence');
            
            // Ad overlay was already made visible at the beginning of this function
            // No need to show it again here
            
            // First, show a loading ad (1st advertisement) for 5 seconds
            window.AdManager.showLoadingAd(5, function() {
                console.log('First loading ad (processing) completed');
                
                // After the first ad completes, show a "View Results" button
                const viewResultsBtn = document.getElementById('view-results-btn');
                if (viewResultsBtn) {
                    viewResultsBtn.disabled = false;
                    
                    // Make the button green and prominent
                    viewResultsBtn.classList.add('btn-success');
                    viewResultsBtn.classList.remove('btn-secondary');
                    viewResultsBtn.textContent = 'View Results';
                    
                    // Make sure the button is visible
                    viewResultsBtn.style.display = 'block';
                    
                    console.log('View Results button enabled');
                    
                    // Add click handler to the View Results button to show second ad
                    if (!viewResultsBtn._clickHandlerAdded) {
                        viewResultsBtn._clickHandlerAdded = true;
                        
                        viewResultsBtn.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            console.log('View Results button clicked, showing second advertisement');
                            
                            // Hide the View Results button
                            viewResultsBtn.style.display = 'none';
                            
                            // When the View Results button is clicked, show the interstitial ad
                            window.AdManager.showInterstitialAd(function(adSuccess) {
                                console.log('Second ad (interstitial) completed:', adSuccess ? 'success' : 'failed');
                                
                                // After the interstitial ad completes, display the results
                                displayTicketResults();
                            });
                        });
                    }
                } else {
                    console.error('View Results button not found!');
                    // If no button is found, display results automatically
                    displayTicketResults();
                }
            });
        } else {
            console.warn('AdManager not found, displaying results directly');
            // If AdManager isn't available, display results directly
            displayTicketResults();
        }
    })
    .catch(error => {
        console.error('Error processing ticket:', error);
        
        // Hide loading indicator
        if (scannerLoading) {
            scannerLoading.style.display = 'none';
        }
        
        // Show error message
        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        if (errorMessage && errorText) {
            errorText.textContent = 'Error processing your ticket: ' + error.message;
            errorMessage.classList.remove('d-none');
        } else {
            alert('Error processing your ticket: ' + error.message);
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
}