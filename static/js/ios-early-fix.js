/**
 * iOS Early Fix - Ensures loading process starts before DOM is fully loaded
 * This critical script executes as early as possible to prevent iOS-specific issues
 * with the scan advancement process.
 */

// Create global flags to help track scanning state
window.isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
window.iosScanInitialized = false;
window.iosLoadingFixApplied = false;
window.iosResultsFixApplied = false;
window.forcedAdvancement = false;
window.lastResultsData = null;  // For storing scan results

// Setup early iOS-specific fixes
(function() {
    // Execute specific iOS fixes earlier than DOMContentLoaded
    if (window.isIOS) {
        console.log('iOS device detected, applying early fixes');
        
        // Add max timeout to force-hide loading overlay if it gets stuck (10 seconds)
        setTimeout(function() {
            console.log('iOS early fix: Force hiding ad-overlay-loading after maximum timeout');
            const loadingOverlay = document.getElementById('ad-overlay-loading');
            if (loadingOverlay && loadingOverlay.style.display !== 'none') {
                loadingOverlay.style.display = 'none';
                
                // CRITICAL FIX: If we have results data, explicitly show the results overlay
                if (window.lastResultsData) {
                    const resultsOverlay = document.getElementById('ad-overlay-results');
                    if (resultsOverlay) {
                        resultsOverlay.style.display = 'flex';
                        console.log('iOS early fix: Forced display of results overlay');
                        window.iosResultsFixApplied = true;
                    }
                }
            }
        }, 10000);
        
        // Add observer to detect when loading ad overlay is hidden
        document.addEventListener('DOMContentLoaded', function() {
            // Setup a mutation observer to watch for when loading ad is hidden
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && 
                        mutation.attributeName === 'style' && 
                        mutation.target.style.display === 'none') {
                        
                        console.log('iOS early fix: Detected loading overlay hidden');
                        
                        // CRITICAL FIX: If we have results data, show the results overlay
                        if (window.lastResultsData && !window.iosResultsFixApplied) {
                            const resultsOverlay = document.getElementById('ad-overlay-results');
                            if (resultsOverlay && resultsOverlay.style.display !== 'flex') {
                                // Force short delay to ensure proper sequencing
                                setTimeout(function() {
                                    resultsOverlay.style.display = 'flex';
                                    console.log('iOS early fix: Forced display of results overlay after loading ad closed');
                                    window.iosResultsFixApplied = true;
                                }, 100);
                            }
                        }
                    }
                });
            });
            
            // Start observing loading overlay
            const loadingOverlay = document.getElementById('ad-overlay-loading');
            if (loadingOverlay) {
                observer.observe(loadingOverlay, { attributes: true });
                console.log('iOS early fix: Now observing loading overlay');
            }
        });
    }
})();