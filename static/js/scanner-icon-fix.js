/**
 * Scanner Icon Fix
 * 
 * This script addresses the issue of disappearing Font Awesome icons
 * particularly on iOS devices. It provides a continuous monitoring
 * system that detects when icons are missing and restores them.
 * 
 * Features:
 * - Detects Font Awesome icons that have failed to render
 * - Applies anti-flicker CSS to protect against rendering issues
 * - Continuously monitors page for icon rendering problems
 * - Focuses especially on icons in the scanning interface
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        checkInterval: 1000,        // Check every second
        scanIconSelector: '.fa, .fas, .far, .fal, .fad, .fab', // All Font Awesome icons
        criticalIconSelectors: [
            '#scan-button .fa-search',
            '#view-results-btn .fa-check-circle',
            '#view-results-btn .fa-lock',
            '.ticket-ball .fa-check'
        ],
        antiFlickerStyle: 'transform: translateZ(0); backface-visibility: hidden; perspective: 1000px; -webkit-font-smoothing: antialiased;'
    };
    
    // Initialize the fix
    function initIconFix() {
        // Initialize immediately
        fixIcons();
        
        // Apply anti-flicker styles immediately
        applyAntiFlickerStyles();
        
        // Set up continuous monitoring
        setInterval(function() {
            applyAntiFlickerStyles();
            fixIcons();
        }, config.checkInterval);
        
        // Listen for DOM changes that might affect icons
        setupMutationObserver();
        
        console.log('Scanner icon fix initialized');
    }
    
    // Fix Font Awesome icons
    function fixIcons() {
        // Find all Font Awesome icons
        const icons = document.querySelectorAll(config.scanIconSelector);
        
        // Check if their font-weight is properly set
        let fixedCount = 0;
        
        icons.forEach(function(icon) {
            // Skip if already processed
            if (icon.hasAttribute('data-icon-fixed')) return;
            
            // Check computed style for font-weight
            const style = window.getComputedStyle(icon);
            const fontWeight = style.getPropertyValue('font-weight');
            
            // Fix icons with missing or incorrect font-weight
            if (!fontWeight || fontWeight === 'normal' || parseInt(fontWeight) < 400) {
                // Apply stronger font-weight to ensure visibility
                icon.style.fontWeight = '900';
                icon.style.visibility = 'visible';
                icon.style.display = 'inline-block';
                
                // Mark as fixed
                icon.setAttribute('data-icon-fixed', 'true');
                
                fixedCount++;
            }
            
            // Ensure icons in critical places are visible
            config.criticalIconSelectors.forEach(function(selector) {
                if (icon.matches(selector)) {
                    // Force these to be extra visible
                    icon.style.fontWeight = '900';
                    icon.style.visibility = 'visible';
                    icon.style.display = 'inline-block';
                    icon.style.opacity = '1';
                }
            });
        });
        
        if (fixedCount > 0) {
            console.log('Fixed', fixedCount, 'Font Awesome icons');
        }
        
        return fixedCount;
    }
    
    // Apply anti-flicker styles to the page
    function applyAntiFlickerStyles() {
        // Find all elements with scan-related classes
        const scanElements = document.querySelectorAll('.ticket-scanner-container, .scan-button, .results-container, .ticket-ball');
        
        scanElements.forEach(function(element) {
            if (!element.hasAttribute('data-antiflicker')) {
                element.style.cssText += config.antiFlickerStyle;
                element.setAttribute('data-antiflicker', 'true');
            }
        });
        
        // Special handling for Font Awesome icons
        const icons = document.querySelectorAll(config.scanIconSelector);
        
        icons.forEach(function(icon) {
            if (!icon.hasAttribute('data-antiflicker')) {
                icon.style.cssText += config.antiFlickerStyle;
                icon.setAttribute('data-antiflicker', 'true');
            }
        });
        
        console.log('Applying anti-flicker styles');
    }
    
    // Setup mutation observer to detect DOM changes
    function setupMutationObserver() {
        // Create an observer instance
        const observer = new MutationObserver(function(mutations) {
            // If we see DOM changes, run the icon fix
            fixIcons();
        });
        
        // Start observing the document body for changes
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'style']
        });
    }
    
    // Initialize right away if document is already loaded
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(initIconFix, 100);
    } else {
        // Otherwise wait for DOM content to be loaded
        document.addEventListener('DOMContentLoaded', initIconFix);
    }
})();