/**
 * Clean File Uploader
 * A standalone, dependency-free file uploader with robust error handling
 * and progress tracking for the Snap Lotto Ticket Scanner
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        acceptedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/heic'],
        maxFileSizeMB: 10,
        endpoint: '/scan-ticket',
        debug: true,
        processingTimeout: 60000, // 60 seconds
        previewWidth: 300,
        previewHeight: 200
    };
    
    // DOM elements - will be populated in init()
    let elements = {
        form: null,
        fileInput: null, 
        fileSelectBtn: null,
        dropArea: null,
        previewContainer: null,
        previewImage: null,
        removeBtn: null,
        scanBtn: null,
        progressContainer: null,
        progressBar: null,
        errorContainer: null
    };
    
    // State management
    let state = {
        fileSelected: false,
        uploading: false,
        processing: false,
        currentFile: null,
        uploadProgress: 0,
        csrfToken: null,
        formSubmitHandler: null
    };
    
    // Utility functions
    function log(message, data) {
        if (config.debug) {
            if (data) {
                console.log(`[CleanFileUploader] ${message}`, data);
            } else {
                console.log(`[CleanFileUploader] ${message}`);
            }
        }
    }
    
    function error(message, data) {
        if (data) {
            console.error(`[CleanFileUploader] ERROR: ${message}`, data);
        } else {
            console.error(`[CleanFileUploader] ERROR: ${message}`);
        }
    }
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' bytes';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }
    
    // Event handlers and core functionality
    function handleFileSelect(e) {
        const files = e.target?.files || e.dataTransfer?.files;
        
        if (!files || files.length === 0) {
            log('No files selected');
            return;
        }
        
        const file = files[0];
        log('File selected:', file.name);
        
        // Validate file type
        if (!config.acceptedTypes.includes(file.type) && 
            !(file.name.toLowerCase().endsWith('.heic') && config.acceptedTypes.includes('image/heic'))) {
            showError(`Invalid file type. Please select one of the following: ${config.acceptedTypes.map(t => t.replace('image/', '')).join(', ')}`);
            clearFileInput();
            return;
        }
        
        // Validate file size
        if (file.size > config.maxFileSizeMB * 1024 * 1024) {
            showError(`File is too large. Maximum file size is ${config.maxFileSizeMB}MB.`);
            clearFileInput();
            return;
        }
        
        // Update state and UI
        state.fileSelected = true;
        state.currentFile = file;
        hideError();
        
        // Generate and show preview
        generatePreview(file);
        
        // Update UI states
        if (elements.dropArea) elements.dropArea.style.display = 'none';
        if (elements.previewContainer) elements.previewContainer.classList.remove('d-none');
        if (elements.scanBtn) elements.scanBtn.disabled = false;
        
        log('File selected and validated');
    }
    
    function generatePreview(file) {
        if (!elements.previewImage) return;
        
        const reader = new FileReader();
        
        reader.onload = function(e) {
            elements.previewImage.src = e.target.result;
            log('Preview generated');
        };
        
        reader.onerror = function() {
            error('Failed to generate preview');
            elements.previewImage.src = ''; // Clear preview on error
        };
        
        reader.readAsDataURL(file);
    }
    
    function removeFile() {
        log('Removing file');
        
        // Reset state
        state.fileSelected = false;
        state.currentFile = null;
        
        // Reset UI
        clearFileInput();
        if (elements.previewImage) elements.previewImage.src = '';
        if (elements.previewContainer) elements.previewContainer.classList.add('d-none');
        if (elements.dropArea) elements.dropArea.style.display = 'block';
        if (elements.scanBtn) elements.scanBtn.disabled = true;
        if (elements.progressContainer) elements.progressContainer.classList.add('d-none');
        if (elements.progressBar) elements.progressBar.style.width = '0%';
        
        hideError();
    }
    
    function clearFileInput() {
        if (elements.fileInput) {
            try {
                elements.fileInput.value = '';
                
                // For IE/Edge (if needed)
                if (elements.fileInput.value) {
                    // Create a form and reset it to clear the input
                    const form = document.createElement('form');
                    form.appendChild(elements.fileInput.cloneNode(true));
                    form.reset();
                    elements.fileInput.parentNode.replaceChild(form.firstChild, elements.fileInput);
                    elements.fileInput = form.firstChild;
                }
            } catch (e) {
                error('Failed to clear file input', e);
            }
        }
    }
    
    function showError(message) {
        log('Showing error:', message);
        
        if (elements.errorContainer) {
            elements.errorContainer.textContent = message;
            elements.errorContainer.classList.remove('d-none');
        } else {
            // Fallback to alert if error container doesn't exist
            alert(message);
        }
    }
    
    function hideError() {
        if (elements.errorContainer) {
            elements.errorContainer.textContent = '';
            elements.errorContainer.classList.add('d-none');
        }
    }
    
    function updateProgressBar(percent) {
        state.uploadProgress = percent;
        
        if (elements.progressBar) {
            elements.progressBar.style.width = `${percent}%`;
            elements.progressBar.setAttribute('aria-valuenow', percent);
        }
        
        log(`Upload progress: ${percent}%`);
    }
    
    function uploadFile() {
        if (!state.fileSelected || !state.currentFile) {
            showError('Please select a file first');
            return false;
        }
        
        if (state.uploading) {
            log('Upload already in progress');
            return false;
        }
        
        log('Starting file upload');
        state.uploading = true;
        
        // Show progress
        if (elements.progressContainer) {
            elements.progressContainer.classList.remove('d-none');
        }
        updateProgressBar(0);
        
        // Create FormData
        const formData = new FormData();
        formData.append('ticket_image', state.currentFile);
        
        // Add CSRF token if available
        if (state.csrfToken) {
            formData.append('csrf_token', state.csrfToken);
        }
        
        // Add other form fields if present
        if (elements.form) {
            const formElements = elements.form.elements;
            for (let i = 0; i < formElements.length; i++) {
                const element = formElements[i];
                if (element.name && element.name !== 'ticket_image' && element.name !== 'csrf_token') {
                    formData.append(element.name, element.value);
                }
            }
        }
        
        // Send the AJAX request
        const xhr = new XMLHttpRequest();
        xhr.open('POST', config.endpoint, true);
        
        // Set up event handlers
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                updateProgressBar(percent);
            }
        };
        
        xhr.onload = function() {
            state.uploading = false;
            
            let response;
            try {
                response = JSON.parse(xhr.responseText);
            } catch (e) {
                error('Failed to parse response', e);
                response = { 
                    error: 'Failed to process response from server',
                    details: xhr.responseText.substring(0, 100) + '...' 
                };
            }
            
            if (xhr.status >= 200 && xhr.status < 300) {
                log('Upload successful', response);
                
                // Check if we need to show ads first
                if (window.DualAdManager && typeof window.DualAdManager.showResultsWithAd === 'function') {
                    log('Showing ads before results');
                    window.DualAdManager.showResultsWithAd(response);
                } else {
                    // Handle the response directly
                    handleUploadSuccess(response);
                }
            } else {
                log('Upload failed', response);
                handleUploadError(response.error || 'Failed to upload file');
            }
        };
        
        xhr.onerror = function() {
            state.uploading = false;
            error('Network error during upload');
            handleUploadError('Network error while uploading. Please check your connection and try again.');
        };
        
        xhr.ontimeout = function() {
            state.uploading = false;
            error('Upload timed out');
            handleUploadError('The upload took too long and timed out. Please try again with a smaller file or better connection.');
        };
        
        xhr.send(formData);
        return true;
    }
    
    function handleUploadSuccess(response) {
        log('Processing successful upload response', response);
        
        // Reset upload UI
        if (elements.progressContainer) {
            elements.progressContainer.classList.add('d-none');
        }
        
        // Here we would normally handle displaying the results
        // but this depends on the application's needs
        
        // If there's a global result handler, call it
        if (window.handleTicketScanResults && typeof window.handleTicketScanResults === 'function') {
            window.handleTicketScanResults(response);
        }
        
        // If we have a results container in our config, update it
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            // Render results - this would be customized based on your application's needs
            renderResults(resultsContainer, response);
        }
    }
    
    function handleUploadError(errorMessage) {
        error('Upload error:', errorMessage);
        
        // Reset UI
        if (elements.progressContainer) {
            elements.progressContainer.classList.add('d-none');
        }
        updateProgressBar(0);
        
        // Show error
        showError(errorMessage);
    }
    
    function renderResults(container, data) {
        // This function would be customized based on your application's needs
        if (!container) return;
        
        if (data.success) {
            container.innerHTML = '<div class="alert alert-success">Upload successful! Results will be displayed soon.</div>';
        } else {
            container.innerHTML = `<div class="alert alert-danger">Error: ${data.error || 'Unknown error'}</div>`;
        }
    }
    
    // Main initialization function
    function initialize() {
        log('Initializing CleanFileUploader');
        
        // Cache DOM elements
        elements.form = document.getElementById('ticket-form');
        elements.fileInput = document.getElementById('ticket-image');
        elements.fileSelectBtn = document.getElementById('file-select-btn');
        elements.dropArea = document.getElementById('drop-area');
        elements.previewContainer = document.getElementById('preview-container');
        elements.previewImage = document.getElementById('ticket-preview');
        elements.removeBtn = document.getElementById('remove-image');
        elements.scanBtn = document.getElementById('scan-button');
        
        // Progress elements - create them if they don't exist
        elements.progressContainer = document.getElementById('progress-container');
        if (!elements.progressContainer && elements.form) {
            elements.progressContainer = document.createElement('div');
            elements.progressContainer.id = 'progress-container';
            elements.progressContainer.className = 'd-none mt-3';
            elements.progressContainer.innerHTML = `
                <label class="form-label small">Upload Progress</label>
                <div class="progress" style="height: 10px;">
                    <div id="upload-progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%"></div>
                </div>
            `;
            elements.form.appendChild(elements.progressContainer);
        }
        elements.progressBar = document.getElementById('upload-progress-bar');
        
        // Error container - create it if it doesn't exist
        elements.errorContainer = document.getElementById('error-container');
        if (!elements.errorContainer && elements.form) {
            elements.errorContainer = document.createElement('div');
            elements.errorContainer.id = 'error-container';
            elements.errorContainer.className = 'alert alert-danger d-none mt-3';
            elements.form.appendChild(elements.errorContainer);
        }
        
        // Get CSRF token if available
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            state.csrfToken = csrfInput.value;
        }
        
        // Check for required elements
        if (!elements.fileInput || !elements.form) {
            error('Required elements not found. Make sure you have a form with id "ticket-form" and a file input with id "ticket-image".');
            return;
        }
        
        // Set up event listeners
        setupEventListeners();
        
        // Initialize UI state
        if (elements.scanBtn) {
            elements.scanBtn.disabled = true;
        }
        
        log('CleanFileUploader initialized successfully');
    }
    
    function setupEventListeners() {
        // File input change
        if (elements.fileInput) {
            // Clone to remove any existing listeners
            const newInput = elements.fileInput.cloneNode(true);
            elements.fileInput.parentNode.replaceChild(newInput, elements.fileInput);
            elements.fileInput = newInput;
            
            // Add change listener
            elements.fileInput.addEventListener('change', handleFileSelect);
        }
        
        // File select button
        if (elements.fileSelectBtn) {
            elements.fileSelectBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (elements.fileInput) {
                    elements.fileInput.click();
                }
            });
        }
        
        // Drop area
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
                
                handleFileSelect(e);
            });
            
            // Also make drop area clickable
            elements.dropArea.addEventListener('click', function(e) {
                if (e.target !== elements.fileSelectBtn && !elements.fileSelectBtn.contains(e.target)) {
                    if (elements.fileInput) {
                        elements.fileInput.click();
                    }
                }
            });
        }
        
        // Remove button
        if (elements.removeBtn) {
            elements.removeBtn.addEventListener('click', removeFile);
        }
        
        // Form submission
        if (elements.form) {
            // Store original submit handler if it exists
            state.formSubmitHandler = elements.form.onsubmit;
            
            // Override submit event
            elements.form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                if (!state.fileSelected) {
                    showError('Please select a file first.');
                    return false;
                }
                
                uploadFile();
                return false;
            });
        }
        
        // Scan button
        if (elements.scanBtn) {
            elements.scanBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                if (!state.fileSelected) {
                    showError('Please select a file first.');
                    return false;
                }
                
                uploadFile();
            });
        }
    }
    
    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        // Slight delay to ensure other scripts have loaded
        setTimeout(initialize, 100);
    });
    
    // Expose public API
    window.CleanFileUploader = {
        init: initialize,
        upload: uploadFile,
        removeFile: removeFile,
        selectFile: function() {
            if (elements.fileInput) elements.fileInput.click();
        },
        getState: function() {
            return {...state};
        }
    };
    
    // Self-initialize after a brief delay to allow DOM to fully load
    setTimeout(function() {
        if (!window.cleanFileUploaderInitialized) {
            console.log('[CleanFileUploader] Auto-initializing');
            initialize();
            window.cleanFileUploaderInitialized = true;
        }
    }, 300);
})();