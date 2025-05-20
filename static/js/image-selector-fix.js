/**
 * Enhanced File Input Fix for Ticket Scanner
 * 
 * This script improves the file selection functionality for the ticket scanner,
 * making it work properly without requiring a backend form submission.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Core elements
    const fileInput = document.getElementById('ticket-image');
    const fileSelectBtn = document.getElementById('file-select-btn');
    const previewContainer = document.getElementById('preview-container');
    const ticketPreview = document.getElementById('ticket-preview');
    const removeImageBtn = document.getElementById('remove-image');
    
    // Make sure the button triggers the file input
    if (fileSelectBtn && fileInput) {
        fileSelectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fileInput.click();
            console.log('File input activated');
        });
    }
    
    // Handle file selection
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files && fileInput.files[0]) {
                const file = fileInput.files[0];
                console.log('File selected:', file.name);
                
                // Show preview if elements exist
                if (previewContainer && ticketPreview) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        ticketPreview.src = e.target.result;
                        previewContainer.classList.remove('d-none');
                        console.log('Preview shown');
                    };
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    }
    
    // Handle image removal
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            if (fileInput) {
                fileInput.value = '';
            }
            
            if (previewContainer) {
                previewContainer.classList.add('d-none');
            }
            
            if (ticketPreview) {
                ticketPreview.src = '';
            }
            
            console.log('Image removed');
        });
    }
    
    // Initialize
    console.log('Image selector fix loaded and active');
});