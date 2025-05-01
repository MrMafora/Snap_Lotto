/**
 * Button Inspector and Fixer
 * 
 * This diagnostic script directly inspects the button elements in the DOM,
 * reports their current state, and forcibly shows the button after a delay.
 */
(function() {
    'use strict';
    
    console.log('📋 Button Inspector loaded');
    
    // Wait until DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initInspector);
    } else {
        initInspector();
    }
    
    function initInspector() {
        console.log('🔍 Initializing Button Inspector');
        
        // Scan DOM for critical elements
        setTimeout(inspectElements, 1000);
        
        // Force button visibility after a delay
        setTimeout(forceButtonVisibility, 10000);
    }
    
    function inspectElements() {
        console.log('📊 Inspecting DOM elements:');
        
        // Check button container
        const btnContainer = document.getElementById('view-results-btn-container');
        if (btnContainer) {
            console.log('✅ Button container found: ', {
                id: btnContainer.id,
                display: btnContainer.style.display,
                visibility: btnContainer.style.visibility,
                classes: btnContainer.className,
                parent: btnContainer.parentElement?.tagName
            });
        } else {
            console.log('❌ Button container NOT found (view-results-btn-container)');
        }
        
        // Check button itself
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            console.log('✅ Button element found: ', {
                id: viewResultsBtn.id,
                display: viewResultsBtn.style.display,
                visibility: viewResultsBtn.style.visibility,
                disabled: viewResultsBtn.disabled,
                classes: viewResultsBtn.className,
                text: viewResultsBtn.innerText || viewResultsBtn.textContent
            });
        } else {
            console.log('❌ Button element NOT found (view-results-btn)');
        }
        
        // Check ad overlays
        const firstAdOverlay = document.getElementById('ad-overlay-loading');
        if (firstAdOverlay) {
            console.log('ℹ️ First ad overlay:', {
                display: firstAdOverlay.style.display,
                visibility: firstAdOverlay.style.visibility
            });
        }
        
        const secondAdOverlay = document.getElementById('ad-overlay-results');
        if (secondAdOverlay) {
            console.log('ℹ️ Second ad overlay:', {
                display: secondAdOverlay.style.display,
                visibility: secondAdOverlay.style.visibility
            });
        }
        
        // Schedule another inspection in 5 seconds
        setTimeout(inspectElements, 5000);
    }
    
    function forceButtonVisibility() {
        console.log('🔨 Forcing button visibility');
        
        // Make sure the button container is visible
        const btnContainer = document.getElementById('view-results-btn-container');
        if (btnContainer) {
            console.log('Making container visible');
            btnContainer.style.display = 'block';
            btnContainer.style.visibility = 'visible';
            btnContainer.style.opacity = '1';
        } else {
            console.log('⚠️ Cannot find button container to force visibility');
        }
        
        // Force button to be visible and enabled
        const viewResultsBtn = document.getElementById('view-results-btn');
        if (viewResultsBtn) {
            console.log('Enabling button');
            viewResultsBtn.disabled = false;
            viewResultsBtn.style.visibility = 'visible';
            viewResultsBtn.style.display = 'block';
            viewResultsBtn.style.opacity = '1';
            viewResultsBtn.classList.remove('btn-secondary');
            viewResultsBtn.classList.add('btn-success', 'btn-pulse');
            viewResultsBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
            
            // Add click handler
            viewResultsBtn.addEventListener('click', function(e) {
                console.log('Forced button clicked');
                
                // Hide ad overlay
                const adOverlay = document.getElementById('ad-overlay-results');
                if (adOverlay) {
                    adOverlay.style.display = 'none';
                }
                
                // Show results container
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer) {
                    resultsContainer.classList.remove('d-none');
                    resultsContainer.style.display = 'block';
                }
                
                // Set global state
                window.inResultsMode = true;
                window.adClosed = true;
                window.viewResultsBtnClicked = true;
            });
        } else {
            console.log('⚠️ Cannot find button to force visibility');
        }
        
        console.log('🏁 Visibility forcing complete');
    }
})();