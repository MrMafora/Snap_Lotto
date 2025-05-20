/**
 * Improved file input handler specifically for the ticket scanner
 * Fixes issue where users need to click twice to select an image
 */
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('ticket-image');
    const fileSelectBtn = document.getElementById('file-select-btn');
    const previewContainer = document.getElementById('preview-container');
    const ticketPreview = document.getElementById('ticket-preview');
    
    if (fileSelectBtn && fileInput) {
        fileSelectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fileInput.click();
        });
    }
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files && fileInput.files[0]) {
                // Display the selected image preview
                if (previewContainer && ticketPreview) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        ticketPreview.src = e.target.result;
                        previewContainer.classList.remove('d-none');
                    };
                    reader.readAsDataURL(fileInput.files[0]);
                }
            }
        });
    }
});