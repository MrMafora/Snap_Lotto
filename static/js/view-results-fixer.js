/**
 * View Results Button Fixer
 * This script ensures the "View Results" button always works regardless of other script issues
 * It adds a fail-safe mechanism that will always enable the button after 15 seconds
 */

(function() {
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('View Results Button Fixer activated');
        initViewResultsButtonFixer();
    });

    // Initialize the button fixer
    function initViewResultsButtonFixer() {
        // Set up logging
        function log(message) {
            console.log(message);
        }

        // Configuration
        const config = {
            buttonId: 'view-results-btn',
            buttonContainerId: 'view-results-btn-container',
            timeoutMs: 15000, // 15 seconds failsafe
            inspectIntervalMs: 1000 // Check DOM every second
        };

        // DOM Elements
        let viewResultsBtn = null;
        let buttonContainer = null;
        let firstAdOverlay = document.getElementById('ad-overlay-loading');
        let secondAdOverlay = document.getElementById('ad-overlay-results');

        // State
        let hasScanned = false;
        let buttonFixed = false;
        let buttonTimer = null;
        let inspectionTimer = null;

        // Force button to be enabled and visible
        function enableButton() {
            if (!viewResultsBtn) {
                viewResultsBtn = document.getElementById(config.buttonId);
                if (!viewResultsBtn) {
                    log('Button not found in DOM');
                    return false;
                }
            }

            if (!buttonContainer) {
                buttonContainer = document.getElementById(config.buttonContainerId);
                if (!buttonContainer) {
                    log('Button container not found in DOM');
                    return false;
                }
            }

            // Make button visible and enabled
            buttonContainer.style.display = 'block';
            viewResultsBtn.disabled = false;
            viewResultsBtn.classList.remove('btn-secondary');
            viewResultsBtn.classList.add('btn-success');
            viewResultsBtn.classList.add('btn-pulse');
            viewResultsBtn.setAttribute('data-forced-enabled', 'true');
            viewResultsBtn.innerHTML = ' View Results Now!';

            // Make sure the button is clickable by adding direct event handlers
            if (!buttonFixed) {
                viewResultsBtn.addEventListener('click', function(e) {
                    log('Button clicked via direct handler');
                    secondAdOverlay.style.display = 'none';
                    document.getElementById('results-container').scrollIntoView({ behavior: 'smooth' });
                    e.stopPropagation();
                });
                buttonFixed = true;
            }

            return true;
        }

        // Check if the scan has been initiated
        function checkScanInitiated() {
            // Look for signs that the scan button was clicked
            if (firstAdOverlay && 
                (getComputedStyle(firstAdOverlay).display === 'flex' || 
                getComputedStyle(firstAdOverlay).display === 'block')) {
                hasScanned = true;
                startButtonTimer();
                return true;
            }
            return false;
        }

        // Start the failsafe timer
        function startButtonTimer() {
            if (buttonTimer) {
                clearTimeout(buttonTimer);
            }
            
            log('Starting failsafe timer for button activation');
            buttonTimer = setTimeout(() => {
                log('Failsafe timer triggered - forcing button activation');
                if (enableButton()) {
                    log('Button enabled by failsafe');
                    
                    // Inspect DOM elements to help with debugging
                    inspectDOM();
                }
            }, config.timeoutMs);
        }

        // Inspect DOM elements to help with debugging
        function inspectDOM() {
            log('📊 Inspecting DOM elements:');
            
            // Check button container
            const btnContainer = document.getElementById(config.buttonContainerId);
            if (btnContainer) {
                log('✅ Button container found: ', {
                    id: btnContainer.id,
                    display: getComputedStyle(btnContainer).display,
                    visibility: getComputedStyle(btnContainer).visibility,
                    classes: btnContainer.className,
                    parent: btnContainer.parentElement.tagName
                });
            } else {
                log('❌ Button container not found in DOM');
            }
            
            // Check button element
            const btn = document.getElementById(config.buttonId);
            if (btn) {
                log('✅ Button element found: ', {
                    id: btn.id,
                    display: getComputedStyle(btn).display,
                    visibility: getComputedStyle(btn).visibility,
                    disabled: btn.disabled,
                    classes: btn.className,
                    text: btn.innerHTML
                });
            } else {
                log('❌ Button element not found in DOM');
            }
            
            // Check ad overlays
            log('ℹ️ First ad overlay:', {
                display: firstAdOverlay ? getComputedStyle(firstAdOverlay).display : 'element not found',
                visibility: firstAdOverlay ? getComputedStyle(firstAdOverlay).visibility : 'element not found'
            });
            
            log('ℹ️ Second ad overlay:', {
                display: secondAdOverlay ? getComputedStyle(secondAdOverlay).display : 'element not found',
                visibility: secondAdOverlay ? getComputedStyle(secondAdOverlay).visibility : 'element not found'
            });
        }
        
        // Set up periodic inspection of button state
        function setupInspectionTimer() {
            inspectionTimer = setInterval(() => {
                if (!hasScanned) {
                    checkScanInitiated();
                } else {
                    // If we're past 15 seconds since scan initiated, force button activation
                    if (secondAdOverlay && 
                        (getComputedStyle(secondAdOverlay).display === 'flex' || 
                        getComputedStyle(secondAdOverlay).display === 'block')) {
                        enableButton();
                    }
                }
                
                // Periodically check the button's DOM presence
                viewResultsBtn = document.getElementById(config.buttonId);
                buttonContainer = document.getElementById(config.buttonContainerId);
                
                // If we're showing button but it somehow got disabled again, re-enable it
                if (viewResultsBtn && viewResultsBtn.disabled && hasScanned) {
                    enableButton();
                }
                
                // Do a full DOM inspection every 5 seconds for debugging
                if (Math.random() < 0.2) { // ~20% chance each check
                    inspectDOM();
                }
            }, config.inspectIntervalMs);
        }

        // Initialize
        function init() {
            viewResultsBtn = document.getElementById(config.buttonId);
            buttonContainer = document.getElementById(config.buttonContainerId);
            setupInspectionTimer();
            
            // Do initial check
            checkScanInitiated();
            
            // Handle form submission to detect scanning
            const form = document.getElementById('ticket-form');
            if (form) {
                form.addEventListener('submit', () => {
                    log('Form submitted - scan initiated');
                    hasScanned = true;
                    startButtonTimer();
                });
            }
            
            // Also watch for file input changes as another way to detect scanning
            const fileInput = document.getElementById('ticket-image');
            if (fileInput) {
                fileInput.addEventListener('change', () => {
                    log('File input changed - scan may be initiated');
                    hasScanned = true;
                    startButtonTimer();
                });
            }
        }

        // Start the fix
        init();
    }
})();