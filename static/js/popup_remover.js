/**
 * Popup Remover Script
 * 
 * This script aggressively removes any popups, modals, overlays, or dialogs 
 * that might appear when viewing lottery website content in our application.
 * 
 * It runs continuously to catch dynamically added popups and uses multiple
 * techniques to ensure popups are fully removed.
 */

// Function to remove popups from any context
function removePopups() {
    // Common popup selectors
    const popupSelectors = [
        '[role="dialog"]',
        '.modal-dialog',
        '.modal',
        '.popup',
        '.overlay',
        'div[class*="popup"]',
        'div[id*="popup"]',
        'div[class*="modal"]',
        'div[id*="modal"]',
        'div[class*="dialog"]',
        'div[id*="dialog"]',
        '.fade.in',
        '#modal-container',
        '.modal-container',
        '.modal-content',
        '.modal-body',
        '.modal-header',
        '.modal-footer',
        '#popup-message',
        '.popup-message',
        '.error-popup',
        '.warning-popup',
        'div[class*="error"]', 
        'div[id*="error"]',
        '[class*="error"]', 
        '[id*="error"]',
        '[class*="modal"]', 
        '[id*="modal"]',
        '.cookie-banner',
        '.consent-banner'
    ];
    
    try {
        // Find and remove all popups
        popupSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                if (element && element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            });
        });
        
        // Remove modal backdrops
        document.querySelectorAll('.modal-backdrop, .overlay, .fade, .in').forEach(element => {
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        });
        
        // Fix body styling
        document.body.classList.remove('modal-open');
        document.body.style.overflow = 'auto';
        document.body.style.paddingRight = '0';
        
        // Remove fixed position elements that might be dialogs
        document.querySelectorAll('div[style*="position: fixed"], div[style*="position:fixed"]').forEach(element => {
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        });
        
        // Re-enable scrolling
        document.documentElement.style.overflow = 'auto';
        document.body.style.overflow = 'auto';
    } catch (e) {
        console.error("Error removing popups:", e);
    }
}

// Run immediately
document.addEventListener('DOMContentLoaded', function() {
    removePopups();
    
    // Run periodically to catch any new popups
    setInterval(removePopups, 500);
    
    // Also run when DOM changes
    const observer = new MutationObserver(function(mutations) {
        removePopups();
    });
    
    // Start observing
    observer.observe(document.body, { 
        childList: true, 
        subtree: true 
    });
});

// Run on window load to catch late-appearing popups
window.addEventListener('load', function() {
    removePopups();
});

// Intercept and prevent default popup behavior
document.addEventListener('click', function(e) {
    // Attempt to prevent popup-triggering clicks
    const target = e.target;
    if (target && 
        (target.getAttribute('data-toggle') === 'modal' || 
         target.getAttribute('data-target') || 
         target.getAttribute('href') === '#modal')) {
        e.preventDefault();
        e.stopPropagation();
        return false;
    }
}, true);