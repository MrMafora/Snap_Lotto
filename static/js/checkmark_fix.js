/**
 * Simple Checkmark Fix for Lottery Application
 * This script ensures checkmarks are properly displayed on matched numbers
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Simple Checkmark Fix script loaded and active");

    // Watch for scan results to appear
    console.log("Watching for scan results to appear");
    
    // Helper function to add checkmarks to match indicators
    function addCheckmarksToMatchIndicators() {
        // Find all match indicators
        const matchIndicators = document.querySelectorAll('.match-indicator');
        
        // Add checkmark to each indicator
        matchIndicators.forEach(indicator => {
            // Only add content if it's empty
            if (!indicator.textContent || indicator.textContent.trim() === '') {
                indicator.textContent = '✓';
            }
        });
        
        console.log("Scan results detected, fixing checkmarks");
    }
    
    // Create an observer to watch for changes in the DOM
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // Check if any of the added nodes are match indicators or contain them
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    
                    // If it's an Element node
                    if (node.nodeType === 1) {
                        // If it's a match indicator itself
                        if (node.classList && node.classList.contains('match-indicator')) {
                            node.textContent = '✓';
                        }
                        
                        // If it contains match indicators
                        const indicators = node.querySelectorAll('.match-indicator');
                        if (indicators.length > 0) {
                            indicators.forEach(indicator => {
                                indicator.textContent = '✓';
                            });
                        }
                    }
                }
            }
        });
    });
    
    // Configure the observer to watch the entire document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Also check when page loads or ticket results are shown
    document.addEventListener('click', function(e) {
        // Check after "View Results" button is clicked
        if (e.target && (e.target.id === 'view-results-btn' || 
                         (e.target.parentNode && e.target.parentNode.id === 'view-results-btn'))) {
            console.log("User clicked View Results, applying checkmarks");
            
            // Use setTimeout to ensure DOM has been updated
            setTimeout(addCheckmarksToMatchIndicators, 100);
        }
    });
    
    // Initial check on page load
    setTimeout(addCheckmarksToMatchIndicators, 500);
});