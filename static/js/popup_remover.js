/**
 * Popup and Error Dialog Remover
 * Automatically removes "Oops" error messages and modal dialogs
 */

// Execute when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Remove popups immediately
    removePopups();
    
    // Then periodically check for new popups (sometimes they're added dynamically)
    setInterval(removePopups, 500);
});

// Function to remove all types of popups and error messages
function removePopups() {
    // Common popup selectors
    const elementsToRemove = [
        '.popup', '.modal', '.overlay', '.cookie-banner',
        '[class*="popup"]', '[class*="modal"]', '[class*="overlay"]',
        '[class*="cookie"]', '[class*="consent"]', '[class*="error"]',
        'div[role="dialog"]', 'div[aria-modal="true"]',
        '.fade', '.modal-backdrop'
    ];
    
    // Remove elements matching selectors
    elementsToRemove.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
            if(el) el.remove();
        });
    });
    
    // Remove elements containing "Oops" text
    document.querySelectorAll('div, h1, h2, h3, p, span').forEach(el => {
        if(el && el.innerText && 
           (el.innerText.includes('Oops') || 
            el.innerText.includes('Something went wrong') || 
            el.innerText.includes('network connectivity'))) {
            
            // Try to find parent modal/popup container
            let parent = el.parentElement;
            for(let i=0; i<5 && parent; i++) {
                if(parent.tagName === 'BODY') break;
                parent = parent.parentElement;
            }
            
            // Hide the parent container if found, otherwise hide the element itself
            if(parent && parent.tagName !== 'BODY') {
                parent.style.display = 'none';
            } else {
                el.style.display = 'none';
            }
        }
    });
    
    // Remove fixed position elements (often overlays/modals)
    document.querySelectorAll('body > div').forEach(el => {
        const style = window.getComputedStyle(el);
        if(style.position === 'fixed' && 
           (style.zIndex === 'auto' || parseInt(style.zIndex) > 100)) {
            el.style.display = 'none';
        }
    });
    
    // Re-enable scrolling if it was disabled by a modal
    document.body.style.overflow = 'auto';
    document.documentElement.style.overflow = 'auto';
}