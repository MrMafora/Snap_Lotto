/**
 * Mobile Optimization Script
 * This script runs very early in the page load cycle to optimize performance
 * for mobile devices, especially iOS.
 */

(function() {
    console.log('Mobile optimization script initializing');
    
    // Track the page load performance
    const startTime = performance.now();
    
    // Define the mobile device detection
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    
    // Function to fix Font Awesome icons
    function fixFontAwesomeIcons() {
        // Add a specific CSS rule to ensure Font Awesome icons work
        const style = document.createElement('style');
        style.textContent = `
            .fa, .fas, .far, .fab, [class*="fa-"] {
                font-family: "Font Awesome 6 Free", "Font Awesome 5 Free", FontAwesome !important;
                display: inline-block !important;
                visibility: visible !important;
                opacity: 1 !important;
            }
        `;
        document.head.appendChild(style);
        
        // Apply an immediate fix for icons in the title and navbar
        setTimeout(() => {
            const icons = document.querySelectorAll('.fa, .fas, .far, .fab, [class*="fa-"]');
            if (icons.length > 0) {
                console.log(`Fixing ${icons.length} Font Awesome icons`);
                icons.forEach(icon => {
                    // Force redraw of the icon
                    const originalDisplay = window.getComputedStyle(icon).display;
                    icon.style.display = 'none';
                    setTimeout(() => {
                        icon.style.display = originalDisplay || 'inline-block';
                    }, 10);
                });
            } else {
                console.log('No Font Awesome icons found on page');
            }
        }, 100);
    }
    
    // Immediately add optimization classes to the body
    document.addEventListener('DOMContentLoaded', function() {
        if (isMobile) {
            document.body.classList.add('mobile-optimized');
            if (isIOS) {
                document.body.classList.add('ios-device');
            }
            
            // Fix for Font Awesome icons - ensure they're displayed correctly
            fixFontAwesomeIcons();
        }
        
        // Optimize images by setting loading="lazy" on non-critical images
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            if (!img.classList.contains('ticket-preview')) {
                img.setAttribute('loading', 'lazy');
            }
        });
        
        // Apply passive event listeners for touch events to improve scrolling performance
        const touchTargets = document.querySelectorAll('button, a, .btn, .ticket-drop-area');
        touchTargets.forEach(el => {
            el.addEventListener('touchstart', function(){}, {passive: true});
            el.addEventListener('touchmove', function(){}, {passive: true});
        });
        
        // Reduce animation duration on mobile
        if (isMobile) {
            const style = document.createElement('style');
            style.textContent = `
                @media (max-width: 576px) {
                    * {
                        animation-duration: 50% !important;
                        transition-duration: 50% !important;
                    }
                    
                    .btn-pulse {
                        animation-duration: 1s !important;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Detect and fix viewport issues on mobile
        if (isMobile) {
            const viewportMeta = document.querySelector('meta[name="viewport"]');
            if (viewportMeta) {
                // Ensure proper mobile rendering with maximum-scale for accessibility
                viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
            }
        }
        
        // Special iOS optimizations
        if (isIOS) {
            // Fix for iOS button display issues
            const buttons = document.querySelectorAll('.btn');
            buttons.forEach(btn => {
                btn.style.webkitAppearance = 'none';
                btn.style.transform = 'translateZ(0)'; // Hardware acceleration
            });
            
            // Disable hover effects on iOS since they can cause performance issues
            const style = document.createElement('style');
            style.textContent = `
                @media (hover: none) {
                    a:hover, button:hover, .btn:hover {
                        transition: none !important;
                        transform: none !important;
                        box-shadow: none !important;
                    }
                }
            `;
            document.head.appendChild(style);
            
            // iOS specific scrolling optimization
            document.body.style.webkitOverflowScrolling = 'touch';
        }
        
        // Track and log performance
        window.addEventListener('load', function() {
            const loadTime = performance.now() - startTime;
            console.log(`Page fully loaded in ${Math.round(loadTime)}ms`);
            
            // If page load is taking too long, simplify rendering
            if (loadTime > 3000 && isMobile) {
                console.log('Applying emergency performance optimizations');
                
                // Disable most animations
                const style = document.createElement('style');
                style.textContent = `
                    @media (max-width: 576px) {
                        * {
                            animation: none !important;
                            transition: none !important;
                        }
                        
                        .btn-pulse {
                            animation: none !important;
                            box-shadow: none !important;
                        }
                    }
                `;
                document.head.appendChild(style);
                
                // Simplify shadows and effects
                document.querySelectorAll('.card, .btn, .ad-container').forEach(el => {
                    el.style.boxShadow = 'none';
                });
            }
        });
    });
    
    // Create a global helper for checking if we're on mobile
    window.isMobileDevice = isMobile;
    window.isIOSDevice = isIOS;
    
    // Provide a global function for emergency optimization if needed
    window.applyEmergencyMobileOptimization = function() {
        console.log('Applying emergency mobile optimizations');
        
        // Remove all animations immediately
        const style = document.createElement('style');
        style.textContent = `
            * {
                animation: none !important;
                transition: none !important;
                box-shadow: none !important;
            }
        `;
        document.head.appendChild(style);
        
        // Simplify rendering
        document.querySelectorAll('.card, .btn, .ad-container').forEach(el => {
            el.style.boxShadow = 'none';
        });
        
        // Reduce image quality for faster rendering
        document.querySelectorAll('img').forEach(img => {
            if (!img.classList.contains('ticket-preview')) {
                img.style.display = 'none';
            }
        });
        
        // Disable all non-critical background images
        document.querySelectorAll('[style*="background-image"]').forEach(el => {
            el.style.backgroundImage = 'none';
        });
        
        return 'Emergency optimizations applied';
    };
    
    // Log completion of the initialization
    console.log('Mobile optimization script loaded');
})();