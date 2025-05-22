/**
 * Analysis Fixes Script
 * This script provides fixes for the lottery analysis tabs
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Analysis fixes script loaded");
    
    // Fix common Bootstrap 5 tab issues
    fixBootstrapTabs();
    
    // Fix fetchWithCSRF implementation if needed
    improveErrorHandling();
    
    // Add auto-repair capability for common content issues
    addContentRepairCapability();
    
    // Add event listeners for logging
    addDebugEventListeners();
});

/**
 * Fix issues with Bootstrap 5 tabs
 */
function fixBootstrapTabs() {
    // Ensure tab visibility is toggled properly
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const targetId = event.target.getAttribute('data-bs-target');
            const targetEl = document.querySelector(targetId);
            
            if (targetEl) {
                // Ensure content area is visible
                if (window.getComputedStyle(targetEl).display === 'none') {
                    console.warn(`Tab content ${targetId} is hidden, fixing...`);
                    targetEl.style.display = 'block';
                }
                
                // Check and load data for dynamic tabs
                if (targetId === '#patterns') {
                    ensurePatternDataLoaded();
                } else if (targetId === '#timeseries') {
                    ensureTimeSeriesDataLoaded();
                } else if (targetId === '#winners') {
                    ensureWinnersDataLoaded();
                } else if (targetId === '#correlations') {
                    ensureCorrelationsDataLoaded();
                }
            }
        });
    });
    
    console.log("Bootstrap tabs enhanced");
}

/**
 * Ensures pattern data is loaded when tab is activated
 */
function ensurePatternDataLoaded() {
    const contentEl = document.getElementById('patterns-content');
    const loadingEl = document.getElementById('patterns-loading');
    
    if (!contentEl || !loadingEl) {
        console.error("Pattern elements not found!");
        return;
    }
    
    // If no content is visible, try to load data
    if (contentEl.innerHTML.trim() === '' || contentEl.style.display === 'none') {
        console.log("Patterns tab appears empty, loading data...");
        
        // Make loading indicator visible
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // If loadPatternData exists, call it
        if (typeof loadPatternData === 'function') {
            loadPatternData();
        } else {
            console.error("loadPatternData function not found!");
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Error: Pattern analysis function not found.
                        Try refreshing the page.
                    </div>
                </div>
            `;
        }
    }
}

/**
 * Ensures time series data is loaded when tab is activated
 */
function ensureTimeSeriesDataLoaded() {
    const contentEl = document.getElementById('timeseries-content');
    const loadingEl = document.getElementById('timeseries-loading');
    
    if (!contentEl || !loadingEl) {
        console.error("Time series elements not found!");
        return;
    }
    
    // If no content is visible, try to load data
    if (contentEl.innerHTML.trim() === '' || contentEl.style.display === 'none') {
        console.log("Time Series tab appears empty, loading data...");
        
        // Make loading indicator visible
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // If loadTimeSeriesData exists, call it
        if (typeof loadTimeSeriesData === 'function') {
            loadTimeSeriesData();
        } else {
            console.error("loadTimeSeriesData function not found!");
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Error: Time series analysis function not found.
                        Try refreshing the page.
                    </div>
                </div>
            `;
        }
    }
}

/**
 * Ensures winners data is loaded when tab is activated
 */
function ensureWinnersDataLoaded() {
    const contentEl = document.getElementById('winners-content');
    const loadingEl = document.getElementById('winners-loading');
    
    if (!contentEl || !loadingEl) {
        console.error("Winners elements not found!");
        return;
    }
    
    // If no content is visible, try to load data
    if (contentEl.innerHTML.trim() === '' || contentEl.style.display === 'none') {
        console.log("Winners tab appears empty, loading data...");
        
        // Make loading indicator visible
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // If loadWinnerData exists, call it
        if (typeof loadWinnerData === 'function') {
            loadWinnerData();
        } else {
            console.error("loadWinnerData function not found!");
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Error: Winner analysis function not found.
                        Try refreshing the page.
                    </div>
                </div>
            `;
        }
    }
}

/**
 * Ensures correlations data is loaded when tab is activated
 */
function ensureCorrelationsDataLoaded() {
    const contentEl = document.getElementById('correlations-content');
    const loadingEl = document.getElementById('correlations-loading');
    
    if (!contentEl || !loadingEl) {
        console.error("Correlations elements not found!");
        return;
    }
    
    // If no content is visible, try to load data
    if (contentEl.innerHTML.trim() === '' || contentEl.style.display === 'none') {
        console.log("Correlations tab appears empty, loading data...");
        
        // Make loading indicator visible
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // If loadCorrelationData exists, call it
        if (typeof loadCorrelationData === 'function') {
            loadCorrelationData();
        } else {
            console.error("loadCorrelationData function not found!");
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Error: Correlation analysis function not found.
                        Try refreshing the page.
                    </div>
                </div>
            `;
        }
    }
}

/**
 * Improve error handling for fetchWithCSRF
 */
function improveErrorHandling() {
    if (typeof window.fetchWithCSRF !== 'function') {
        console.warn("fetchWithCSRF not found, cannot enhance");
        return;
    }
    
    // Store original implementation
    const originalFetch = window.fetchWithCSRF;
    
    // Create enhanced version
    window.fetchWithCSRF = function(url, options = {}) {
        console.log(`Enhanced fetchWithCSRF called for ${url}`);
        
        return originalFetch(url, options)
            .catch(error => {
                console.error(`Network error in fetchWithCSRF for ${url}:`, error);
                
                // Provide a more detailed error for UI handling
                const enhancedError = new Error(`Network request failed: ${error.message}`);
                enhancedError.originalError = error;
                enhancedError.url = url;
                enhancedError.isNetworkError = true;
                enhancedError.timestamp = new Date().toISOString();
                
                throw enhancedError;
            });
    };
    
    console.log("fetchWithCSRF has been enhanced with better error handling");
}

/**
 * Add auto-repair capability for content areas
 */
function addContentRepairCapability() {
    // Check content areas periodically
    setInterval(() => {
        const activeTab = document.querySelector('.tab-pane.show.active');
        if (!activeTab) return;
        
        const contentId = activeTab.id;
        const contentEl = document.getElementById(`${contentId}-content`);
        const loadingEl = document.getElementById(`${contentId}-loading`);
        
        if (!contentEl || !loadingEl) return;
        
        // If content area is empty but tab is active, try to repair
        if (contentEl.innerHTML.trim() === '' && 
            window.getComputedStyle(contentEl).display === 'none' && 
            window.getComputedStyle(loadingEl).display === 'none') {
            
            console.warn(`Found empty content in active tab ${contentId}, repairing...`);
            
            // Show loading indicator
            loadingEl.style.display = 'block';
            
            // Call appropriate loader function
            if (contentId === 'patterns' && typeof loadPatternData === 'function') {
                loadPatternData();
            } else if (contentId === 'timeseries' && typeof loadTimeSeriesData === 'function') {
                loadTimeSeriesData();
            } else if (contentId === 'winners' && typeof loadWinnerData === 'function') {
                loadWinnerData();
            } else if (contentId === 'correlations' && typeof loadCorrelationData === 'function') {
                loadCorrelationData();
            }
        }
    }, 2000);
    
    console.log("Content auto-repair system activated");
}

/**
 * Add event listeners for debugging
 */
function addDebugEventListeners() {
    // Monitor tab changes
    document.addEventListener('shown.bs.tab', function(event) {
        const targetId = event.target.getAttribute('data-bs-target');
        console.log(`Tab changed to ${targetId}`);
    });
    
    // Better error logging for unhandled promises
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        event.preventDefault(); // Prevent default handling
    });
    
    console.log("Debug event listeners added");
}