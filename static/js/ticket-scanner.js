/**
 * Ticket Scanner JS
 * Manages the file selection, form submission, and ad display process
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get references to important elements
    const ticketForm = document.getElementById('ticket-form');
    const fileInput = document.getElementById('ticket-image');
    const fileSelectBtn = document.getElementById('file-select-btn');
    const scanButton = document.getElementById('scan-button');
    const previewContainer = document.getElementById('preview-container');
    const ticketPreview = document.getElementById('ticket-preview');
    const removeImageBtn = document.getElementById('remove-image');
    const dropArea = document.getElementById('drop-area');
    
    // Initialize loading/results elements as hidden
    const scannerLoading = document.getElementById('scanner-loading');
    if (scannerLoading) {
        scannerLoading.style.display = 'none';
    }
    
    // Flag for tracking if a file has been selected
    let fileSelected = false;
    
    // Handle the file selection button
    if (fileSelectBtn) {
        fileSelectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('File select button clicked in ticket-scanner.js');
            
            // Try to use the global helper function from file-select-fix.js first
            if (window.openFileSelector && window.openFileSelector()) {
                console.log('Using global file selector helper');
                return false;
            }
            
            // Fallback to direct click
            if (fileInput) {
                console.log('Direct file input click from ticket-scanner.js');
                fileInput.click();
            }
            
            return false;
        });
    }
    
    // Add change handler for file input
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelection);
    }
    
    // Handle file selection
    function handleFileSelection(e) {
        console.log('File selection handled in ticket-scanner.js');
        const files = e.target.files;
        
        if (files && files.length > 0) {
            const file = files[0];
            
            // Check if the file is an image
            if (!file.type.match('image.*')) {
                alert('Please select an image file');
                return;
            }
            
            // Create a URL for the selected file
            const imgUrl = URL.createObjectURL(file);
            
            // Update the preview image
            if (ticketPreview) {
                ticketPreview.src = imgUrl;
                
                // Show the preview
                if (previewContainer) {
                    previewContainer.classList.remove('d-none');
                }
                
                // Hide the drop area
                if (dropArea) {
                    dropArea.style.display = 'none';
                }
                
                // Set the flag
                fileSelected = true;
            }
        }
    }
    
    // Handle removing selected image
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            // Clear the file input
            if (fileInput) {
                fileInput.value = '';
            }
            
            // Hide the preview
            if (previewContainer) {
                previewContainer.classList.add('d-none');
            }
            
            // Show the drop area
            if (dropArea) {
                dropArea.style.display = 'block';
            }
            
            // Reset the flag
            fileSelected = false;
        });
    }
    
    // Handle form submission and trigger the ads
    if (ticketForm) {
        ticketForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            console.log('Form submitted in ticket-scanner.js');
            
            // Check if a file has been selected
            if (!fileSelected) {
                alert('Please select an image of your lottery ticket');
                return false;
            }
            
            // Show loading state
            if (scannerLoading) {
                scannerLoading.style.display = 'block';
            }
            
            // If we have the dual ad manager, show the ad
            if (window.DualAdManager) {
                console.log('Showing ad via DualAdManager');
                DualAdManager.showPublicServiceAd();
            } else {
                console.log('DualAdManager not found, submitting form directly');
                // Handle actual form submission through AJAX instead
                submitFormWithAjax();
            }
            
            return false;
        });
    }
    
    // Scan button should trigger form submission
    if (scanButton) {
        scanButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            console.log('Scan button clicked in ticket-scanner.js');
            
            // Check if a file has been selected
            if (!fileSelected) {
                alert('Please select an image of your lottery ticket');
                return false;
            }
            
            // Submit the form
            if (ticketForm) {
                ticketForm.dispatchEvent(new Event('submit'));
            }
            
            return false;
        });
    }
    
    // Function to handle form submission with AJAX
    function submitFormWithAjax() {
        // Create a FormData object from the form
        const formData = new FormData(ticketForm);
        
        // Create a new XMLHttpRequest
        const xhr = new XMLHttpRequest();
        
        // Configure the request
        xhr.open('POST', ticketForm.action, true);
        
        // Set up the handler for when the request completes
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 400) {
                // Success! Handle the response
                const response = JSON.parse(xhr.responseText);
                
                // Handle the response (this would be done by your existing code)
                if (response.success) {
                    console.log('Ticket scanned successfully');
                    // Your existing success handling code
                } else {
                    console.error('Error scanning ticket:', response.error);
                    // Your existing error handling code
                }
            } else {
                // Error - handle it
                console.error('Server error while scanning ticket');
                // Your existing error handling code
            }
            
            // Hide loading state
            if (scannerLoading) {
                scannerLoading.style.display = 'none';
            }
        };
        
        // Handle errors
        xhr.onerror = function() {
            console.error('Network error while scanning ticket');
            // Your existing error handling code
            
            // Hide loading state
            if (scannerLoading) {
                scannerLoading.style.display = 'none';
            }
        };
        
        // Send the request
        xhr.send(formData);
    }
    
    console.log('Ticket scanner script initialized');
});