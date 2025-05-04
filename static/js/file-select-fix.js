/**
 * File Selection Button Fix
 * This script ensures the "Select Image" button always works regardless of other script issues
 * It adds redundant attachment of the click handler for the file select button
 */

(function() {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('File Selection Button Fixer activated');
        
        // Main initialization function
        function initFileSelectFix() {
            // Get references to the important elements
            const fileSelectBtn = document.getElementById('file-select-btn');
            const fileInput = document.getElementById('ticket-image');
            
            // If elements don't exist, there's nothing to fix
            if (!fileSelectBtn || !fileInput) {
                console.log('File selection elements not found, nothing to fix');
                return;
            }
            
            console.log('Found file selection elements, applying fix');
            
            // Remove previous click listeners to avoid duplications
            const newFileSelectBtn = fileSelectBtn.cloneNode(true);
            if (fileSelectBtn.parentNode) {
                fileSelectBtn.parentNode.replaceChild(newFileSelectBtn, fileSelectBtn);
                
                // Add our strong direct click handler
                newFileSelectBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('File select button clicked, triggering file input');
                    
                    // Directly trigger the file input click
                    fileInput.click();
                    
                    return false;
                });
                
                console.log('File select button handler successfully attached');
            }
            
            // Also add a direct click handler to the drop area as a backup
            const dropArea = document.getElementById('drop-area');
            if (dropArea) {
                dropArea.addEventListener('click', function(e) {
                    // Only trigger if click is directly on the drop area (not on buttons)
                    if (e.target === dropArea || e.target.tagName !== 'BUTTON') {
                        console.log('Drop area clicked, triggering file input');
                        fileInput.click();
                    }
                });
            }
            
            // Debug helpers - check element state periodically
            setInterval(function() {
                const currentFileSelectBtn = document.getElementById('file-select-btn');
                if (currentFileSelectBtn) {
                    const styles = window.getComputedStyle(currentFileSelectBtn);
                    const isClickable = styles.pointerEvents !== 'none' && 
                                      !currentFileSelectBtn.disabled &&
                                      styles.display !== 'none' &&
                                      styles.visibility !== 'hidden';
                    
                    if (!isClickable) {
                        console.log('File select button is not fully clickable, fixing...');
                        currentFileSelectBtn.disabled = false;
                        currentFileSelectBtn.style.pointerEvents = 'auto';
                        currentFileSelectBtn.style.cursor = 'pointer';
                        currentFileSelectBtn.style.opacity = '1';
                    }
                }
            }, 1000);
        }
        
        // Initialize the fix
        initFileSelectFix();
        
        // Also initialize after a short delay to ensure all other scripts have run
        setTimeout(initFileSelectFix, 500);
    });
})();