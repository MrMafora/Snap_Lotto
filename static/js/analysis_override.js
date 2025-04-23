/**
 * Analysis Override Script
 * This script provides direct overrides for core analysis functionality
 * Enhanced with additional debug logging
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Analysis override script loaded");
    
    // Log tab and API information
    console.log("Current URL: " + window.location.href);
    console.log("Tab structure inspection:");
    
    try {
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        console.log(`- Tab ID: ${tab.id}, Target: ${tab.getAttribute('data-bs-target')}`);
    });
    
    // Find which tab is currently active
    const activeTab = document.querySelector('[data-bs-toggle="tab"].active');
    console.log("Initial active tab:", activeTab ? activeTab.id : "None");
    
    // Log API availability for all endpoints
    checkApiAvailability();
    
    // Directly add click handlers to all tabs
    setupDirectTabHandlers();
    
    // Set up direct fetch functions
    setupDirectFetchFunctions();
    
    // Add specific handler for manual tab switching
    addManualTabSwitchHandler();
    
    // Force both Pattern Analysis and Time Series tabs to load immediately
    console.log("Forcing immediate data load for tabs");
    
    // Stagger the loads to avoid overwhelming the server
    setTimeout(function() {
        console.log("Executing delayed Pattern Analysis data load");
        loadPatternsDirectly();
    }, 1000);
    
    setTimeout(function() {
        console.log("Executing delayed Time Series data load");
        loadTimeSeriesDirectly();
    }, 2000);
    
    // Finally ensure the active tab is loaded
    setTimeout(loadActiveTabData, 2500);
    
    // Add debugging information display
    setTimeout(function() {
        // Add diagnostic message at the top of the page
        const debugElement = document.createElement('div');
        debugElement.className = 'alert alert-info mt-2 mb-2';
        debugElement.innerHTML = `
            <h6>Debug Info: Tab Switching Enhanced (v2.0)</h6>
            <p>If the tabs don't switch correctly, please try:</p>
            <ol class="mb-0">
                <li>Using the direct buttons below</li>
                <li>Clicking the manual tab links</li>
                <li>Refreshing the page</li>
            </ol>
        `;
        
        // Insert after the page heading
        const heading = document.querySelector('.d-sm-flex.align-items-center');
        if (heading && heading.parentNode) {
            heading.parentNode.insertBefore(debugElement, heading.nextSibling);
        }
    }, 3000);
    
    } catch (error) {
        console.error("Error during tab analysis initialization:", error);
        
        // Add error message to the top of the page
        try {
            const errorElement = document.createElement('div');
            errorElement.className = 'alert alert-danger mt-2 mb-2';
            errorElement.innerHTML = `
                <h6>Error Initializing Tab System</h6>
                <p>${error.message}</p>
                <p>Please try refreshing the page. If the problem persists, contact support.</p>
            `;
            
            const container = document.querySelector('.container-fluid');
            if (container) {
                container.insertBefore(errorElement, container.firstChild);
            }
        } catch (displayError) {
            console.error("Could not display error message:", displayError);
        }
    }
});

// Check all API endpoints
function checkApiAvailability() {
    const endpoints = [
        '/api/lottery-analysis/patterns?lottery_type=&days=365',
        '/api/lottery-analysis/time-series?lottery_type=&days=365'
    ];
    
    endpoints.forEach(endpoint => {
        try {
            fetch(endpoint)
                .then(response => {
                    console.log(`API endpoint ${endpoint} status:`, response.status, response.ok);
                    return response.ok;
                })
                .catch(error => {
                    console.error(`API endpoint ${endpoint} check failed:`, error);
                });
        } catch (error) {
            console.error(`Error checking API ${endpoint}:`, error);
        }
    });
}

// Add manual tab switching buttons to help users if Bootstrap tabs don't work
function addManualTabSwitchHandler() {
    // Add manual tab switching buttons
    const tabContainer = document.querySelector('ul.nav-tabs');
    if (tabContainer) {
        const manualSwitchDiv = document.createElement('div');
        manualSwitchDiv.className = 'manual-tab-switch mt-2 mb-2';
        manualSwitchDiv.innerHTML = `
            <div class="alert alert-info">
                <p class="mb-2">If tabs aren't working, use these direct links:</p>
                <div class="d-flex flex-wrap">
                    <button class="btn btn-sm btn-outline-primary mr-1 mb-1" data-target="frequency">Number Frequency</button>
                    <button class="btn btn-sm btn-outline-primary mr-1 mb-1" data-target="patterns">Pattern Analysis</button>
                    <button class="btn btn-sm btn-outline-primary mr-1 mb-1" data-target="timeseries">Time Series</button>
                    <button class="btn btn-sm btn-outline-primary mr-1 mb-1" data-target="winners">Winner Analysis</button>
                    <button class="btn btn-sm btn-outline-primary mr-1 mb-1" data-target="correlations">Lottery Correlations</button>
                </div>
            </div>
        `;
        
        tabContainer.parentNode.insertBefore(manualSwitchDiv, tabContainer.nextSibling);
        
        // Add event listeners to the buttons
        const buttons = manualSwitchDiv.querySelectorAll('button');
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                console.log(`Manual switch to tab: ${targetId}`);
                
                // Hide all content
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active');
                    pane.classList.remove('show');
                });
                
                // Show selected content
                const targetPane = document.getElementById(targetId);
                if (targetPane) {
                    targetPane.classList.add('active');
                    targetPane.classList.add('show');
                    
                    // Also update tab selection
                    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
                        tab.classList.remove('active');
                        tab.setAttribute('aria-selected', 'false');
                        
                        if (tab.getAttribute('data-bs-target') === `#${targetId}`) {
                            tab.classList.add('active');
                            tab.setAttribute('aria-selected', 'true');
                        }
                    });
                    
                    // Load data if needed
                    loadTabData(targetId);
                }
            });
        });
    }
}

/**
 * Set up direct handlers for tabs without relying on Bootstrap JS
 */
function setupDirectTabHandlers() {
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Get target tab ID
            const targetId = this.getAttribute('data-bs-target');
            if (!targetId) return;
            
            // Hide all tab panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
                pane.classList.remove('show');
            });
            
            // Show target tab pane
            const targetPane = document.querySelector(targetId);
            if (targetPane) {
                targetPane.classList.add('active');
                targetPane.classList.add('show');
            }
            
            // Update tab button states
            tabs.forEach(t => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');
            
            // Load data for the tab
            console.log(`Direct tab handler activated for ${targetId}`);
            loadTabData(targetId.substring(1)); // Remove the # prefix
        });
    });
    
    // Set up direct button handlers
    setupDirectTabButtons();
    
    console.log("Direct tab handlers established");
}

/**
 * Set up handlers for the direct tab buttons 
 */
function setupDirectTabButtons() {
    // Map button IDs to tab pane IDs
    const buttonMappings = {
        'direct-frequency-btn': 'frequency',
        'direct-patterns-btn': 'patterns',
        'direct-timeseries-btn': 'timeseries',
        'direct-winners-btn': 'winners',
        'direct-correlations-btn': 'correlations'
    };
    
    // Add click handlers to each direct button
    Object.entries(buttonMappings).forEach(([buttonId, tabId]) => {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', function() {
                console.log(`Direct button clicked: ${buttonId} for tab ${tabId}`);
                
                // Remove active class from all tabs
                document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
                    tab.classList.remove('active');
                    tab.setAttribute('aria-selected', 'false');
                });
                
                // Add active class to corresponding tab
                const tab = document.querySelector(`[data-bs-target="#${tabId}"]`);
                if (tab) {
                    tab.classList.add('active');
                    tab.setAttribute('aria-selected', 'true');
                }
                
                // Hide all tab panes
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('show');
                    pane.classList.remove('active');
                });
                
                // Show target tab pane
                const targetPane = document.getElementById(tabId);
                if (targetPane) {
                    targetPane.classList.add('show');
                    targetPane.classList.add('active');
                    
                    // Load data for this tab
                    loadTabData(tabId);
                } else {
                    console.error(`Target tab pane #${tabId} not found`);
                }
            });
            console.log(`Attached handler to direct button: ${buttonId}`);
        } else {
            console.warn(`Direct button #${buttonId} not found in the DOM`);
        }
    });
}

/**
 * Set up direct fetch functions without dependencies
 */
function setupDirectFetchFunctions() {
    // Define a global fetch function that handles CSRF tokens
    window.directFetch = function(url) {
        console.log(`Direct fetch called for ${url}`);
        
        // Add CSRF token if available
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        console.log('CSRF token found:', token ? 'Yes' : 'No');
        
        // Create simpler headers that won't cause CORS issues
        const headers = {
            'X-Requested-With': 'XMLHttpRequest'
        };
        
        if (token) {
            headers['X-CSRFToken'] = token;
        }
        
        console.log('Request headers:', headers);
        
        // Use a simpler fetch approach
        return fetch(url, {
            method: 'GET',
            headers: headers,
            credentials: 'same-origin',
            cache: 'no-store'
        })
        .then(response => {
            console.log(`Response for ${url}:`, {
                status: response.status,
                ok: response.ok,
                statusText: response.statusText,
                contentType: response.headers.get('content-type')
            });
            return response;
        })
        .catch(error => {
            console.error(`Network error in directFetch for ${url}:`, error);
            throw new Error(`Network request failed: ${error.message}`);
        });
    };
    
    console.log("Direct fetch function established");
}

/**
 * Load data for active tab on page load
 */
function loadActiveTabData() {
    const activePane = document.querySelector('.tab-pane.active');
    if (activePane) {
        console.log(`Loading data for initially active tab: ${activePane.id}`);
        loadTabData(activePane.id);
    }
}

/**
 * Load data for a specific tab
 */
function loadTabData(tabId) {
    console.log(`Loading data for tab ${tabId}`);
    
    switch (tabId) {
        case 'patterns':
            loadPatternsDirectly();
            break;
        case 'timeseries':
            loadTimeSeriesDirectly();
            break;
        case 'winners':
            loadWinnersDirectly();
            break;
        case 'correlations':
            loadCorrelationsDirectly();
            break;
        default:
            console.log(`No data loading required for tab ${tabId}`);
    }
}

/**
 * Directly load patterns data without dependencies
 */
function loadPatternsDirectly() {
    const contentEl = document.getElementById('patterns-content');
    const loadingEl = document.getElementById('patterns-loading');
    
    if (!contentEl || !loadingEl) {
        console.error("Pattern elements not found");
        return;
    }
    
    // Show loading indicator
    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';
    
    // Get parameters
    const lotteryTypeSelect = document.getElementById('lottery_type');
    const daysSelect = document.getElementById('days');
    const lotteryType = lotteryTypeSelect ? lotteryTypeSelect.value || '' : '';
    const days = daysSelect ? daysSelect.value || '365' : '365';
    
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    const url = `/api/lottery-analysis/patterns?lottery_type=${encodeURIComponent(lotteryType)}&days=${encodeURIComponent(days)}&_ts=${timestamp}`;
    
    console.log(`Loading patterns from URL: ${url}`);
    
    // Update loading message with more detail
    loadingEl.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Loading...</span>
        </div>
        <p class="mt-2">Loading pattern analysis data...</p>
        <p class="small text-muted">Request URL: ${url}</p>
    `;
    
    // Fetch data directly
    directFetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Log the raw response text for debugging
            return response.text().then(text => {
                console.log("Raw API response text:", text.substring(0, 500) + "..."); // Log first 500 chars
                
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error("JSON parse error:", e);
                    throw new Error(`JSON parsing failed: ${e.message}. Raw response starts with: ${text.substring(0, 100)}`);
                }
            });
        })
        .then(data => {
            console.log("Pattern data received:", data);
            let html = '';
            
            if (data && Object.keys(data).length > 0) {
                // Process each lottery type
                for (const [lotteryType, typeData] of Object.entries(data)) {
                    if (!typeData || typeData.error) {
                        html += `
                            <div class="col-md-6 mb-4">
                                <div class="card border-left-warning shadow h-100 py-2">
                                    <div class="card-body">
                                        <div class="row no-gutters align-items-center">
                                            <div class="col mr-2">
                                                <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                                                    ${lotteryType}
                                                </div>
                                                <div class="h5 mb-0 font-weight-bold text-gray-800">
                                                    No Pattern Data
                                                </div>
                                                <div class="mt-2">
                                                    <p>${typeData?.error || 'Insufficient data for pattern analysis.'}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                        continue;
                    }
                    
                    // Create pattern card for valid data
                    html += `
                        <div class="col-md-6 mb-4">
                            <div class="card border-left-primary shadow h-100 py-2">
                                <div class="card-body">
                                    <div class="row no-gutters align-items-center">
                                        <div class="col mr-2">
                                            <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                                                ${lotteryType}
                                            </div>
                                            <div class="h5 mb-0 font-weight-bold text-gray-800">
                                                Pattern Analysis
                                            </div>
                                            <div class="mt-2">
                                                <img src="data:image/png;base64,${typeData.chart_base64}" 
                                                    alt="Pattern Analysis for ${lotteryType}" 
                                                    class="img-fluid">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            } else {
                html = `
                    <div class="col-12">
                        <div class="alert alert-info">
                            No data available for pattern analysis. Please ensure there are lottery results in the database.
                        </div>
                    </div>
                `;
            }
            
            // Set the HTML
            contentEl.innerHTML = html;
            
            // Make sure content becomes visible
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        })
        .catch(error => {
            console.error("Error loading pattern data:", error);
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <h5>Error Loading Pattern Analysis</h5>
                        <p>There was a problem loading the pattern analysis data: ${error.message}</p>
                        <p>Please try refreshing the page or selecting different filters.</p>
                    </div>
                </div>
            `;
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        });
}

/**
 * Directly load time series data without dependencies
 */
function loadTimeSeriesDirectly() {
    const contentEl = document.getElementById('timeseries-content');
    const loadingEl = document.getElementById('timeseries-loading');
    
    if (!contentEl || !loadingEl) {
        console.error("Time series elements not found");
        return;
    }
    
    // Show loading indicator
    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';
    
    // Get parameters
    const lotteryTypeSelect = document.getElementById('lottery_type');
    const daysSelect = document.getElementById('days');
    const lotteryType = lotteryTypeSelect ? lotteryTypeSelect.value || '' : '';
    const days = daysSelect ? daysSelect.value || '365' : '365';
    
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    const url = `/api/lottery-analysis/time-series?lottery_type=${encodeURIComponent(lotteryType)}&days=${encodeURIComponent(days)}&_ts=${timestamp}`;
    
    console.log(`Loading time series from URL: ${url}`);
    
    // Update loading message with more detail
    loadingEl.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Loading...</span>
        </div>
        <p class="mt-2">Loading time series data...</p>
        <p class="small text-muted">Request URL: ${url}</p>
    `;
    
    // Fetch data directly
    directFetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Log the raw response text for debugging
            return response.text().then(text => {
                console.log("Raw Time Series API response text:", text.substring(0, 500) + "..."); // Log first 500 chars
                
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error("JSON parse error:", e);
                    throw new Error(`JSON parsing failed: ${e.message}. Raw response starts with: ${text.substring(0, 100)}`);
                }
            });
        })
        .then(data => {
            console.log("Time series data received:", data);
            let html = '';
            
            if (data && Object.keys(data).length > 0) {
                // Process each lottery type
                for (const [lotteryType, typeData] of Object.entries(data)) {
                    if (!typeData || typeData.error) {
                        html += `
                            <div class="col-md-6 mb-4">
                                <div class="card border-left-warning shadow h-100 py-2">
                                    <div class="card-body">
                                        <div class="row no-gutters align-items-center">
                                            <div class="col mr-2">
                                                <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                                                    ${lotteryType}
                                                </div>
                                                <div class="h5 mb-0 font-weight-bold text-gray-800">
                                                    No Time Series Data
                                                </div>
                                                <div class="mt-2">
                                                    <p>${typeData?.error || 'Insufficient data for time series analysis.'}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                        continue;
                    }
                    
                    // Create time series card for valid data
                    html += `
                        <div class="col-md-6 mb-4">
                            <div class="card border-left-info shadow h-100 py-2">
                                <div class="card-body">
                                    <div class="row no-gutters align-items-center">
                                        <div class="col mr-2">
                                            <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
                                                ${lotteryType}
                                            </div>
                                            <div class="h5 mb-0 font-weight-bold text-gray-800">
                                                Time Series Analysis
                                            </div>
                                            <div class="mt-2">
                                                <img src="data:image/png;base64,${typeData.chart_base64}" 
                                                    alt="Time Series Analysis for ${lotteryType}" 
                                                    class="img-fluid">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            } else {
                html = `
                    <div class="col-12">
                        <div class="alert alert-info">
                            No data available for time series analysis. Please ensure there are lottery results in the database.
                        </div>
                    </div>
                `;
            }
            
            // Set the HTML
            contentEl.innerHTML = html;
            
            // Make sure content becomes visible
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        })
        .catch(error => {
            console.error("Error loading time series data:", error);
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <h5>Error Loading Time Series Analysis</h5>
                        <p>There was a problem loading the time series data: ${error.message}</p>
                        <p>Please try refreshing the page or selecting different filters.</p>
                    </div>
                </div>
            `;
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        });
}

/**
 * Directly load winners data without dependencies
 */
function loadWinnersDirectly() {
    const contentEl = document.getElementById('winners-content');
    const loadingEl = document.getElementById('winners-loading');
    
    if (!contentEl || !loadingEl) {
        console.error("Winners elements not found");
        return;
    }
    
    // Show loading indicator
    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';
    
    // Get parameters
    const lotteryTypeSelect = document.getElementById('lottery_type');
    const daysSelect = document.getElementById('days');
    const lotteryType = lotteryTypeSelect ? lotteryTypeSelect.value || '' : '';
    const days = daysSelect ? daysSelect.value || '365' : '365';
    
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    const url = `/api/lottery-analysis/winners?lottery_type=${encodeURIComponent(lotteryType)}&days=${encodeURIComponent(days)}&_ts=${timestamp}`;
    
    console.log(`Loading winners from URL: ${url}`);
    
    // Update loading message with more detail
    loadingEl.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Loading...</span>
        </div>
        <p class="mt-2">Loading winners data...</p>
        <p class="small text-muted">Request URL: ${url}</p>
    `;
    
    // Fetch data directly
    directFetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Log the raw response text for debugging
            return response.text().then(text => {
                console.log("Raw Winners API response text:", text.substring(0, 500) + "..."); // Log first 500 chars
                
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error("JSON parse error:", e);
                    throw new Error(`JSON parsing failed: ${e.message}. Raw response starts with: ${text.substring(0, 100)}`);
                }
            });
        })
        .then(data => {
            console.log("Winners data received:", data);
            let html = '';
            
            if (data && Object.keys(data).length > 0) {
                // Process each lottery type
                for (const [lotteryType, typeData] of Object.entries(data)) {
                    if (!typeData || typeData.error) {
                        html += `
                            <div class="col-md-6 mb-4">
                                <div class="card border-left-warning shadow h-100 py-2">
                                    <div class="card-body">
                                        <div class="row no-gutters align-items-center">
                                            <div class="col mr-2">
                                                <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                                                    ${lotteryType}
                                                </div>
                                                <div class="h5 mb-0 font-weight-bold text-gray-800">
                                                    No Winners Data
                                                </div>
                                                <div class="mt-2">
                                                    <p>${typeData?.error || 'Insufficient data for winners analysis.'}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                        continue;
                    }
                    
                    // Create winners card for valid data
                    html += `
                        <div class="col-md-6 mb-4">
                            <div class="card border-left-success shadow h-100 py-2">
                                <div class="card-body">
                                    <div class="row no-gutters align-items-center">
                                        <div class="col mr-2">
                                            <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                                                ${lotteryType}
                                            </div>
                                            <div class="h5 mb-0 font-weight-bold text-gray-800">
                                                Winners Analysis
                                            </div>
                                            <div class="mt-2">
                                                ${typeData.chart_base64 ? 
                                                    `<img src="data:image/png;base64,${typeData.chart_base64}" 
                                                        alt="Winners Analysis for ${lotteryType}" 
                                                        class="img-fluid">` :
                                                    `<p>No visualization available</p>`
                                                }
                                                ${typeData.winners_table ? 
                                                    `<div class="mt-3">${typeData.winners_table}</div>` :
                                                    `<p>No winners table available</p>`
                                                }
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            } else {
                html = `
                    <div class="col-12">
                        <div class="alert alert-info">
                            No data available for winners analysis. Please ensure there are lottery results in the database.
                        </div>
                    </div>
                `;
            }
            
            // Set the HTML
            contentEl.innerHTML = html;
            
            // Make sure content becomes visible
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        })
        .catch(error => {
            console.error("Error loading winners data:", error);
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <h5>Error Loading Winners Analysis</h5>
                        <p>There was a problem loading the winners data: ${error.message}</p>
                        <p>Please try refreshing the page or selecting different filters.</p>
                    </div>
                </div>
            `;
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        });
}

/**
 * Directly load correlations data without dependencies
 */
function loadCorrelationsDirectly() {
    const contentEl = document.getElementById('correlations-content');
    const loadingEl = document.getElementById('correlations-loading');
    
    if (!contentEl || !loadingEl) {
        console.error("Correlations elements not found");
        return;
    }
    
    // Show loading indicator
    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';
    
    // Get parameters
    const daysSelect = document.getElementById('days');
    const days = daysSelect ? daysSelect.value || '365' : '365';
    
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    const url = `/api/lottery-analysis/correlations?days=${encodeURIComponent(days)}&_ts=${timestamp}`;
    
    console.log(`Loading correlations from URL: ${url}`);
    
    // Update loading message with more detail
    loadingEl.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Loading...</span>
        </div>
        <p class="mt-2">Loading correlations data...</p>
        <p class="small text-muted">Request URL: ${url}</p>
    `;
    
    // Fetch data directly
    directFetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Log the raw response text for debugging
            return response.text().then(text => {
                console.log("Raw Correlations API response text:", text.substring(0, 500) + "..."); // Log first 500 chars
                
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error("JSON parse error:", e);
                    throw new Error(`JSON parsing failed: ${e.message}. Raw response starts with: ${text.substring(0, 100)}`);
                }
            });
        })
        .then(data => {
            console.log("Correlations data received:", data);
            let html = '';
            
            if (data && data.chart_base64) {
                html = `
                    <div class="col-12 mb-4">
                        <div class="card border-left-warning shadow h-100 py-2">
                            <div class="card-body">
                                <div class="row no-gutters align-items-center">
                                    <div class="col mr-2">
                                        <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                                            Lottery Correlations
                                        </div>
                                        <div class="h5 mb-0 font-weight-bold text-gray-800">
                                            Cross-Game Analysis
                                        </div>
                                        <div class="mt-2">
                                            <img src="data:image/png;base64,${data.chart_base64}" 
                                                 alt="Lottery Type Correlations" 
                                                 class="img-fluid">
                                        </div>
                                        <div class="mt-3">
                                            <p class="text-muted">This analysis shows potential relationships between different lottery types.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (data && data.error) {
                html = `
                    <div class="col-12">
                        <div class="alert alert-warning">
                            <h5>Correlation Analysis Issue</h5>
                            <p>${data.error}</p>
                        </div>
                    </div>
                `;
            } else {
                html = `
                    <div class="col-12">
                        <div class="alert alert-info">
                            <h5>No Correlation Data Available</h5>
                            <p>There is not enough cross-game lottery data to analyze correlations.</p>
                            <p>Please ensure there are multiple lottery types with results in the database.</p>
                        </div>
                    </div>
                `;
            }
            
            // Set the HTML
            contentEl.innerHTML = html;
            
            // Make sure content becomes visible
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        })
        .catch(error => {
            console.error("Error loading correlations data:", error);
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <h5>Error Loading Correlation Analysis</h5>
                        <p>There was a problem loading the correlations data: ${error.message}</p>
                        <p>Please try refreshing the page or selecting different filters.</p>
                    </div>
                </div>
            `;
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        });
}