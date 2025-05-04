/**
 * Loop Fix
 * Prevents recursive file dialog loop in ticket scanner
 * This is a critical fix that stops the endless reopening of the file dialog
 */

(function() {
    'use strict';
    
    // Guard variable to prevent recursive triggering
    window.fileDialogState = {
        // Tracks if a file selection is in progress
        isSelectingFile: false,
        // Tracks the last time a file dialog was shown (to prevent rapid reopening)
        lastDialogTime: 0,
        // Minimum time between dialogs in milliseconds
        minDialogInterval: 1000,
        // Debug mode
        debug: true
    };
    
    function log(message) {
        if (window.fileDialogState.debug) {
            console.log(`[LoopFix] ${message}`);
        }
    }
    
    log('Loop fix initialized');
    
    // Intercept all click events to the file input
    const originalClick = HTMLInputElement.prototype.click;
    HTMLInputElement.prototype.click = function() {
        // Only intercept file inputs
        if (this.type === 'file') {
            const now = Date.now();
            const timeSinceLastDialog = now - window.fileDialogState.lastDialogTime;
            
            if (window.fileDialogState.isSelectingFile) {
                log('Prevented recursive file dialog - selection already in progress');
                return false;
            }
            
            if (timeSinceLastDialog < window.fileDialogState.minDialogInterval) {
                log(`Prevented too frequent file dialog (${timeSinceLastDialog}ms since last)`);
                return false;
            }
            
            // Allow this click to proceed
            log('File dialog opened');
            window.fileDialogState.isSelectingFile = true;
            window.fileDialogState.lastDialogTime = now;
            
            // Set a failsafe timeout to reset the state in case the change event doesn't fire
            setTimeout(function() {
                if (window.fileDialogState.isSelectingFile) {
                    log('Failsafe: Resetting file selection state after timeout');
                    window.fileDialogState.isSelectingFile = false;
                }
            }, 5000); // 5 second failsafe
        }
        
        // Call the original click method
        return originalClick.apply(this, arguments);
    };
    
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        // Find all file inputs and add our change handler
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(function(input) {
            // Avoid adding multiple listeners by using a unique marker
            if (!input.hasAttribute('data-loop-fix')) {
                input.setAttribute('data-loop-fix', 'true');
                
                // Add a capture phase listener that runs before other listeners
                input.addEventListener('change', function(e) {
                    log('File selected, resetting selection state');
                    window.fileDialogState.isSelectingFile = false;
                }, true);
            }
        });
        
        // Fix for the ticket-image input specifically
        const ticketImage = document.getElementById('ticket-image');
        if (ticketImage) {
            log('Found ticket-image input, applying specific fix');
            
            // Ensure our change handler runs first (capture phase)
            ticketImage.addEventListener('change', function(e) {
                // Only reset state if files were actually selected
                if (this.files && this.files.length > 0) {
                    window.fileDialogState.isSelectingFile = false;
                    log('Ticket image selected, preventing further dialogs');
                    
                    // Add a brief delay to make sure processing happens
                    setTimeout(function() {
                        log('Ticket image processing complete');
                    }, 100);
                }
            }, true);
        }
        
        log('Loop fix fully initialized on DOM ready');
    });
})();