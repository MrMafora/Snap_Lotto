/**
 * File Upload Fix
 * Critical fix for the file selection redirect issue in the ticket scanner
 * This script ensures proper event handling during file selection
 */

(function() {
    'use strict';
    
    // Execute immediately to intercept all form submissions
    console.log('[UploadFix] Installing global form submission interceptor');
    
    // Set up global form submission interceptor
    const originalSubmit = HTMLFormElement.prototype.submit;
    HTMLFormElement.prototype.submit = function() {
        // Only intercept ticket-form submissions
        if (this.id === 'ticket-form') {
            const fileInput = document.getElementById('ticket-image');
            if (fileInput && fileInput.files.length > 0) {
                console.log('[UploadFix] Form submission intercepted, file selected but not processed yet');
                
                // Check if we're intentionally submitting
                if (!window.intentionalFormSubmit) {
                    console.log('[UploadFix] Preventing unintentional form submission');
                    
                    // Show user feedback
                    const previewContainer = document.getElementById('preview-container');
                    if (previewContainer) {
                        previewContainer.classList.remove('d-none');
                    }
                    
                    // Trigger file preview
                    const file = fileInput.files[0];
                    if (file) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const preview = document.getElementById('ticket-preview');
                            if (preview) {
                                preview.src = e.target.result;
                                console.log('[UploadFix] Preview updated with selected file');
                            }
                        };
                        reader.readAsDataURL(file);
                    }
                    
                    return false;
                } else {
                    console.log('[UploadFix] Allowing intentional form submission');
                    window.intentionalFormSubmit = false;
                }
            }
        }
        
        // Call original submit for non-ticket forms or intentional submissions
        return originalSubmit.apply(this, arguments);
    };
    
    // Wait for DOM to be fully loaded to complete setup
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[UploadFix] DOM loaded, initializing form submission controls');
        
        // Get the form and file input elements
        const ticketForm = document.getElementById('ticket-form');
        const fileInput = document.getElementById('ticket-image');
        
        // Setup direct event listener for form submission
        if (ticketForm) {
            // Remove existing listeners by cloning
            const newForm = ticketForm.cloneNode(true);
            if (ticketForm.parentNode) {
                ticketForm.parentNode.replaceChild(newForm, ticketForm);
            
                // Add our high-priority submit handler
                newForm.addEventListener('submit', function(e) {
                    // Always prevent default form submission
                    e.preventDefault();
                    console.log('[UploadFix] Form submit event prevented');
                    
                    // If this is an intentional submission, use AJAX instead
                    if (window.intentionalFormSubmit === true) {
                        console.log('[UploadFix] Processing intentional form submission via AJAX');
                        
                        // Use CleanFileUploader if available
                        if (window.CleanFileUploader && typeof window.CleanFileUploader.upload === 'function') {
                            window.CleanFileUploader.upload();
                        } else {
                            console.log('[UploadFix] CleanFileUploader not available, using fallback');
                            
                            // Fallback to basic AJAX submission
                            const formData = new FormData(newForm);
                            const xhr = new XMLHttpRequest();
                            xhr.open('POST', '/scan-ticket', true);
                            xhr.onload = function() {
                                if (xhr.status === 200) {
                                    console.log('[UploadFix] Form submitted successfully via AJAX');
                                    try {
                                        const response = JSON.parse(xhr.responseText);
                                        if (window.processTicketScanResults) {
                                            window.processTicketScanResults(response);
                                        } else if (window.handleTicketScanResults) {
                                            window.handleTicketScanResults(response);
                                        }
                                    } catch (e) {
                                        console.error('[UploadFix] Error processing response:', e);
                                    }
                                }
                            };
                            xhr.send(formData);
                        }
                    }
                    
                    return false;
                }, true); // Use capture for highest priority
            }
        }
        
        // Setup the file input to properly handle changes
        if (fileInput) {
            // Clone to remove previous listeners
            const newFileInput = fileInput.cloneNode(true);
            if (fileInput.parentNode) {
                fileInput.parentNode.replaceChild(newFileInput, fileInput);
                
                // Add our enhanced change handler
                newFileInput.addEventListener('change', function(e) {
                    console.log('[UploadFix] File input change detected');
                    
                    // Prevent any form submission
                    e.preventDefault();
                    
                    const file = this.files[0];
                    if (file) {
                        console.log('[UploadFix] File selected:', file.name);
                        
                        // Update preview if possible
                        const previewImage = document.getElementById('ticket-preview');
                        const previewContainer = document.getElementById('preview-container');
                        
                        if (previewImage) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                previewImage.src = e.target.result;
                                console.log('[UploadFix] Preview updated');
                                
                                if (previewContainer) {
                                    previewContainer.classList.remove('d-none');
                                }
                                
                                // Enable scan button if it exists
                                const scanButton = document.getElementById('scan-button');
                                if (scanButton) {
                                    scanButton.disabled = false;
                                }
                            };
                            reader.readAsDataURL(file);
                        }
                        
                        // Initialize CleanFileUploader if it exists but isn't initialized
                        if (window.CleanFileUploader && typeof window.CleanFileUploader.init === 'function') {
                            if (!window.cleanFileUploaderInitialized) {
                                console.log('[UploadFix] Initializing CleanFileUploader');
                                window.CleanFileUploader.init();
                                window.cleanFileUploaderInitialized = true;
                            }
                        }
                    }
                }, true); // Use capture for highest priority
            }
        }
        
        // Setup the scan button to properly trigger submission
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('[UploadFix] Scan button clicked, marking as intentional submission');
                window.intentionalFormSubmit = true;
                
                // Use CleanFileUploader if available
                if (window.CleanFileUploader && typeof window.CleanFileUploader.upload === 'function') {
                    window.CleanFileUploader.upload();
                } else {
                    // Direct form submission as fallback
                    if (ticketForm) {
                        window.intentionalFormSubmit = true;
                        ticketForm.submit();
                    }
                }
            });
        }
        
        console.log('[UploadFix] File upload fix fully initialized');
    });
})();