/**
 * Clean File Uploader
 * A completely rebuilt file upload system that handles all aspects of file selection,
 * preview, and submission without any conflicts or dependencies on other scripts.
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        debug: true,
        formId: 'ticket-form',
        fileInputId: 'ticket-image',
        fileSelectBtnId: 'file-select-btn',
        scanBtnId: 'scan-button',
        previewContainerId: 'preview-container',
        previewImageId: 'ticket-preview',
        removeImageBtnId: 'remove-image',
        dropAreaId: 'drop-area',
        loadingIndicatorId: 'scanner-loading',
        resultContainerId: 'results-container'
    };

    // State object to track current uploader state
    let state = {
        hasFile: false,
        fileObject: null,
        isUploading: false,
        isPreviewVisible: false
    };

    // Element references
    let elements = {};

    // Debug logging helper
    function log(message, data) {
        if (CONFIG.debug) {
            const timestamp = new Date().toISOString();
            if (data !== undefined) {
                console.log(`[${timestamp}] CleanUploader: ${message}`, data);
            } else {
                console.log(`[${timestamp}] CleanUploader: ${message}`);
            }
        }
    }

    // Error logging - always show errors
    function error(message, err) {
        console.error(`CleanUploader ERROR: ${message}`, err);
    }

    // Initialize when the DOM is ready
    document.addEventListener('DOMContentLoaded', initialize);

    // Main initialization function
    function initialize() {
        log('Initializing Clean File Uploader');
        
        // Cache all required DOM elements
        cacheElements();
        
        // Set up all event handlers
        setupEventHandlers();

        // Initialize controls state
        updateControlState();
        
        // Make the uploader functions available globally
        window.CleanFileUploader = {
            selectFile: () => {
                if (elements.fileInput) elements.fileInput.click();
            },
            removeFile: removeFile,
            submitForm: submitForm,
            getState: () => ({...state}),
            // For integration with ad system
            beginImageProcessing: function() {
                // This can be called by the ad system when it's ready to submit the form
                if (state.hasFile && !state.isUploading) {
                    submitForm();
                    return true;
                }
                return false;
            }
        };
        
        log('Clean File Uploader initialized successfully');
    }

    // Cache references to all required DOM elements
    function cacheElements() {
        elements.form = document.getElementById(CONFIG.formId);
        elements.fileInput = document.getElementById(CONFIG.fileInputId);
        elements.fileSelectBtn = document.getElementById(CONFIG.fileSelectBtnId);
        elements.scanBtn = document.getElementById(CONFIG.scanBtnId);
        elements.previewContainer = document.getElementById(CONFIG.previewContainerId);
        elements.previewImage = document.getElementById(CONFIG.previewImageId);
        elements.removeImageBtn = document.getElementById(CONFIG.removeImageBtnId);
        elements.dropArea = document.getElementById(CONFIG.dropAreaId);
        elements.loadingIndicator = document.getElementById(CONFIG.loadingIndicatorId);
        elements.resultContainer = document.getElementById(CONFIG.resultContainerId);
        
        log('Elements cached:', Object.keys(elements).filter(k => elements[k] !== null));
    }

    // Set up all event handlers
    function setupEventHandlers() {
        // File select button - trigger file input click
        if (elements.fileSelectBtn) {
            elements.fileSelectBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (elements.fileInput) {
                    elements.fileInput.click();
                }
            });
            log('File select button handler attached');
        }
        
        // File input change - process selected file
        if (elements.fileInput) {
            elements.fileInput.addEventListener('change', handleFileSelected);
            log('File input change handler attached');
        }
        
        // Remove image button
        if (elements.removeImageBtn) {
            elements.removeImageBtn.addEventListener('click', function(e) {
                e.preventDefault();
                removeFile();
            });
            log('Remove image button handler attached');
        }
        
        // Form submission
        if (elements.form) {
            elements.form.addEventListener('submit', function(e) {
                e.preventDefault();
                if (state.hasFile) {
                    submitForm();
                } else {
                    alert('Please select an image first.');
                }
                return false;
            });
            log('Form submit handler attached');
        }
        
        // Scan button
        if (elements.scanBtn) {
            elements.scanBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (state.hasFile) {
                    submitForm();
                } else {
                    alert('Please select an image first.');
                }
                return false;
            });
            log('Scan button handler attached');
        }
        
        // File drop handling
        if (elements.dropArea) {
            elements.dropArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.add('highlight');
            });
            
            elements.dropArea.addEventListener('dragleave', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.remove('highlight');
            });
            
            elements.dropArea.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.remove('highlight');
                
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    handleFile(e.dataTransfer.files[0]);
                }
            });
            
            log('Drop area handlers attached');
        }
    }

    // Handle selected file from file input
    function handleFileSelected(e) {
        if (e.target.files && e.target.files.length > 0) {
            log('File selected via input:', e.target.files[0].name);
            handleFile(e.target.files[0]);
        }
    }

    // Process a file (from any source)
    function handleFile(file) {
        // Validate the file
        if (!validateFile(file)) {
            return;
        }
        
        // Store the file in state
        state.fileObject = file;
        state.hasFile = true;
        
        // Create preview
        createPreview(file);
        
        // Update UI elements
        updateControlState();
        
        log('File processed successfully:', file.name);
    }

    // Validate file type and size
    function validateFile(file) {
        // Check if it's an image file
        if (!file.type.startsWith('image/')) {
            error('Invalid file type:', file.type);
            alert('Please select an image file (JPEG, PNG, etc).');
            return false;
        }
        
        // Check file size (max 10MB)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            error('File too large:', file.size);
            alert('File is too large. Maximum size is 10MB.');
            return false;
        }
        
        return true;
    }

    // Create image preview
    function createPreview(file) {
        if (!elements.previewImage) {
            error('Preview image element not found');
            return;
        }
        
        const reader = new FileReader();
        
        reader.onload = function(e) {
            elements.previewImage.src = e.target.result;
            
            // Show preview container
            if (elements.previewContainer) {
                elements.previewContainer.classList.remove('d-none');
                state.isPreviewVisible = true;
            }
            
            // Hide drop area
            if (elements.dropArea) {
                elements.dropArea.style.display = 'none';
            }
            
            log('Image preview created');
        };
        
        reader.onerror = function() {
            error('Error reading file for preview');
            alert('Error creating preview. Please try another image.');
        };
        
        reader.readAsDataURL(file);
    }

    // Remove selected file
    function removeFile() {
        // Clear file input
        if (elements.fileInput) {
            elements.fileInput.value = '';
        }
        
        // Hide preview
        if (elements.previewContainer) {
            elements.previewContainer.classList.add('d-none');
            state.isPreviewVisible = false;
        }
        
        // Show drop area
        if (elements.dropArea) {
            elements.dropArea.style.display = 'block';
        }
        
        // Reset state
        state.fileObject = null;
        state.hasFile = false;
        
        // Update UI
        updateControlState();
        
        log('File removed');
    }

    // Update UI control states based on current state
    function updateControlState() {
        // Enable/disable scan button
        if (elements.scanBtn) {
            elements.scanBtn.disabled = !state.hasFile;
        }
        
        // Show/hide remove button
        if (elements.removeImageBtn) {
            elements.removeImageBtn.style.display = state.hasFile ? 'inline-block' : 'none';
        }
    }

    // Submit the form with the file
    function submitForm() {
        if (!state.hasFile || !state.fileObject) {
            error('Cannot submit form - no file selected');
            alert('Please select an image first.');
            return;
        }
        
        // Prevent multiple submissions
        if (state.isUploading) {
            log('Upload already in progress, ignoring duplicate submission');
            return;
        }
        
        log('Submitting form with file:', state.fileObject.name);
        
        // Update state
        state.isUploading = true;
        
        // Show loading indicator
        if (elements.loadingIndicator) {
            elements.loadingIndicator.style.display = 'block';
        }
        
        // Create FormData from form
        const formData = new FormData(elements.form);
        
        // Ensure the file is correctly added to FormData
        // First remove any existing file entry
        formData.delete(CONFIG.fileInputId);
        // Then add the file with the correct field name
        formData.append('ticket_image', state.fileObject);
        
        // Log form data for debugging
        if (CONFIG.debug) {
            log('Form data entries:');
            for (const pair of formData.entries()) {
                log(`- ${pair[0]}: ${pair[1] instanceof File ? pair[1].name : pair[1]}`);
            }
        }
        
        // Get CSRF token if available
        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
        
        // Send the request
        fetch(elements.form.action || '/scan-ticket', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken || ''
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            log('Form submission successful, response:', data);
            
            // Store results data for later use
            window.lastResultsData = data;
            
            // Check if we have DualAdManager for handling the ads
            if (window.DualAdManager) {
                log('Using DualAdManager to display results with ads');
                
                // Start with the public service ad
                window.DualAdManager.showPublicServiceAd();
                
                // Schedule the monetization ad after the public service ad is done
                // (DualAdManager handles this timing internally)
            } else {
                // Handle results display directly if no ad manager
                displayResults(data);
            }
        })
        .catch(err => {
            error('Error submitting form:', err.message);
            
            // Hide loading indicator
            if (elements.loadingIndicator) {
                elements.loadingIndicator.style.display = 'none';
            }
            
            // Reset state
            state.isUploading = false;
            
            // Show error message
            alert(`Error uploading image: ${err.message}`);
        });
    }

    // Display results directly (when not using ad manager)
    function displayResults(data) {
        // Hide loading indicator
        if (elements.loadingIndicator) {
            elements.loadingIndicator.style.display = 'none';
        }
        
        // Reset upload state
        state.isUploading = false;
        
        // Display results in results container
        if (elements.resultContainer) {
            // This would typically be more complex with template rendering
            elements.resultContainer.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            elements.resultContainer.style.display = 'block';
        }
        
        log('Results displayed');
    }

    // This function can be called by DualAdManager when view results is clicked
    window.showTicketResults = function() {
        if (window.lastResultsData) {
            displayResults(window.lastResultsData);
        } else {
            error('No results data available to display');
        }
    };
})();