/**
 * Direct Checkmark Fix - Just forces hard text into the indicators
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Direct checkmark fix loaded");
    
    // Function to add checkmarks
    function forceCheckmarks() {
        const indicators = document.querySelectorAll('.match-indicator');
        if (indicators.length > 0) {
            console.log(`Found ${indicators.length} match indicators to fix`);
            indicators.forEach(indicator => {
                // Force checkmark text and style
                indicator.textContent = '✓';
                indicator.style.display = 'flex';
                indicator.style.alignItems = 'center';
                indicator.style.justifyContent = 'center';
                indicator.style.color = 'white';
                indicator.style.fontWeight = 'bold';
                indicator.style.fontSize = '10px';
                indicator.style.fontFamily = 'Arial, sans-serif';
                indicator.style.lineHeight = '1';
            });
            console.log("Checkmarks added directly");
        }
    }
    
    // Watch for the results to be shown
    const viewResultsBtn = document.getElementById('view-results-btn');
    if (viewResultsBtn) {
        viewResultsBtn.addEventListener('click', function() {
            console.log("View Results clicked, adding checkmarks soon");
            setTimeout(forceCheckmarks, 200);
        });
    }
    
    // Watch for DOM changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                setTimeout(forceCheckmarks, 100);
            }
        });
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Run initial check
    setTimeout(forceCheckmarks, 500);
    
    // Periodically check for indicators without text
    setInterval(forceCheckmarks, 1000);
});