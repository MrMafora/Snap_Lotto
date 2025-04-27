/**
 * Ticket Submission Handler
 * This script handles the ticket submission process with advertisement integration.
 * FIXED VERSION - April 2025
 */

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
        // Clear any previous inline styles
        adOverlayLoading.removeAttribute('style');
        // Apply our display style
        adOverlayLoading.style.display = 'flex';
        adOverlayLoading.style.opacity = '1';
        adOverlayLoading.style.visibility = 'visible';
        console.log('FIRST ad overlay (yellow badge) is now visible');
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
                adOverlayLoading.style.display = 'none';
                console.log('First ad overlay hidden');
            }
            
            // Show the second ad overlay (blue badge)
            const adOverlayResults = document.getElementById('ad-overlay-results');
            if (adOverlayResults) {
                // Clear any previous inline styles
                adOverlayResults.removeAttribute('style');
                // Apply our display style
                adOverlayResults.style.display = 'flex';
                adOverlayResults.style.opacity = '1';
                adOverlayResults.style.visibility = 'visible';
                console.log('SECOND ad overlay (blue badge) is now visible');
                
                // Show the View Results button
                const viewResultsBtn = document.getElementById('view-results-btn');
                if (viewResultsBtn) {
                    viewResultsBtn.disabled = false;
                    viewResultsBtn.style.display = 'block';
                    
                    // Make sure the event listener is only added once
                    if (!viewResultsBtn._clickHandlerAdded) {
                        viewResultsBtn._clickHandlerAdded = true;
                        
                        viewResultsBtn.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            console.log('View Results button clicked');
                            
                            // Hide the button
                            viewResultsBtn.style.display = 'none';
                            
                            // After 15 seconds from clicking the button, hide overlay and show results
                            setTimeout(function() {
                                console.log('Second ad (blue badge) completed - 15 seconds elapsed');
                                
                                // Hide the results overlay
                                adOverlayResults.style.display = 'none';
                                
                                // Show the actual results
                                displayTicketResults();
                            }, 15000); // 15 seconds
                        });
                    }
                } else {
                    console.error('View Results button not found!');
                    // Fallback: display results after 15 seconds automatically
                    setTimeout(function() {
                        if (adOverlayResults) adOverlayResults.style.display = 'none';
                        displayTicketResults();
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

// Add remove image handler
document.addEventListener('DOMContentLoaded', function() {
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