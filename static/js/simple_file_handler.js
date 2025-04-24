// Simple File Handler Script
// Provides reliable and concise file upload functionality

function initSimpleFileHandler() {
    console.log("Initializing Simple File Handler");
    
    // Basic DOM elements
    const fileInput = document.getElementById('ticket-image');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('ticket-preview');
    const removeBtn = document.getElementById('remove-image');
    const dropArea = document.getElementById('drop-area');
    
    // Hide results on page load
    hideResultsOnLoad();
    
    // File input change handler
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                handleSelectedFile(file);
            }
        });
    }
    
    // Remove image button
    if (removeBtn) {
        removeBtn.addEventListener('click', function() {
            if (fileInput) fileInput.value = '';
            if (previewImage) previewImage.src = '';
            if (previewContainer) previewContainer.classList.add('d-none');
        });
    }
    
    // Drag and drop functionality
    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
            dropArea.addEventListener(event, function(e) {
                e.preventDefault();
                e.stopPropagation();
            });
        });
        
        ['dragenter', 'dragover'].forEach(event => {
            dropArea.addEventListener(event, function() {
                dropArea.classList.add('highlight');
            });
        });
        
        ['dragleave', 'drop'].forEach(event => {
            dropArea.addEventListener(event, function() {
                dropArea.classList.remove('highlight');
            });
        });
        
        dropArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const file = dt.files[0];
            
            if (file) {
                fileInput.files = dt.files;
                handleSelectedFile(file);
            }
        });
    }
    
    // Process selected file
    function handleSelectedFile(file) {
        // Verify it's an image
        if (!file.type.match('image.*')) {
            alert('Please select an image file');
            if (fileInput) fileInput.value = '';
            return;
        }
        
        console.log(`File selected: ${file.name} (${file.type})`);
        
        // Read and show preview
        const reader = new FileReader();
        
        reader.onload = function(e) {
            if (previewImage) {
                previewImage.src = e.target.result;
                console.log("Preview image loaded successfully");
            }
            
            if (previewContainer) {
                previewContainer.classList.remove('d-none');
                console.log("Preview container shown");
            }
        };
        
        reader.onerror = function() {
            console.error("Error reading file");
            alert('Error reading the image. Please try another file.');
            if (fileInput) fileInput.value = '';
        };
        
        console.log("Reading file as data URL");
        reader.readAsDataURL(file);
    }
    
    // Hide all results on page load
    function hideResultsOnLoad() {
        // Result containers to hide
        const containers = [
            'results-container',
            'fixed-results-wrapper',
            'error-message',
            'success-content',
            'prize-container',
            'no-prize-container'
        ];
        
        containers.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.add('d-none');
                el.style.display = 'none';
                console.log(`Hidden container: ${id}`);
            }
        });
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    initSimpleFileHandler();
});