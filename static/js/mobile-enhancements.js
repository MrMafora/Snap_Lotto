/**
 * Mobile-specific enhancements for Snap Lotto
 * Focuses on improving touch interactions and performance on mobile devices
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only apply mobile optimizations on small screens
    if (window.innerWidth < 768) {
        initMobileOptimizations();
    }
    
    // Listen for orientation changes
    window.addEventListener('orientationchange', handleOrientationChange);
});

/**
 * Initialize all mobile-specific optimizations
 */
function initMobileOptimizations() {
    optimizeFormElements();
    enhanceTouchTargets();
    improveMobileScrolling();
    fixVirtualKeyboard();
    addTouchFeedback();
    optimizeImages();
    enhanceTicketScanner();
}

/**
 * Make form elements more touch-friendly
 */
function optimizeFormElements() {
    // Make select dropdowns more finger-friendly
    document.querySelectorAll('select').forEach(select => {
        select.classList.add('mobile-optimized');
        select.style.fontSize = '16px';  // Prevent iOS zoom on focus
        select.style.height = '44px';    // Better touch target
    });
    
    // Prevent zoom on input focus in iOS
    document.querySelectorAll('input[type="text"], input[type="email"], input[type="number"], textarea').forEach(input => {
        input.style.fontSize = '16px';
    });
    
    // Enhance buttons for mobile
    document.querySelectorAll('.btn').forEach(btn => {
        if (!btn.classList.contains('btn-sm')) {
            btn.style.paddingTop = '12px';
            btn.style.paddingBottom = '12px';
        }
    });
}

/**
 * Add touch-specific feedback to interactive elements
 */
function addTouchFeedback() {
    // Add active state for touch interactions
    document.querySelectorAll('a, button, .card, .nav-link, .clickable').forEach(el => {
        // Only add touch feedback to elements without existing event handlers
        if (!el.getAttribute('data-touch-feedback')) {
            el.setAttribute('data-touch-feedback', 'true');
            
            el.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            }, { passive: true });
            
            el.addEventListener('touchend', function() {
                this.classList.remove('touch-active');
            }, { passive: true });
            
            el.addEventListener('touchcancel', function() {
                this.classList.remove('touch-active');
            }, { passive: true });
        }
    });
}

/**
 * Optimize performance by improving mobile scrolling
 */
function improveMobileScrolling() {
    // Use passive event listeners for better scroll performance
    document.addEventListener('touchstart', function() {}, { passive: true });
    document.addEventListener('touchmove', function() {}, { passive: true });
    
    // Add momentum scrolling to overflow elements
    document.querySelectorAll('.table-responsive, .scrollable').forEach(el => {
        el.style.webkitOverflowScrolling = 'touch';
    });
}

/**
 * Fix common virtual keyboard issues on mobile
 */
function fixVirtualKeyboard() {
    // Fix viewport issues when keyboard appears
    const viewportMeta = document.querySelector('meta[name="viewport"]');
    if (viewportMeta) {
        viewportMeta.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes, viewport-fit=cover');
    }
    
    // Fix for iOS 100vh issue
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    if (isIOS) {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
        
        window.addEventListener('resize', () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        });
    }
}

/**
 * Handle device orientation changes
 */
function handleOrientationChange() {
    // Reapply vh fix on orientation change
    setTimeout(() => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }, 300);
}

/**
 * Optimize images for mobile
 */
function optimizeImages() {
    // Add loading="lazy" to images below the fold
    document.querySelectorAll('img').forEach((img, index) => {
        if (index > 3 && !img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }
    });
}

/**
 * Specific enhancements for the ticket scanner page
 */
function enhanceTicketScanner() {
    const ticketForm = document.getElementById('ticket-form');
    if (!ticketForm) return;
    
    // Make file input more mobile-friendly
    const fileInput = document.getElementById('ticket-image');
    if (fileInput) {
        // Modern mobile browsers have good file pickers, enhance the experience
        fileInput.setAttribute('capture', 'environment');  // Use camera directly
        
        // Enhance file select button
        const fileSelectBtn = document.getElementById('file-select-btn');
        if (fileSelectBtn) {
            fileSelectBtn.innerHTML = '<i class="fas fa-camera me-2"></i> Take Photo';
            fileSelectBtn.classList.add('btn-lg');
        }
    }
    
    // Improve the scan button
    const scanButton = document.getElementById('scan-button');
    if (scanButton) {
        scanButton.classList.add('w-100', 'py-3');
    }
    
    // Improve view results button with touch feedback
    const viewResultsBtn = document.getElementById('view-results-btn');
    if (viewResultsBtn) {
        viewResultsBtn.classList.add('py-3', 'w-100');
        
        viewResultsBtn.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.98)';
        }, { passive: true });
        
        viewResultsBtn.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        }, { passive: true });
    }
}