/**
 * iOS Early Fix - Executes before page is fully loaded
 * Ensures mobile devices don't get stuck in advertisement loops
 */
 
// This script is designed to execute as early as possible during page loading
(function() {
    console.log("iOS early fix loaded");
    
    // Handle iOS-specific issues with scanning process
    function setupEarlyFixHandlers() {
        // Create a global emergency function that can be called from console
        window.emergencyAdvanceScanner = function() {
            console.log("Emergency scanner advancement triggered");
            
            // Force hide loading overlay
            var loadingOverlay = document.getElementById('ad-overlay-loading');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
            
            // Force show results overlay
            var resultsOverlay = document.getElementById('ad-overlay-results');
            if (resultsOverlay) {
                resultsOverlay.style.display = 'flex';
            }
            
            return "Emergency scanner advancement initiated";
        };
        
        // Ensure loading overlay disappears after a maximum timeout
        setTimeout(function() {
            var loadingOverlay = document.getElementById('ad-overlay-loading');
            if (loadingOverlay && loadingOverlay.style.display !== 'none') {
                console.log("iOS early fix: Force hiding ad-overlay-loading after maximum timeout");
                loadingOverlay.style.display = 'none';
                
                // Also check if we need to show the results overlay
                if (window.lastResultsData) {
                    var resultsOverlay = document.getElementById('ad-overlay-results');
                    if (resultsOverlay) {
                        resultsOverlay.style.display = 'flex';
                    }
                }
            }
        }, 25000); // 25 seconds maximum
    }
    
    // Set up handlers when DOM is ready or immediately if already loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupEarlyFixHandlers);
    } else {
        setupEarlyFixHandlers();
    }
})();