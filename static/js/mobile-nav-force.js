/**
 * Force Mobile Navigation Fixed Positioning
 * This script ensures the mobile navigation stays at the bottom of the screen
 */

function forceMobileNavPosition() {
    const mobileNav = document.getElementById('mobile-nav');
    if (mobileNav && window.innerWidth <= 991) {
        // Remove any existing positioning classes
        mobileNav.className = 'd-lg-none';
        
        // Force fixed positioning with CSS text override
        mobileNav.style.cssText = `
            position: fixed !important;
            bottom: 0px !important;
            left: 0px !important;
            right: 0px !important;
            width: 100vw !important;
            height: 60px !important;
            background: white !important;
            border-top: 1px solid #ddd !important;
            box-shadow: 0 -2px 4px rgba(0,0,0,0.1) !important;
            z-index: 99999 !important;
            display: flex !important;
            margin: 0px !important;
            padding: 0px !important;
            transform: none !important;
            top: auto !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: space-around !important;
        `;
        
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
        
        console.log('Mobile navigation positioning forced with aggressive CSS override v2.0');
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
    if (mobileNav && mobileNav.style.position !== 'fixed') {
        forceMobileNavPosition();
    }
}, 5000);