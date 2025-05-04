/**
 * Direct Button Fix
 * A last-resort, guaranteed solution for the file select button functionality
 * This script applies a direct, focused fix for the Select Image button without 
 * interfering with any other components
 */

// Use setTimeout to ensure this runs after all other scripts
setTimeout(function() {
    console.log("[DirectButtonFix] Initializing direct button fix");
    
    // Utility to check and reset file dialog state if needed
    function ensureFileDialogReady() {
        // Always reset the file dialog state to ensure the button works
        if (window.fileDialogState && window.fileDialogState.isSelectingFile) {
            console.log("[DirectButtonFix] Resetting stuck file dialog state");
            window.fileDialogState.isSelectingFile = false;
            window.fileDialogState.lastDialogTime = 0;
        }
    }
    
    // Find the select button and file input
    const fileSelectBtn = document.getElementById('file-select-btn');
    const fileInput = document.getElementById('ticket-image');
    
    if (fileSelectBtn && fileInput) {
        console.log("[DirectButtonFix] Found file select button and file input");
        
        // Store original button to restore if needed
        const originalButton = fileSelectBtn.cloneNode(true);
        
        // Create completely new button to replace the original
        const newButton = document.createElement('button');
        newButton.id = 'file-select-btn';
        newButton.className = fileSelectBtn.className; // Copy all classes
        newButton.type = 'button';
        newButton.innerHTML = fileSelectBtn.innerHTML;
        
        // Apply a dedicated, isolated click handler
        newButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Always reset file dialog state before clicking
            ensureFileDialogReady();
            
            console.log("[DirectButtonFix] Button clicked, directly triggering file input");
            
            // Use direct DOM method call instead of the .click() method that might be intercepted
            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            fileInput.dispatchEvent(clickEvent);
            
            // Return false to prevent any other handlers
            return false;
        });
        
        // Replace the original button if possible
        if (fileSelectBtn.parentNode) {
            console.log("[DirectButtonFix] Replacing button with enhanced version");
            fileSelectBtn.parentNode.replaceChild(newButton, fileSelectBtn);
        }
        
        // Also add a global emergency reset function
        window.emergencyResetFileInput = function() {
            console.log("[DirectButtonFix] Emergency reset requested");
            ensureFileDialogReady();
            
            // If our button is somehow broken, restore the original
            const currentBtn = document.getElementById('file-select-btn');
            if (currentBtn && currentBtn.parentNode) {
                currentBtn.parentNode.replaceChild(originalButton, currentBtn);
                console.log("[DirectButtonFix] Original button restored");
            }
            
            return "Emergency reset complete";
        };
        
        console.log("[DirectButtonFix] Direct button fix successfully applied");
    } else {
        console.error("[DirectButtonFix] Could not find file select button or file input");
    }
}, 1000); // Run after 1 second to ensure DOM is fully loaded and all other scripts have run