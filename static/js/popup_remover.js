/**
 * Popup Remover Script
 * 
 * This script removes the "Oops!" error popups that appear when viewing scraped lottery content.
 * It targets specific elements used by the National Lottery website to show error messages.
 */

(function() {
    // Run immediately and then periodically to handle dynamic loading
    removePopups();
    
    // Set an interval to continuously check and remove popups
    // This catches popups that appear after page load
    setInterval(removePopups, 200);
    
    function removePopups() {
        // Remove any dialog overlays or modals with "Oops" messages
        const popups = document.querySelectorAll('.modal-dialog, .popup, .overlay, [role="dialog"], .modal');
        popups.forEach(popup => {
            const text = popup.textContent || '';
            if (text.includes('Oops') || text.includes('went wrong') || text.includes('network') || text.includes('connectivity')) {
                if (popup.style) {
                    popup.style.display = 'none';
                    popup.style.visibility = 'hidden';
                }
                // Try to remove from DOM entirely if possible
                try {
                    popup.parentNode.removeChild(popup);
                } catch (e) {
                    // Silent catch if removal fails
                }
            }
        });
        
        // Remove specific popup from national lottery site
        const specificPopups = document.querySelectorAll('[id*="popup"], [class*="popup"], [id*="dialog"], [class*="dialog"], [id*="modal"], [class*="modal"]');
        specificPopups.forEach(popup => {
            if (popup.style) {
                popup.style.display = 'none';
                popup.style.visibility = 'hidden';
            }
        });

        // Also remove any overlay backgrounds
        const overlays = document.querySelectorAll('.modal-backdrop, .overlay, .fade, .in');
        overlays.forEach(overlay => {
            if (overlay.style) {
                overlay.style.display = 'none';
                overlay.style.visibility = 'hidden';
            }
            try {
                overlay.parentNode.removeChild(overlay);
            } catch (e) {
                // Silent catch
            }
        });
        
        // Re-enable scrolling on the body and html elements
        const bodyAndHtml = document.querySelectorAll('body, html');
        bodyAndHtml.forEach(element => {
            if (element.style) {
                element.style.overflow = 'auto';
                element.style.position = 'static';
            }
            // Remove any modal classes from body
            if (element.classList) {
                element.classList.remove('modal-open');
            }
        });
    }
})();