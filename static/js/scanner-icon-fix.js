/**
 * Scanner Icon Fix for Mobile Devices
 * 
 * This script addresses the issue of Font Awesome icons disappearing on iOS devices
 * during the scanning process. It enhances all critical icons with additional styling
 * and monitors/repairs any missing icons during runtime.
 * 
 * Features:
 * - Adds explicit font weight to Font Awesome icons
 * - Applies hardware acceleration to icon elements
 * - Monitors for icon visibility issues and repairs them
 * - Forces icon repainting when they disappear
 */

(function() {
    'use strict';
    
    console.log('Scanner icon fix initializing');
    
    // Configuration for icon fixing
    const config = {
        checkInterval: 1000, // How often to check for broken icons (ms)
        criticalIconSelectors: [
            '.fa-camera',
            '.fa-image',
            '.fa-upload',
            '.fa-trash',
            '.fa-check',
            '.fa-times',
            '.fa-search',
            '.fa-ticket',
            '.fa-trophy',
            '.fa-calculator',
            '.fa-chart-bar',
            '.fa-lock',
            '.fa-check-circle',
            '.fa-clock',
            '.fa-bell',
            '.fa-info-circle'
        ],
        fixedIconClass: 'icon-fixed',
        monitoringActive: true
    };
    
    // Apply critical styling to Font Awesome icons
    function fixFontAwesomeIcons() {
        // Target all Font Awesome icons
        const icons = document.querySelectorAll('.fas, .far, .fab, .fa, [class*="fa-"]');
        
        icons.forEach(function(icon) {
            // Skip already fixed icons
            if (icon.classList.contains(config.fixedIconClass)) {
                return;
            }
            
            // Apply critical fixes
            icon.classList.add(config.fixedIconClass);
            
            // Apply inline critical styles for iOS rendering
            const currentStyle = icon.getAttribute('style') || '';
            icon.setAttribute('style', currentStyle + 
                '; display: inline-block !important;' +
                ' font-weight: 900 !important;' +
                ' transform: translateZ(0);' +
                ' backface-visibility: hidden;' +
                ' -webkit-font-smoothing: antialiased;' +
                ' -moz-osx-font-smoothing: grayscale;');
        });
        
        console.log('Fixed', icons.length, 'Font Awesome icons');
    }
    
    // Force re-render of broken icons
    function forceIconRerender(brokenIcons) {
        brokenIcons.forEach(function(icon) {
            // Check if the icon is actually broken
            const currentFontWeight = window.getComputedStyle(icon).fontWeight;
            const iconVisible = icon.offsetWidth > 0 && icon.offsetHeight > 0;
            
            if (!iconVisible || currentFontWeight !== '900') {
                // Clone and replace the icon to force browser re-render
                const parent = icon.parentNode;
                
                if (parent) {
                    const clone = icon.cloneNode(true);
                    
                    // Apply even stronger fixes to the clone
                    clone.style.fontWeight = '900 !important';
                    clone.style.visibility = 'visible';
                    clone.style.opacity = '1';
                    clone.style.display = 'inline-block';
                    clone.style.transform = 'translateZ(0)';
                    
                    // Special fix for iOS rendering
                    clone.innerHTML = ' ' + clone.innerHTML;
                    
                    // Replace the original icon
                    parent.replaceChild(clone, icon);
                    
                    console.log('Force re-rendered icon:', clone.className);
                }
            }
        });
    }
    
    // Check for broken Font Awesome icons and fix them
    function monitorAndFixIcons() {
        if (!config.monitoringActive) {
            return;
        }
        
        // Check for critical icons that need fixing
        const brokenIcons = [];
        
        // Check each critical icon type
        config.criticalIconSelectors.forEach(function(selector) {
            const icons = document.querySelectorAll(selector);
            
            icons.forEach(function(icon) {
                const computedStyle = window.getComputedStyle(icon);
                
                // Check for signs of broken icon
                if (computedStyle.fontWeight !== '900' ||
                    computedStyle.display === 'none' ||
                    computedStyle.visibility === 'hidden' ||
                    parseFloat(computedStyle.opacity) < 0.9) {
                    
                    brokenIcons.push(icon);
                }
            });
        });
        
        // Fix any broken icons
        if (brokenIcons.length > 0) {
            console.log('Found', brokenIcons.length, 'broken icons to fix');
            forceIconRerender(brokenIcons);
        }
    }
    
    // Special fix for Font Awesome inside buttons
    function fixFontAwesomeInButtons() {
        const buttons = document.querySelectorAll('button, .btn');
        
        buttons.forEach(function(button) {
            // Find Font Awesome icons inside the button
            const icons = button.querySelectorAll('.fas, .far, .fab, .fa, [class*="fa-"]');
            
            icons.forEach(function(icon) {
                // Apply special styling to ensure icon remains visible
                icon.setAttribute('style', 
                    'display: inline-block !important;' +
                    ' font-weight: 900 !important;' +
                    ' visibility: visible !important;' + 
                    ' min-width: 1em !important;' +
                    ' transform: translateZ(0);' +
                    ' backface-visibility: hidden;' +
                    ' margin-right: 0.5em !important;');
                
                // Add a non-breaking space after the icon to ensure proper rendering
                const space = document.createTextNode('\u00A0');
                if (icon.nextSibling) {
                    icon.parentNode.insertBefore(space, icon.nextSibling);
                } else {
                    icon.parentNode.appendChild(space);
                }
                
                // Mark as fixed
                icon.classList.add(config.fixedIconClass);
                icon.setAttribute('data-button-icon-fixed', 'true');
            });
        });
    }
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Scanner icon fix running initial fixes');
        
        // Apply initial fixes
        fixFontAwesomeIcons();
        fixFontAwesomeInButtons();
        
        // Set up monitoring for icon problems
        setInterval(function() {
            // Apply fixes to any new icons
            fixFontAwesomeIcons();
            
            // Check for and fix broken icons
            monitorAndFixIcons();
        }, config.checkInterval);
        
        // Special event listener for scan button
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', function() {
                // Apply immediate fixes when scan is started
                setTimeout(function() {
                    fixFontAwesomeIcons();
                    fixFontAwesomeInButtons();
                    monitorAndFixIcons();
                }, 100);
            });
        }
        
        // Also apply fixes immediately after page transitions
        window.addEventListener('pageshow', function() {
            setTimeout(function() {
                fixFontAwesomeIcons();
                fixFontAwesomeInButtons();
                monitorAndFixIcons();
            }, 100);
        });
        
        console.log('Scanner icon fix initialized');
    });
    
    // Expose diagnostic function to console
    window.checkIcons = function() {
        const allIcons = document.querySelectorAll('.fas, .far, .fab, .fa, [class*="fa-"]');
        let brokenCount = 0;
        
        allIcons.forEach(function(icon) {
            const computedStyle = window.getComputedStyle(icon);
            const fontWeight = computedStyle.fontWeight;
            const isVisible = 
                computedStyle.display !== 'none' && 
                computedStyle.visibility !== 'hidden' &&
                parseFloat(computedStyle.opacity) > 0;
            
            if (fontWeight !== '900' || !isVisible) {
                console.log('Broken icon:', icon.className, 'Font weight:', fontWeight, 'Visible:', isVisible);
                brokenCount++;
            }
        });
        
        return {
            total: allIcons.length,
            broken: brokenCount,
            fixed: allIcons.length - brokenCount
        };
    };
    
    // Apply initial fixes even before DOM is fully loaded
    fixFontAwesomeIcons();
})();