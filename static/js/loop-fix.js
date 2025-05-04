/**
 * Loop Fix
 * Prevents recursive file dialog loop in ticket scanner while ensuring
 * the "Select Image" button functionality is preserved.
 * 
 * Issue #1: The file dialog was entering an infinite reopening loop
 * Fix #1: Implemented window.fileDialogState tracking to prevent recursive dialogs
 * 
 * Issue #2: The "Select Image" button stopped working entirely
 * Fix #2: Modified dialog state handling to allow user-initiated clicks while
 *         still preventing programmatic rapid-fire opening
 *
 * This script is part of a multi-layered solution:
 * 1. loop-fix.js - Prevents infinite file dialog loops
 * 2. file-select-fix.js - Ensures proper file selection and preview
 * 3. direct-button-fix.js - Last-resort fallback for button functionality
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
                // FIXED: We don't return false here as it prevents the click completely
                // Instead, we'll let the click happen for the first one only
                log('However, this is likely the initial user click, so allowing it');
                window.fileDialogState.isSelectingFile = false;
            }
            
            if (timeSinceLastDialog < window.fileDialogState.minDialogInterval) {
                log(`Too frequent file dialog attempt (${timeSinceLastDialog}ms since last)`);
                // FIXED: For first-time clicks, we shouldn't block regardless of timing
                if (timeSinceLastDialog < 100) {  // If it's less than 100ms, it's definitely programmatic
                    log('Prevented programmatic rapid-fire dialog');
                    return false;
                } else {
                    log('But allowing possible user-initiated dialog');
                }
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
        
        // Add a direct high-priority click handler for the file selection button
        const fileSelectBtn = document.getElementById('file-select-btn');
        if (fileSelectBtn) {
            log('Found file select button, adding high-priority click handler');
            
            // Add direct click handler to the select button with capture phase to run first
            fileSelectBtn.addEventListener('click', function(e) {
                log('Direct high-priority file select button click detected');
                const fileInput = document.getElementById('ticket-image');
                
                if (fileInput) {
                    // Directly reset file dialog state to ensure button always works
                    log('Ensuring file dialog state is reset before button click');
                    window.fileDialogState.isSelectingFile = false;
                }
            }, true); // true for capture phase to run before other handlers
        }
        
        log('Loop fix fully initialized on DOM ready');
    });
    
    // Provide a global function to reset file dialog state in case of emergency
    window.resetFileDialogState = function() {
        log('Manual reset of file dialog state requested');
        window.fileDialogState.isSelectingFile = false;
        window.fileDialogState.lastDialogTime = 0;
        return 'File dialog state reset successfully';
    };
})();