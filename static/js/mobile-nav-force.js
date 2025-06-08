/**
 * Force Mobile Navigation Fixed Positioning
 * This script ensures the mobile navigation stays at the bottom of the screen
 */

function forceMobileNavPosition() {
    const mobileNav = document.getElementById('mobile-nav');
    if (mobileNav && window.innerWidth <= 991) {
        // Clear any conflicting styles first
        mobileNav.removeAttribute('style');
        mobileNav.className = 'd-lg-none';
        
        // Apply simple, reliable fixed positioning
        mobileNav.style.setProperty('position', 'fixed', 'important');
        mobileNav.style.setProperty('bottom', '0px', 'important');
        mobileNav.style.setProperty('left', '0px', 'important');
        mobileNav.style.setProperty('right', '0px', 'important');
        mobileNav.style.setProperty('width', '100%', 'important');
        mobileNav.style.setProperty('height', '60px', 'important');
        mobileNav.style.setProperty('background', 'white', 'important');
        mobileNav.style.setProperty('border-top', '1px solid #ddd', 'important');
        mobileNav.style.setProperty('box-shadow', '0 -2px 4px rgba(0,0,0,0.1)', 'important');
        mobileNav.style.setProperty('z-index', '9999', 'important');
        mobileNav.style.setProperty('display', 'flex', 'important');
        mobileNav.style.setProperty('flex-direction', 'row', 'important');
        mobileNav.style.setProperty('align-items', 'center', 'important');
        mobileNav.style.setProperty('justify-content', 'space-around', 'important');
        mobileNav.style.setProperty('visibility', 'visible', 'important');
        mobileNav.style.setProperty('opacity', '1', 'important');
        
        // Force styling on navigation links
        const navLinks = mobileNav.querySelectorAll('a');
        navLinks.forEach(link => {
            link.style.cssText = `
                flex: 1 !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                color: #666 !important;
                text-decoration: none !important;
                font-size: 10px !important;
                padding: 4px !important;
                height: 100% !important;
                margin: 0px !important;
            `;
            
            const icon = link.querySelector('i');
            if (icon) {
                icon.style.cssText = `
                    font-size: 16px !important;
                    margin-bottom: 2px !important;
                `;
            }
        });
        
        // Force body padding to prevent content overlap
        document.body.style.setProperty('padding-bottom', '70px', 'important');
        document.body.style.setProperty('margin-bottom', '0px', 'important');
        
        console.log('Mobile navigation v6.0 - Simplified positioning, navigation should be visible');
    }
}

// Run immediately when DOM is ready
document.addEventListener('DOMContentLoaded', forceMobileNavPosition);

// Run after page fully loads
window.addEventListener('load', forceMobileNavPosition);

// Run again after a short delay to override any conflicting scripts
setTimeout(forceMobileNavPosition, 1000);

// Run whenever the page is shown (for mobile browser tab switching)
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        setTimeout(forceMobileNavPosition, 100);
    }
});

// Check and reapply positioning every 5 seconds as fallback
setInterval(function() {
    const mobileNav = document.getElementById('mobile-nav');
    if (mobileNav && window.innerWidth <= 991) {
        const computedStyle = window.getComputedStyle(mobileNav);
        if (computedStyle.position !== 'fixed' || computedStyle.bottom !== '0px') {
            forceMobileNavPosition();
        }
    }
}, 5000);