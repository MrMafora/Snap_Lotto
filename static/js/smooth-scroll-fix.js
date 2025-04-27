/**
 * Smooth Scroll Fix for Snap Lotto Ticket Scanner
 * 
 * This script improves scrolling behavior throughout the ticket scanning process,
 * particularly during and after ad display and results viewing.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Smooth scroll fix applied');
    
    // Store original scroll position
    window.originalScrollY = 0;
    
    // Replace the existing disableScrolling function with an improved version
    window.disableScrolling = function() {
        // Store current scroll position before disabling
        window.originalScrollY = window.scrollY;
        
        // Apply scrolling lock with hardware acceleration
        document.body.style.position = 'fixed';
        document.body.style.top = `-${window.originalScrollY}px`;
        document.body.style.width = '100%';
        document.body.style.overflowY = 'scroll';
        document.body.classList.add('scrolling-disabled');
        
        console.log('Scrolling disabled, position saved:', window.originalScrollY);
    };
    
    // Replace the existing enableScrolling function with an improved version
    window.enableScrolling = function() {
        // Only proceed if scrolling is currently disabled
        if (!document.body.classList.contains('scrolling-disabled')) {
            console.log('Scrolling is already enabled, no action needed');
            return;
        }
        
        // Remove fixed positioning
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        document.body.style.overflowY = '';
        document.body.classList.remove('scrolling-disabled');
        
        // Restore the scroll position with smooth behavior
        if (window.originalScrollY !== undefined) {
            // Use both approaches for maximum compatibility
            window.scrollTo({
                top: window.originalScrollY,
                behavior: 'auto' // Use auto first for immediate positioning
            });
            
            // Then apply smooth scrolling after a slight delay
            setTimeout(() => {
                // If results are showing, scroll to results container
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer && !resultsContainer.classList.contains('d-none')) {
                    resultsContainer.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }, 50);
        }
        
        console.log('Scrolling enabled, position restored');
    };
    
    // Ensure we have a smooth scroll to the results container
    window.scrollToResults = function() {
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            // Enable scrolling first if it's disabled
            if (document.body.classList.contains('scrolling-disabled')) {
                enableScrolling();
            }
            
            // Scroll smoothly to the results
            setTimeout(() => {
                resultsContainer.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                console.log('Smoothly scrolled to results container');
            }, 100);
        }
    };
    
    // Add event listeners for visibility changes
    document.addEventListener('visibilitychange', function() {
        // If page becomes visible again and we're showing results, ensure scrolling is enabled
        if (!document.hidden && window.showingResultsAfterAd) {
            console.log('Page visible again, ensuring scrolling is enabled');
            enableScrolling();
            
            // Force scroll to results after a short delay
            setTimeout(scrollToResults, 200);
        }
    });
    
    // Monitor scroll position
    let lastKnownScrollY = window.scrollY;
    window.addEventListener('scroll', function() {
        // Only track scroll position when scrolling is enabled
        if (!document.body.classList.contains('scrolling-disabled')) {
            lastKnownScrollY = window.scrollY;
        }
    });
    
    // Periodic check to ensure scrolling is properly enabled in results mode
    setInterval(() => {
        if (window.showingResultsAfterAd && document.body.classList.contains('scrolling-disabled')) {
            console.log('Results showing but scrolling still disabled, fixing...');
            enableScrolling();
        }
    }, 2000);
    
    // Replace the view results button click handler with one that uses our improved scrolling
    const viewResultsBtns = document.querySelectorAll('#view-results-btn');
    viewResultsBtns.forEach(btn => {
        // Monitor for clicks with capture to ensure we get first access
        btn.addEventListener('click', function(e) {
            console.log('View Results clicked - ensuring smooth scrolling');
            
            // Ensure scrolling is enabled with our improved method
            enableScrolling();
            
            // After a short delay, scroll to the results 
            setTimeout(scrollToResults, 300);
        }, true);
    });
    
    console.log('Smooth scroll handlers attached to View Results buttons');
});