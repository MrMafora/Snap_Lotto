/**
 * Unified Ticket Scanner Handler
 * A complete solution for the ticket scanning functionality that fixes all known issues
 * with file selection, preview, and submission
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        debug: true,
        acceptedImageTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        maxFileSizeMB: 10, // 10MB max file size
        scanEndpoint: '/scan-ticket'
    };
    
    // Debug logger
    function log(message, data) {
        if (config.debug) {
            if (data) {
                console.log(`[UnifiedTicketHandler] ${message}`, data);
            } else {
                console.log(`[UnifiedTicketHandler] ${message}`);
            }
        }
    }
    
    // Error logger - always show errors
    function error(message, data) {
        if (data) {
            console.error(`[UnifiedTicketHandler] ERROR: ${message}`, data);
        } else {
            console.error(`[UnifiedTicketHandler] ERROR: ${message}`);
        }
    }
    
    // State tracking
    let state = {
        fileSelected: false,
        fileProcessing: false,
        fileError: null,
        originalFile: null,
        eventHandlersInitialized: false
    };
    
    // Element references
    let elements = {
        form: null,
        fileInput: null,
        fileSelectBtn: null,
        scanButton: null,
        dropArea: null,
        previewContainer: null,
        previewImage: null,
        removeImageBtn: null,
        loadingIndicator: null,
        errorMessage: null
    };
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', initialize);
    
    // Main initialization function
    function initialize() {
        log('Initializing Unified Ticket Handler');
        
        // Get references to all required elements
        cacheElements();
        
        // If critical elements are missing, stop initialization
        if (!elements.form || !elements.fileInput || !elements.fileSelectBtn) {
            error('Critical elements missing from the page - cannot initialize');
            return;
        }
        
        // Set up all event handlers
        setupEventHandlers();
        
        // Expose public API
        window.UnifiedTicketHandler = {
            selectFile: triggerFileSelection,
            removeFile: removeSelectedFile,
            scanTicket: submitForm,
            getState: () => ({...state})
        };
        
        log('Unified Ticket Handler initialized successfully');
    }
    
    // Cache references to all required elements
    function cacheElements() {
        elements.form = document.getElementById('ticket-form');
        elements.fileInput = document.getElementById('ticket-image');
        elements.fileSelectBtn = document.getElementById('file-select-btn');
        elements.scanButton = document.getElementById('scan-button');
        elements.dropArea = document.getElementById('drop-area');
        elements.previewContainer = document.getElementById('preview-container');
        elements.previewImage = document.getElementById('ticket-preview');
        elements.removeImageBtn = document.getElementById('remove-image');
        elements.loadingIndicator = document.getElementById('scanner-loading');
        elements.errorMessage = document.getElementById('error-message');
        
        if (elements.loadingIndicator) {
            elements.loadingIndicator.style.display = 'none';
        }
        
        log('Elements cached', elements);
    }
    
    // Set up all event handlers
    function setupEventHandlers() {
        if (state.eventHandlersInitialized) {
            log('Event handlers already initialized, skipping');
            return;
        }
        
        // File selection button
        if (elements.fileSelectBtn) {
            // Remove any existing click handlers to avoid conflicts
            const newBtn = elements.fileSelectBtn.cloneNode(true);
            elements.fileSelectBtn.parentNode.replaceChild(newBtn, elements.fileSelectBtn);
            elements.fileSelectBtn = newBtn;
            
            // Add our clean click handler
            elements.fileSelectBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                log('File select button clicked');
                
                triggerFileSelection();
                return false;
            });
            
            log('File select button handler attached');
        }
        
        // File input change
        if (elements.fileInput) {
            // Remove any existing change handlers to avoid conflicts
            const newInput = elements.fileInput.cloneNode(true);
            elements.fileInput.parentNode.replaceChild(newInput, elements.fileInput);
            elements.fileInput = newInput;
            
            // Add our clean change handler
            elements.fileInput.addEventListener('change', handleFileSelected);
            
            log('File input change handler attached');
        }
        
        // Remove image button
        if (elements.removeImageBtn) {
            elements.removeImageBtn.addEventListener('click', removeSelectedFile);
            log('Remove image button handler attached');
        }
        
        // Form submission
        if (elements.form) {
            elements.form.addEventListener('submit', function(e) {
                e.preventDefault();
                log('Form submit event intercepted');
                
                if (!state.fileSelected) {
                    error('Cannot submit form - no file selected');
                    showUserMessage('Please select an image of your lottery ticket.');
                    return false;
                }
                
                submitForm();
                return false;
            });
            
            log('Form submission handler attached');
        }
        
        // Scan button
        if (elements.scanButton) {
            elements.scanButton.addEventListener('click', function(e) {
                e.preventDefault();
                log('Scan button clicked');
                
                if (!state.fileSelected) {
                    error('Cannot scan - no file selected');
                    showUserMessage('Please select an image of your lottery ticket.');
                    return false;
                }
                
                submitForm();
                return false;
            });
            
            log('Scan button handler attached');
        }
        
        // File drop area
        if (elements.dropArea) {
            elements.dropArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.add('dragover');
            });
            
            elements.dropArea.addEventListener('dragleave', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.remove('dragover');
            });
            
            elements.dropArea.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.remove('dragover');
                
                log('File dropped in drop area');
                
                const dt = e.dataTransfer;
                if (dt.files && dt.files.length > 0) {
                    log('Processing dropped file');
                    processFile(dt.files[0]);
                }
            });
            
            log('Drop area handlers attached');
        }
        
        state.eventHandlersInitialized = true;
        log('All event handlers initialized');
    }
    
    // Trigger file selection dialog
    function triggerFileSelection() {
        if (!elements.fileInput) {
            error('Cannot trigger file selection - file input not found');
            return;
        }
        
        log('Triggering file selection dialog');
        elements.fileInput.click();
    }
    
    // Handle file selected event
    function handleFileSelected(e) {
        log('File selection change event triggered');
        
        const files = e.target.files;
        if (!files || files.length === 0) {
            error('No files selected in file input');
            return;
        }
        
        log('File selected, processing', files[0]);
        processFile(files[0]);
    }
    
    // Process the selected file
    function processFile(file) {
        // Reset any previous errors
        state.fileError = null;
        
        // Validate file type
        if (!validateFileType(file)) {
            error(`Invalid file type: ${file.type}`);
            elements.fileInput.value = ''; // Clear the input
            showUserMessage(`Please select a valid image file (JPEG, PNG, GIF, WEBP).`);
            return;
        }
        
        // Validate file size
        if (!validateFileSize(file)) {
            error(`File too large: ${Math.round(file.size / 1024 / 1024)}MB`);
            elements.fileInput.value = ''; // Clear the input
            showUserMessage(`File size exceeds the maximum allowed (${config.maxFileSizeMB}MB).`);
            return;
        }
        
        // File is valid - update state and UI
        state.fileSelected = true;
        state.originalFile = file;
        
        // Create and display preview
        createPreview(file);
        
        log('File successfully processed and validated');
    }
    
    // Validate file type
    function validateFileType(file) {
        return config.acceptedImageTypes.includes(file.type);
    }
    
    // Validate file size
    function validateFileSize(file) {
        const maxSizeBytes = config.maxFileSizeMB * 1024 * 1024;
        return file.size <= maxSizeBytes;
    }
    
    // Create image preview
    function createPreview(file) {
        if (!elements.previewImage) {
            error('Cannot create preview - preview image element not found');
            return;
        }
        
        log('Creating file preview');
        
        const reader = new FileReader();
        
        reader.onload = function(e) {
            log('File read complete, updating preview');
            
            // Set the preview image source
            elements.previewImage.src = e.target.result;
            
            // Show the preview container
            if (elements.previewContainer) {
                elements.previewContainer.classList.remove('d-none');
                log('Preview container now visible');
            }
            
            // Hide the drop area
            if (elements.dropArea) {
                elements.dropArea.style.display = 'none';
                log('Drop area now hidden');
            }
        };
        
        reader.onerror = function() {
            error('Error reading file for preview');
            showUserMessage('Error reading the selected file. Please try another image.');
            
            // Clear the file input
            if (elements.fileInput) {
                elements.fileInput.value = '';
            }
            
            // Reset state
            state.fileSelected = false;
            state.originalFile = null;
        };
        
        // Read the file as data URL for preview
        reader.readAsDataURL(file);
    }
    
    // Remove the selected file
    function removeSelectedFile() {
        log('Removing selected file');
        
        // Clear the file input
        if (elements.fileInput) {
            elements.fileInput.value = '';
        }
        
        // Hide the preview
        if (elements.previewContainer) {
            elements.previewContainer.classList.add('d-none');
        }
        
        // Show the drop area
        if (elements.dropArea) {
            elements.dropArea.style.display = 'block';
        }
        
        // Reset state
        state.fileSelected = false;
        state.originalFile = null;
        
        log('Selected file removed');
    }
    
    // Display user-friendly message
    function showUserMessage(message) {
        // First try to use alert (simplest approach)
        alert(message);
    }
    
    // Submit the form with the file
    function submitForm() {
        if (!state.fileSelected || !state.originalFile) {
            error('Cannot submit form - no file selected');
            showUserMessage('Please select an image of your lottery ticket.');
            return;
        }
        
        log('Preparing to submit form with file:', state.originalFile);
        
        // Show loading indicator
        if (elements.loadingIndicator) {
            elements.loadingIndicator.style.display = 'block';
        }
        
        // Mark as processing
        state.fileProcessing = true;
        
        // If we have the DualAdManager, use it to handle the ad display
        if (window.DualAdManager) {
            log('Using DualAdManager for form submission');
            
            // Create a connection between DualAdManager and UnifiedTicketHandler
            if (!window.DualAdManager.originalProcessTicket) {
                // Save the original processTicketWithAds function
                window.DualAdManager.originalProcessTicket = window.DualAdManager.processTicketWithAds;
                
                // Replace it with our enhanced version
                window.DualAdManager.processTicketWithAds = function() {
                    log('Enhanced ticket processing through DualAdManager');
                    
                    // Start with showing the public service ad
                    window.DualAdManager.showPublicServiceAd();
                    
                    // Get file data from our unified handler
                    const fileData = elements.fileInput.files[0];
                    if (!fileData) {
                        log('ERROR: No file data available when processing with DualAdManager');
                        alert('Please select an image of your lottery ticket');
                        return;
                    }
                    
                    // Store file for later use by DualAdManager
                    window.lastSelectedTicketFile = fileData;
                    log('Stored file data for DualAdManager:', fileData.name);
                };
            }
            
            // Trigger the ad display and submission process
            DualAdManager.processTicketWithAds();
        } else {
            // Otherwise handle submission ourselves
            log('DualAdManager not available, handling submission directly');
            submitFormWithAjax();
        }
    }
    
    // Submit the form via AJAX
    function submitFormWithAjax() {
        log('Submitting form with AJAX');
        
        if (!elements.form) {
            error('Cannot submit - form element not found');
            if (elements.loadingIndicator) {
                elements.loadingIndicator.style.display = 'none';
            }
            return;
        }
        
        // Create a FormData object
        const formData = new FormData(elements.form);
        
        // Ensure the file is included in the FormData
        if (state.originalFile && elements.fileInput.files.length === 0) {
            log('Manually adding file to FormData');
            formData.delete('ticket_image'); // Remove any empty file entries
            formData.append('ticket_image', state.originalFile);
        }
        
        // Log all form data for debugging
        if (config.debug) {
            log('Form data contents:');
            for (const pair of formData.entries()) {
                log(`- ${pair[0]}: ${pair[1] instanceof File ? pair[1].name : pair[1]}`);
            }
        }
        
        // Get CSRF token
        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
        
        // Send the request
        fetch(elements.form.action || config.scanEndpoint, {
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
            
            // Store results for display
            window.lastResultsData = data;
            
            // If DualAdManager not handling the UI, we need to show results
            if (!window.DualAdManager) {
                displayResults(data);
            }
        })
        .catch(err => {
            error('Error submitting form:', err);
            
            // If DualAdManager not handling the UI, show error
            if (!window.DualAdManager) {
                if (elements.loadingIndicator) {
                    elements.loadingIndicator.style.display = 'none';
                }
                
                showUserMessage(`Error scanning ticket: ${err.message}`);
            }
        })
        .finally(() => {
            // Reset processing state
            state.fileProcessing = false;
        });
    }
    
    // Display results (if not using DualAdManager)
    function displayResults(data) {
        log('Displaying results directly');
        
        // Hide loading indicator
        if (elements.loadingIndicator) {
            elements.loadingIndicator.style.display = 'none';
        }
        
        // This would be implemented based on your specific UI
        // For now, we'll use the existing results display code if available
        if (typeof handleTicketResults === 'function') {
            log('Using existing handleTicketResults function');
            handleTicketResults(data);
        } else {
            log('No results handler available');
            
            // Basic results display
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.classList.remove('d-none');
                
                // Check for success/error in response
                if (data.error) {
                    showUserMessage(`Error: ${data.error}`);
                } else {
                    showUserMessage('Ticket scanned successfully! See results below.');
                }
            }
        }
    }
})();