/**
 * File Selection Button Fix
 * This script ensures the "Select Image" button always works regardless of other script issues
 * It adds proper handling for file selection, including preview functionality
 */

(function() {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Complete File Selection Fix activated (v2.0)');
        
        // Main initialization function
        function initFileSelectFix() {
            // Get references to the important elements
            const fileSelectBtn = document.getElementById('file-select-btn');
            const fileInput = document.getElementById('ticket-image');
            const previewContainer = document.getElementById('preview-container');
            const ticketPreview = document.getElementById('ticket-preview');
            const ticketForm = document.getElementById('ticket-form');
            
            // If essential elements don't exist, there's nothing to fix
            if (!fileSelectBtn || !fileInput) {
                console.log('File selection elements not found, nothing to fix');
                return;
            }
            
            console.log('Found file selection elements, applying complete image handling fix');
            
            // CRITICAL FIX: Override form submission to prevent redirect on file selection
            if (ticketForm) {
                // Backup the original submission handler if it exists
                if (typeof window.originalSubmitHandler !== 'function') {
                    window.originalSubmitHandler = ticketForm.onsubmit;
                }
                
                // Create a controlled form submission handler
                ticketForm.onsubmit = function(e) {
                    // Prevent default form submission behavior 
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Only actually submit the form when explicitly triggered
                    if (window.intentionalFormSubmit === true) {
                        console.log('Intentional form submission detected, proceeding with scan');
                        window.intentionalFormSubmit = false;
                        
                        // Call the original handler if available
                        if (typeof window.originalSubmitHandler === 'function') {
                            return window.originalSubmitHandler.call(this, e);
                        }
                    } else {
                        console.log('Prevented automatic form submission, not scanning yet');
                    }
                    
                    return false;
                };
            }
            
            // CRITICAL FIX: Create a proper file selection handler function
            function handleImageSelection(e) {
                console.log('File input change event triggered');
                const file = fileInput.files[0];
                
                if (file) {
                    // Check if file is an image
                    if (!file.type.match('image.*')) {
                        alert('Please select an image file');
                        fileInput.value = ''; // Clear the file input
                        return;
                    }
                    
                    console.log('Valid image file selected:', file.name);
                    
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        console.log('File read successfully, updating preview');
                        if (ticketPreview) {
                            ticketPreview.src = e.target.result;
                            console.log('Preview image source updated');
                            
                            // Show the preview container if it exists
                            if (previewContainer) {
                                previewContainer.classList.remove('d-none');
                                console.log('Preview container now visible');
                            }
                            
                            // Update scan button state if the function exists
                            if (typeof updateScanButton === 'function') {
                                updateScanButton();
                            }
                        } else {
                            console.error('Ticket preview element not found');
                        }
                    };
                    
                    reader.onerror = function() {
                        console.error('Error reading file:', file.name);
                        alert('Error reading the image file. Please try a different image.');
                        fileInput.value = ''; // Clear the file input on error
                    };
                    
                    // Read the file as a data URL
                    console.log('Starting file read operation');
                    reader.readAsDataURL(file);
                } else {
                    console.log('No file selected');
                    if (previewContainer) {
                        previewContainer.classList.add('d-none');
                    }
                    
                    // Update scan button state if the function exists
                    if (typeof updateScanButton === 'function') {
                        updateScanButton();
                    }
                }
            }
            
            // CRITICAL FIX: Add a robust change handler to the file input
            if (fileInput) {
                // Remove existing event listeners to avoid conflicts
                const newFileInput = fileInput.cloneNode(true);
                if (fileInput.parentNode) {
                    fileInput.parentNode.replaceChild(newFileInput, fileInput);
                    
                    // Add our enhanced change handler
                    newFileInput.addEventListener('change', handleImageSelection);
                    console.log('Enhanced file input change handler attached');
                    
                    // Store reference to new file input for later use
                    window.fixedFileInput = newFileInput;
                }
            }
            
            // CRITICAL FIX: Ensure the select button works correctly
            if (fileSelectBtn) {
                // Clone to remove any problematic event listeners
                const newFileSelectBtn = fileSelectBtn.cloneNode(true);
                if (fileSelectBtn.parentNode) {
                    fileSelectBtn.parentNode.replaceChild(newFileSelectBtn, fileSelectBtn);
                    
                    // Add our improved click handler
                    newFileSelectBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('File select button clicked, triggering file input');
                        
                        // Use the stored fixed file input reference if available, otherwise fall back to original
                        const inputToClick = window.fixedFileInput || fileInput;
                        console.log('Clicking on file input element:', inputToClick ? 'Found' : 'Not found');
                        if (inputToClick) {
                            inputToClick.click();
                        } else {
                            console.error('Cannot find file input element to click');
                        }
                        
                        return false;
                    });
                    
                    console.log('Enhanced file select button handler attached');
                }
            }
            
            // CRITICAL FIX: Make the actual scan button trigger the form submission properly
            const scanButton = document.getElementById('scan-button');
            if (scanButton) {
                scanButton.addEventListener('click', function(e) {
                    console.log('Scan button clicked, marking as intentional submission');
                    window.intentionalFormSubmit = true;
                });
            }
            
            console.log('Complete file selection fix applied successfully');
        }
        
        // Initialize right away
        initFileSelectFix();
        
        // Add a global helper function that can be called from anywhere
        window.openFileSelector = function() {
            const fileInput = document.getElementById('ticket-image');
            if (fileInput) {
                console.log('Direct file selector opened via global helper');
                fileInput.click();
                return true;
            }
            return false;
        };
        
        // Add a direct click handler to the document that will work as a fallback
        // This ensures redundant functionality in case our main fixes don't work
        document.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'file-select-btn') {
                console.log('Document-level file select button click detected');
                const fileInput = document.getElementById('ticket-image');
                if (fileInput) {
                    e.preventDefault();
                    e.stopPropagation();
                    fileInput.click();
                    return false;
                }
            }
        }, true); // Use capture phase for maximum reliability
        
        // Also initialize after a delay to ensure all other scripts have run
        setTimeout(initFileSelectFix, 500);
    });
})();