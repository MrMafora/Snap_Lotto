/**
 * Mobile Optimization - Improves loading speed on mobile devices
 * This script consolidates critical performance optimizations and defers non-essential operations
 */

// Self-executing function to avoid polluting global scope
(function() {
    // Flag to indicate if we're on a mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // Set initial flags
    window.pageOptimized = false;
    window.criticalResourcesLoaded = false;
    
    // Only apply optimizations on mobile devices
    if (isMobile) {
        console.log('Mobile device detected, applying performance optimizations');
        
        // Apply initial optimizations immediately
        applyInitialOptimizations();
        
        // Set up load event handlers
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, applying critical performance optimizations');
            
            // Mark critical resources as loaded
            window.criticalResourcesLoaded = true;
            
            // Apply the most important optimizations first
            applyDOMLoadedOptimizations();
            
            // Defer non-essential operations
            setTimeout(applyDeferredOptimizations, 100);
        });
        
        // Apply final optimizations after window load
        window.addEventListener('load', function() {
            console.log('Window loaded, applying final performance optimizations');
            
            // Mark page as fully optimized
            window.pageOptimized = true;
        });
    }
    
    // Step 1: Apply immediate optimizations
    function applyInitialOptimizations() {
        // Disable animations initially to improve first paint
        const style = document.createElement('style');
        style.textContent = `
            * {
                animation-duration: 0.001s !important;
                transition-duration: 0.001s !important;
            }
            
            body, html {
                scroll-behavior: auto !important;
            }
            
            .ticket-drop-area {
                transition: none !important;
            }
        `;
        document.head.appendChild(style);
        
        // Prevent render-blocking by deferring unnecessary scripts
        document.querySelectorAll('script:not([data-critical="true"])').forEach(script => {
            if (!script.hasAttribute('defer') && !script.hasAttribute('async')) {
                script.setAttribute('defer', '');
            }
        });
    }
    
    // Step 2: Apply DOM-loaded optimizations
    function applyDOMLoadedOptimizations() {
        // Optimize for touch events
        document.documentElement.style.touchAction = 'manipulation';
        
        // Initialize any visible UI elements first
        initializeVisibleElements();
        
        // Enable hardware acceleration for smoother animations
        document.body.style.transform = 'translateZ(0)';
        document.body.style.backfaceVisibility = 'hidden';
        document.body.style.perspective = '1000px';
        
        // Enable smoother scrolling now that critical content is loaded
        document.documentElement.style.scrollBehavior = 'smooth';
    }
    
    // Step 3: Apply deferred optimizations
    function applyDeferredOptimizations() {
        // Remove initial animation/transition block after a short delay
        const styleElements = document.querySelectorAll('style');
        styleElements.forEach(style => {
            if (style.textContent.includes('animation-duration: 0.001s')) {
                setTimeout(() => {
                    style.textContent = '';
                }, 300);
            }
        });
        
        // Optimize images that are off-screen
        optimizeOffscreenImages();
    }
    
    // Helper function to initialize visible UI elements first
    function initializeVisibleElements() {
        // Focus on visible form elements
        const dropArea = document.getElementById('drop-area');
        if (dropArea && isElementInViewport(dropArea)) {
            dropArea.classList.add('ready');
        }
        
        // Pre-initialize the file input system
        const fileInput = document.getElementById('ticket-image');
        if (fileInput) {
            // Create an empty touch event listener to make the input more responsive
            fileInput.addEventListener('touchstart', function() {}, { passive: true });
        }
    }
    
    // Helper function to check if element is in viewport
    function isElementInViewport(el) {
        if (!el || !el.getBoundingClientRect) return false;
        
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Helper function to optimize offscreen images
    function optimizeOffscreenImages() {
        // Set loading="lazy" for images that are offscreen
        document.querySelectorAll('img').forEach(img => {
            if (!isElementInViewport(img) && !img.getAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
        });
    }
})();