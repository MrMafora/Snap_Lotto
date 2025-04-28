/**
 * Direct View Results button handler for Snap Lotto
 * 
 * This ensures that the View Results button always works by directly
 * attaching handlers when the page loads and after scanning a ticket.
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Keep track of if we've set up direct handlers
    window.directHandlersSetup = false;
    
    // Setup direct handlers on page load
    setupDirectHandlers();
    
    // Also set up a mutation observer to detect when new buttons are added to the DOM
    setupMutationObserver();
});

// Function to set up direct handlers
function setupDirectHandlers() {
    console.log('Setting up direct View Results button handlers');
    
    // Find all View Results buttons
    const viewResultsButtons = document.querySelectorAll('#view-results-btn');
    
    if (viewResultsButtons.length === 0) {
        console.log('No View Results buttons found, will try again later');
        return;
    }
    
    // Add direct click handler to all buttons
    viewResultsButtons.forEach(button => {
        // Remove any existing direct handlers by cloning
        const newButton = button.cloneNode(true);
        if (button.parentNode) {
            button.parentNode.replaceChild(newButton, button);
        }
        
        // Add a strong direct click handler
        newButton.addEventListener('click', directViewResultsHandler, true);
        
        // Mark this button as having our direct handler
        newButton.setAttribute('data-has-direct-handler', 'true');
        
        console.log('Direct handler attached to View Results button');
    });
    
    // Set flag to indicate we've set up the handlers
    window.directHandlersSetup = true;
}

// The direct handler function
function directViewResultsHandler(e) {
    console.log('🔵 DIRECT HANDLER: View Results button clicked at ' + new Date().toISOString());
    
    // Always stop event propagation and prevent default
    e.stopPropagation();
    e.preventDefault();
    
    // Mobile specific fix - Force the button text to update
    const viewResultsBtn = document.getElementById('view-results-btn');
    if (viewResultsBtn) {
        // Check if button text still contains "Wait" on mobile
        if (viewResultsBtn.innerText.includes('Wait')) {
            console.log('Mobile button still showing wait state, forcing update');
            viewResultsBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i> View Results Now!';
            viewResultsBtn.classList.remove('btn-secondary');
            viewResultsBtn.classList.add('btn-success');
        }
    }
    
    // Clear all possible timers
    for (let i = 1; i < 10000; i++) {
        clearTimeout(i);
        clearInterval(i);
    }
    
    // Clear known named timers
    if (window.countdownInterval) {
        clearInterval(window.countdownInterval);
        window.countdownInterval = null;
    }
    
    if (window.countdownTimeout) {
        clearTimeout(window.countdownTimeout);
        window.countdownTimeout = null;
    }
    
    if (window.adDisplayTimeout) {
        clearTimeout(window.adDisplayTimeout);
        window.adDisplayTimeout = null;
    }
    
    if (window.resultDisplayTimeout) {
        clearTimeout(window.resultDisplayTimeout);
        window.resultDisplayTimeout = null;
    }
    
    // Set all the required state flags
    window.countdownRunning = false;
    window.inResultsMode = true;
    window.showingResultsAfterAd = true;
    window.adClosed = true;
    window.viewResultsBtnClicked = true;
    window.resultsShown = true;
    window.hasCompletedAdFlow = true;
    window.permanentResultsMode = true;
    
    // Force hide all ad overlays
    document.querySelectorAll('[id^="ad-overlay"]').forEach(overlay => {
        overlay.style.display = 'none';
        overlay.style.opacity = '0';
        overlay.style.visibility = 'hidden';
    });
    
    // Find the results container
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
        // Make sure it's visible
        resultsContainer.classList.remove('d-none');
        resultsContainer.style.display = 'block';
        
        // If we have results data stored, display it
        if (window.lastResultsData) {
            console.log('Redisplaying stored results data from direct handler');
            
            // Check if displayResults function exists
            if (typeof displayResults === 'function') {
                displayResults(window.lastResultsData);
            } else {
                console.error('displayResults function not found!');
                
                // Try to manually activate the results display
                document.body.classList.add('showing-results');
                document.body.classList.add('results-mode');
                document.body.classList.add('ad-completed');
                document.body.classList.add('ad-closed');
            }
        } else {
            console.error('No results data found to display from direct handler');
        }
    }
    
    // Hide scan form
    const scanForm = document.getElementById('scan-form-container');
    if (scanForm) {
        scanForm.classList.add('d-none');
        scanForm.style.display = 'none';
    }
    
    // Make sure body scrolling is enabled
    if (typeof enableScrolling === 'function') {
        enableScrolling();
    } else {
        // Manual scrolling reset if function not found
        document.body.style.overflow = '';
        document.body.style.height = '';
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        document.documentElement.style.overflow = '';
        document.documentElement.style.height = '';
    }
    
    // Create a persistent monitor to keep results visible
    if (window.resultsMonitorInterval) {
        clearInterval(window.resultsMonitorInterval);
    }
    
    window.resultsMonitorInterval = setInterval(() => {
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer && resultsContainer.classList.contains('d-none')) {
            console.log('Results container was hidden, making visible again');
            resultsContainer.classList.remove('d-none');
            resultsContainer.style.display = 'block';
            
            // Force all ad overlays to stay hidden
            document.querySelectorAll('[id^="ad-overlay"]').forEach(overlay => {
                overlay.style.display = 'none';
            });
        }
    }, 1000); // Check every second
    
    return false;
}

// Set up a mutation observer to watch for View Results button being added
function setupMutationObserver() {
    // Create a new observer
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            // Check if any nodes were added
            if (mutation.addedNodes.length) {
                // Look for View Results button
                const viewResultsBtn = document.getElementById('view-results-btn');
                if (viewResultsBtn && !viewResultsBtn.hasAttribute('data-has-direct-handler')) {
                    console.log('View Results button detected in DOM, setting up direct handler');
                    setupDirectHandlers();
                }
            }
        });
    });
    
    // Start observing the document with the configured parameters
    observer.observe(document.body, { childList: true, subtree: true });
    
    console.log('Mutation observer set up to watch for View Results button');
}

// Periodically check for the button and attach handlers if needed
setInterval(() => {
    const viewResultsBtn = document.getElementById('view-results-btn');
    if (viewResultsBtn && !viewResultsBtn.hasAttribute('data-has-direct-handler')) {
        console.log('View Results button found without direct handler, reattaching');
        setupDirectHandlers();
    }
}, 2000); // Check every 2 seconds