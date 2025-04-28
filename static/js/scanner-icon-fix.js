/**
 * Special Font Awesome Icon Fix for Scanner Page
 * This script fixes the icon display issues specifically on the ticket scanner page
 */
(function() {
    'use strict';
    
    // Run immediately to fix icons as soon as possible
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Scanner icon fix script loaded');
        
        // Apply specific icon fixes for the scanner page
        fixScannerPageIcons();
        
        // Watch for any dynamically added icons
        watchForNewIcons();
    });
    
    // Apply fixes specifically for scanner page icons
    function fixScannerPageIcons() {
        // Add a high-priority CSS fix
        const style = document.createElement('style');
        style.textContent = `
            /* High-priority icon fix */
            .fa, .fas, .far, .fab, [class*="fa-"] {
                font-family: "Font Awesome 6 Free", "Font Awesome 5 Free", FontAwesome !important;
                visibility: visible !important;
                opacity: 1 !important;
                display: inline-block !important;
            }
            
            /* Specific fix for the ticket scanner page elements */
            #lottery-ticket-scanner .fa,
            #lottery-ticket-scanner .fas,
            #lottery-ticket-scanner .far,
            #lottery-ticket-scanner .fab,
            #lottery-ticket-scanner [class*="fa-"],
            .lottery-ticket-scanner .fa,
            .lottery-ticket-scanner .fas,
            .lottery-ticket-scanner .far,
            .lottery-ticket-scanner .fab,
            .lottery-ticket-scanner [class*="fa-"],
            .ticket-scanner-container .fa,
            .ticket-scanner-container .fas,
            .ticket-scanner-container .far,
            .ticket-scanner-container .fab,
            .ticket-scanner-container [class*="fa-"] {
                font-family: "Font Awesome 6 Free", "Font Awesome 5 Free", FontAwesome !important;
                visibility: visible !important;
                opacity: 1 !important;
                display: inline-block !important;
            }
            
            /* Header nav fix */
            .navbar .fa,
            .navbar .fas,
            .navbar .far,
            .navbar .fab,
            .navbar [class*="fa-"],
            nav .fa,
            nav .fas,
            nav .far,
            nav .fab,
            nav [class*="fa-"],
            header .fa,
            header .fas,
            header .far,
            header .fab,
            header [class*="fa-"] {
                font-family: "Font Awesome 6 Free", "Font Awesome 5 Free", FontAwesome !important;
                visibility: visible !important;
                opacity: 1 !important;
                display: inline-block !important;
            }
            
            /* Fix for the Snap Lotto header icon */
            a[href="/"] i.fa,
            a[href="/"] i.fas,
            a[href="/"] i.far,
            a[href="/"] i.fab,
            a[href="/"] [class*="fa-"] {
                font-family: "Font Awesome 6 Free", "Font Awesome 5 Free", FontAwesome !important;
                visibility: visible !important;
                opacity: 1 !important;
                display: inline-block !important;
                font-weight: 900 !important;
            }
        `;
        document.head.appendChild(style);
        
        // Force redraw of existing icons
        setTimeout(function() {
            const icons = document.querySelectorAll('.fa, .fas, .far, .fab, [class*="fa-"]');
            console.log(`Found ${icons.length} icons to fix`);
            
            icons.forEach(function(icon) {
                // Save original display state
                const originalDisplay = window.getComputedStyle(icon).display;
                
                // Force a redraw by temporarily hiding and showing
                icon.style.display = 'none';
                
                // Use requestAnimationFrame for smoother rendering
                requestAnimationFrame(function() {
                    icon.style.display = originalDisplay || 'inline-block';
                });
            });
        }, 50);
    }
    
    // Monitor for dynamically added icons
    function watchForNewIcons() {
        // Create a mutation observer to watch for new icons
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                    // Check each added node
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            // Check if this is an icon
                            if (node.classList && 
                                (node.classList.contains('fa') || 
                                 node.classList.contains('fas') || 
                                 node.classList.contains('far') || 
                                 node.classList.contains('fab') ||
                                 Array.from(node.classList).some(c => c.startsWith('fa-')))) {
                                
                                // Fix this icon
                                fixIcon(node);
                            }
                            
                            // Check for icons within added node
                            const childIcons = node.querySelectorAll('.fa, .fas, .far, .fab, [class*="fa-"]');
                            childIcons.forEach(fixIcon);
                        }
                    });
                }
            });
        });
        
        // Start observing the document for icon changes
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class']
        });
    }
    
    // Fix a single icon
    function fixIcon(icon) {
        // Determine appropriate font-weight based on icon type
        let fontWeight = '400';
        if (icon.classList && (icon.classList.contains('fas') || 
                               icon.classList.contains('fa-solid') || 
                               Array.from(icon.classList).some(c => c.startsWith('fa-')))) {
            fontWeight = '900';
        }
        
        // Ensure icon has proper font and styling
        icon.style.fontFamily = '"Font Awesome 6 Free", "Font Awesome 5 Free", FontAwesome';
        icon.style.fontWeight = fontWeight;
        icon.style.visibility = 'visible';
        icon.style.opacity = '1';
        icon.style.display = 'inline-block';
        
        // Check if the icon is directly inside an anchor tag (special handling)
        const isInAnchor = icon.parentElement && icon.parentElement.tagName.toLowerCase() === 'a';
        if (isInAnchor) {
            icon.style.fontWeight = '900'; // Ensure header icons are bold
        }
        
        // Force a redraw
        const originalDisplay = window.getComputedStyle(icon).display;
        icon.style.display = 'none';
        
        requestAnimationFrame(function() {
            icon.style.display = originalDisplay || 'inline-block';
            
            // Double-check visibility after the redraw
            setTimeout(function() {
                if (window.getComputedStyle(icon).opacity === '0' || 
                    window.getComputedStyle(icon).visibility === 'hidden') {
                    icon.style.opacity = '1';
                    icon.style.visibility = 'visible';
                }
            }, 50);
        });
    }
})();