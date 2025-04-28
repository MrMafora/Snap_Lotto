/**
 * Critical Transition Fix - Ensures proper transition from first ad to second ad
 * This script specifically targets the issue where scanning gets stuck after the first ad
 * and doesn't show the second ad with results.
 */

// Self-executing function to avoid polluting global scope
(function() {
    // Set up detection for when first ad closes
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Critical transition fix loaded');
        
        // We need to ensure the transition from first ad to second ad happens properly
        // This function will directly monitor when the first ad closes
        function monitorFirstAdClosure() {
            const loadingOverlay = document.getElementById('ad-overlay-loading');
            
            // Create a mutation observer to detect when the first ad closes
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && 
                        mutation.attributeName === 'style' && 
                        mutation.target.style.display === 'none') {
                        
                        console.log('⚠️ Critical transition fix: First ad closed, ensuring second ad shows');
                        
                        // Force short delay to ensure proper sequencing
                        setTimeout(function() {
                            // Only proceed if we have results data
                            if (window.lastResultsData) {
                                const resultsOverlay = document.getElementById('ad-overlay-results');
                                if (resultsOverlay) {
                                    // Force the second ad to display
                                    resultsOverlay.style.display = 'flex';
                                    console.log('⚠️ Critical transition fix: Forced second ad to show');
                                    
                                    // Use AdManager if available
                                    if (window.AdManager && typeof window.AdManager.showInterstitialAd === 'function') {
                                        window.AdManager.showInterstitialAd(function() {
                                            console.log('⚠️ Critical transition fix: Called AdManager.showInterstitialAd');
                                        });
                                    }
                                }
                            }
                        }, 200);
                    }
                });
            });
            
            // Start observing the loading overlay for style changes
            if (loadingOverlay) {
                observer.observe(loadingOverlay, { attributes: true });
                console.log('⚠️ Critical transition fix: Now monitoring first ad for closure');
            }
        }
        
        // Start monitoring first ad immediately
        monitorFirstAdClosure();
        
        // Also add a backup check that runs after ticket scanning starts
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.addEventListener('click', function() {
                console.log('⚠️ Critical transition fix: Scan button clicked, adding backup check');
                
                // Add a backup timer to ensure second ad shows after first ad
                setTimeout(function() {
                    const loadingOverlay = document.getElementById('ad-overlay-loading');
                    const resultsOverlay = document.getElementById('ad-overlay-results');
                    
                    if (loadingOverlay && loadingOverlay.style.display === 'none' && 
                        resultsOverlay && resultsOverlay.style.display !== 'flex' && 
                        window.lastResultsData) {
                        
                        console.log('⚠️ Critical transition fix: BACKUP - First ad closed but second ad not shown');
                        
                        // Force show second ad
                        resultsOverlay.style.display = 'flex';
                        
                        // Use AdManager if available
                        if (window.AdManager && typeof window.AdManager.showInterstitialAd === 'function') {
                            window.AdManager.showInterstitialAd(function() {
                                console.log('⚠️ Critical transition fix: BACKUP - Called AdManager.showInterstitialAd');
                            });
                        }
                    }
                }, 8000); // Check 8 seconds after scan button clicked
            });
        }
        
        // Add a DOM-wide catch for first-to-second ad transition
        // This is the most aggressive approach for ensuring the transition works
        setInterval(function() {
            // Only check if we have scan results
            if (window.lastResultsData) {
                const loadingOverlay = document.getElementById('ad-overlay-loading');
                const resultsOverlay = document.getElementById('ad-overlay-results');
                
                // If loading ad is hidden but results ad is not showing, force it
                if (loadingOverlay && loadingOverlay.style.display === 'none' && 
                    resultsOverlay && resultsOverlay.style.display !== 'flex') {
                    
                    console.log('⚠️ Critical transition fix: INTERVAL - Detected missing second ad');
                    
                    // Force show second ad
                    resultsOverlay.style.display = 'flex';
                    
                    // Use AdManager if available
                    if (window.AdManager && typeof window.AdManager.showInterstitialAd === 'function') {
                        window.AdManager.showInterstitialAd(function() {
                            console.log('⚠️ Critical transition fix: INTERVAL - Called AdManager.showInterstitialAd');
                        });
                    }
                }
            }
        }, 1000); // Check every second
    });
})();