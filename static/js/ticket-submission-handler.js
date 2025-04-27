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
    
    // Show loading spinner
    if (scannerLoading) {
        scannerLoading.style.display = 'block';
    }
    
    // For local development and improved reliability
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    if (csrfToken) {
        formData.append('csrf_token', csrfToken.value);
    }
    
    // Check if we have the AdManager for showing interstitial ads
    if (window.AdManager) {
        console.log('Using AdManager to show ads sequence');
        
        // First, show a loading ad (1st advertisement)
        window.AdManager.showLoadingAd(3, function() {
            console.log('First loading ad completed, now showing interstitial ad');
            
            // Then show interstitial ad with countdown (2nd advertisement)
            window.AdManager.showInterstitialAd(function(adSuccess) {
            console.log('Ad display status:', adSuccess ? 'success' : 'failed');
            
            // Submit the form via AJAX to process the ticket
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
                
                // Process and display the scan results
                if (typeof window.displayResults === 'function') {
                    window.displayResults(data);
                } else {
                    console.log('Displaying results:', data);
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
        });
        });
    } else {
        console.warn('AdManager not found, using direct submission method');
        
        // If AdManager isn't available, submit form directly
        fetch('/scan-ticket', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
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
            // Hide loading spinner
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
            
            // Process the results
            if (typeof window.displayResults === 'function') {
                window.displayResults(data);
            } else {
                console.log('Displaying results:', data);
                // Fallback logic
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.classList.remove('d-none');
                    
                    // If we have parsedResultsContent, add it to the container
                    if (window.parsedResultsContent) {
                        resultsContainer.innerHTML = window.parsedResultsContent;
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Hide loading spinner
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
    }
    
    // Return false to prevent default form submission
    return false;
}