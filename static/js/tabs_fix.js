/**
 * Direct JavaScript fixes for lottery analysis tabs
 * This script explicitly forces proper tab functionality
 */

// Execute when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Tab fixes loaded');
    
    // Make sure all tabs have proper event listeners
    setupTabEventListeners();
    
    // Setup immediate API data loading for each tab
    setupDataLoading();
    
    // Add MutationObserver to ensure visibility
    monitorTabVisibility();
});

// Setup event listeners for all tabs
function setupTabEventListeners() {
    // Get all tab buttons
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    // Add click handler to each
    tabButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            // Prevent default behavior to handle manually
            event.preventDefault();
            
            // Get the target tab
            const targetId = button.getAttribute('data-bs-target');
            
            // Hide all tab panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show');
                pane.classList.remove('active');
            });
            
            // Remove active class from all tab buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            });
            
            // Show the selected tab pane
            const targetPane = document.querySelector(targetId);
            targetPane.classList.add('show');
            targetPane.classList.add('active');
            
            // Mark the clicked button as active
            button.classList.add('active');
            button.setAttribute('aria-selected', 'true');
            
            // Handle data loading for the tab
            loadDataForTab(targetId);
            
            console.log(`Tab changed to ${targetId}`);
        });
    });
    
    console.log('Tab event listeners setup');
}

// Setup data loading for each tab
function setupDataLoading() {
    // Add immediate load for active tab
    const activeTab = document.querySelector('.tab-pane.active');
    if (activeTab) {
        console.log(`Initially active tab: #${activeTab.id}`);
        loadDataForTab(`#${activeTab.id}`);
    }
    
    // Trigger data loading for Pattern Analysis tab
    document.getElementById('patterns-tab')?.addEventListener('shown.bs.tab', function() {
        loadDataForTab('#patterns');
    });
    
    // Trigger data loading for Time Series tab
    document.getElementById('timeseries-tab')?.addEventListener('shown.bs.tab', function() {
        loadDataForTab('#timeseries');
    });
    
    // Trigger data loading for Winners tab
    document.getElementById('winners-tab')?.addEventListener('shown.bs.tab', function() {
        loadDataForTab('#winners');
    });
    
    // Trigger data loading for Correlations tab
    document.getElementById('correlations-tab')?.addEventListener('shown.bs.tab', function() {
        loadDataForTab('#correlations');
    });
    
    console.log('Data loading triggers setup');
}

// Load data for specific tab
function loadDataForTab(tabId) {
    console.log(`Loading data for tab: ${tabId}`);
    
    if (tabId === '#patterns') {
        const contentEl = document.getElementById('patterns-content');
        const loadingEl = document.getElementById('patterns-loading');
        
        if (!contentEl || !loadingEl) {
            console.error('Pattern elements not found');
            return;
        }
        
        // Show loading indicator
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // Define a backup loadPatternData function if not available
        if (typeof loadPatternData !== 'function') {
            console.log('Creating backup loadPatternData function');
            window.loadPatternData = function() {
                // Get the parameters
                const lotteryTypeSelect = document.getElementById('lottery_type');
                const daysSelect = document.getElementById('days');
                const lotteryType = lotteryTypeSelect ? lotteryTypeSelect.value || '' : '';
                const days = daysSelect ? daysSelect.value || '365' : '365';
                
                // Build URL
                const url = `/api/lottery-analysis/patterns?lottery_type=${encodeURIComponent(lotteryType)}&days=${encodeURIComponent(days)}`;
                
                // Get the content and loading elements
                const content = document.getElementById('patterns-content');
                const loading = document.getElementById('patterns-loading');
                
                // Make the fetch request
                fetch(url)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.json();
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
                        content.innerHTML = html;
                        
                        // Make sure content becomes visible
                        loading.style.display = 'none';
                        content.style.display = 'block';
                    })
                    .catch(error => {
                        console.error("Error loading pattern data:", error);
                        content.innerHTML = `
                            <div class="col-12">
                                <div class="alert alert-danger">
                                    <h5>Error Loading Pattern Analysis</h5>
                                    <p>There was a problem loading the pattern analysis data: ${error.message}</p>
                                    <p>Please try refreshing the page or selecting different filters.</p>
                                </div>
                            </div>
                        `;
                        loading.style.display = 'none';
                        content.style.display = 'block';
                    });
            };
        }
        
        // Call the loader function
        console.log('Calling loadPatternData');
        loadPatternData();
    } 
    else if (tabId === '#timeseries') {
        const contentEl = document.getElementById('timeseries-content');
        const loadingEl = document.getElementById('timeseries-loading');
        
        if (!contentEl || !loadingEl) {
            console.error('Time series elements not found');
            return;
        }
        
        // Show loading indicator
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // Define a backup loadTimeSeriesData function if not available
        if (typeof loadTimeSeriesData !== 'function') {
            console.log('Creating backup loadTimeSeriesData function');
            window.loadTimeSeriesData = function() {
                // Get the parameters
                const lotteryTypeSelect = document.getElementById('lottery_type');
                const daysSelect = document.getElementById('days');
                const lotteryType = lotteryTypeSelect ? lotteryTypeSelect.value || '' : '';
                const days = daysSelect ? daysSelect.value || '365' : '365';
                
                // Build URL
                const url = `/api/lottery-analysis/time-series?lottery_type=${encodeURIComponent(lotteryType)}&days=${encodeURIComponent(days)}`;
                
                // Get the content and loading elements
                const content = document.getElementById('timeseries-content');
                const loading = document.getElementById('timeseries-loading');
                
                // Make the fetch request
                fetch(url)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.json();
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
                                                                alt="Time Series for ${lotteryType}" 
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
                        content.innerHTML = html;
                        
                        // Make sure content becomes visible
                        loading.style.display = 'none';
                        content.style.display = 'block';
                    })
                    .catch(error => {
                        console.error("Error loading time series data:", error);
                        content.innerHTML = `
                            <div class="col-12">
                                <div class="alert alert-danger">
                                    <h5>Error Loading Time Series Analysis</h5>
                                    <p>There was a problem loading the time series data: ${error.message}</p>
                                    <p>Please try refreshing the page or selecting different filters.</p>
                                </div>
                            </div>
                        `;
                        loading.style.display = 'none';
                        content.style.display = 'block';
                    });
            };
        }
        
        // Call the loader function
        console.log('Calling loadTimeSeriesData');
        loadTimeSeriesData();
    }
    else if (tabId === '#winners') {
        const contentEl = document.getElementById('winners-content');
        const loadingEl = document.getElementById('winners-loading');
        
        if (!contentEl || !loadingEl) {
            console.error('Winners elements not found');
            return;
        }
        
        // Show loading indicator
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // Define a backup loadWinnerData function if not available
        if (typeof loadWinnerData !== 'function') {
            console.log('Creating backup loadWinnerData function');
            window.loadWinnerData = function() {
                // Get the parameters
                const lotteryTypeSelect = document.getElementById('lottery_type');
                const daysSelect = document.getElementById('days');
                const lotteryType = lotteryTypeSelect ? lotteryTypeSelect.value || '' : '';
                const days = daysSelect ? daysSelect.value || '365' : '365';
                
                // Build URL
                const url = `/api/lottery-analysis/winners?lottery_type=${encodeURIComponent(lotteryType)}&days=${encodeURIComponent(days)}`;
                
                // Get the content and loading elements
                const content = document.getElementById('winners-content');
                const loading = document.getElementById('winners-loading');
                
                // Make the fetch request
                fetch(url)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log("Winner data received:", data);
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
                                                                No Winner Data
                                                            </div>
                                                            <div class="mt-2">
                                                                <p>${typeData?.error || 'Insufficient data for winner analysis.'}</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                    continue;
                                }
                                
                                // Create winner card for valid data
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
                                                            Winner Analysis
                                                        </div>
                                                        <div class="mt-2">
                                                            <img src="data:image/png;base64,${typeData.chart_base64}" 
                                                                alt="Winner Analysis for ${lotteryType}" 
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
                                        No data available for winner analysis. Please ensure there are lottery results in the database.
                                    </div>
                                </div>
                            `;
                        }
                        
                        // Set the HTML
                        content.innerHTML = html;
                        
                        // Make sure content becomes visible
                        loading.style.display = 'none';
                        content.style.display = 'block';
                    })
                    .catch(error => {
                        console.error("Error loading winner data:", error);
                        content.innerHTML = `
                            <div class="col-12">
                                <div class="alert alert-danger">
                                    <h5>Error Loading Winner Analysis</h5>
                                    <p>There was a problem loading the winner data: ${error.message}</p>
                                    <p>Please try refreshing the page or selecting different filters.</p>
                                </div>
                            </div>
                        `;
                        loading.style.display = 'none';
                        content.style.display = 'block';
                    });
            };
        }
        
        // Call the loader function
        console.log('Calling loadWinnerData');
        loadWinnerData();
    }
    else if (tabId === '#correlations') {
        const contentEl = document.getElementById('correlations-content');
        const loadingEl = document.getElementById('correlations-loading');
        
        if (!contentEl || !loadingEl) {
            console.error('Correlations elements not found');
            return;
        }
        
        // Show loading indicator
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // Define a backup loadCorrelationData function if not available
        if (typeof loadCorrelationData !== 'function') {
            console.log('Creating backup loadCorrelationData function');
            window.loadCorrelationData = function() {
                // Get the parameters
                const daysSelect = document.getElementById('days');
                const days = daysSelect ? daysSelect.value || '365' : '365';
                
                // Build URL
                const url = `/api/lottery-analysis/correlations?days=${encodeURIComponent(days)}`;
                
                // Get the content and loading elements
                const content = document.getElementById('correlations-content');
                const loading = document.getElementById('correlations-loading');
                
                // Make the fetch request
                fetch(url)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log("Correlation data received:", data);
                        let html = '';
                        
                        if (data && data.chart_base64) {
                            // Create correlation visualization
                            html = `
                                <div class="col-12 mb-4">
                                    <div class="card shadow h-100">
                                        <div class="card-body">
                                            <h5 class="card-title">Lottery Correlations</h5>
                                            <div class="mt-2">
                                                <img src="data:image/png;base64,${data.chart_base64}" 
                                                    alt="Lottery Correlations" 
                                                    class="img-fluid">
                                            </div>
                                            <div class="mt-3">
                                                <p class="text-muted">
                                                    This chart shows the correlation between different lottery types. 
                                                    Stronger correlations suggest that patterns in one lottery may provide 
                                                    insight into patterns in another.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else if (data && data.error) {
                            html = `
                                <div class="col-12">
                                    <div class="alert alert-warning">
                                        <h5>Correlation Analysis Unavailable</h5>
                                        <p>${data.error}</p>
                                    </div>
                                </div>
                            `;
                        } else {
                            html = `
                                <div class="col-12">
                                    <div class="alert alert-info">
                                        No data available for correlation analysis. Please ensure there are lottery results for multiple lottery types in the database.
                                    </div>
                                </div>
                            `;
                        }
                        
                        // Set the HTML
                        content.innerHTML = html;
                        
                        // Make sure content becomes visible
                        loading.style.display = 'none';
                        content.style.display = 'block';
                    })
                    .catch(error => {
                        console.error("Error loading correlation data:", error);
                        content.innerHTML = `
                            <div class="col-12">
                                <div class="alert alert-danger">
                                    <h5>Error Loading Correlation Analysis</h5>
                                    <p>There was a problem loading the correlation data: ${error.message}</p>
                                    <p>Please try refreshing the page or selecting different filters.</p>
                                </div>
                            </div>
                        `;
                        loading.style.display = 'none';
                        content.style.display = 'block';
                    });
            };
        }
        
        // Call the loader function
        console.log('Calling loadCorrelationData');
        loadCorrelationData();
    }
}

// Monitor tab visibility using MutationObserver
function monitorTabVisibility() {
    // Monitor all tab panes
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabPanes.forEach(pane => {
        // Create a new observer for each pane
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(mutation => {
                if (mutation.type === 'attributes' && 
                    (mutation.attributeName === 'class' || mutation.attributeName === 'style')) {
                    
                    const isActive = pane.classList.contains('active');
                    const isShown = pane.classList.contains('show');
                    const isVisible = window.getComputedStyle(pane).display !== 'none';
                    
                    console.log(`Tab #${pane.id} state changed: active=${isActive}, shown=${isShown}, visible=${isVisible}`);
                    
                    // If active but not visible, fix it
                    if (isActive && !isVisible) {
                        console.log(`Fixing visibility for tab #${pane.id}`);
                        pane.style.display = 'block';
                    }
                    
                    // If active, ensure data is loaded
                    if (isActive && isShown) {
                        setTimeout(() => {
                            loadDataForTab(`#${pane.id}`);
                        }, 100);
                    }
                }
            });
        });
        
        // Start observing
        observer.observe(pane, { 
            attributes: true,
            attributeFilter: ['class', 'style']
        });
    });
    
    console.log('Tab visibility monitoring started');
}

// Force fix displayable content when the page is fully loaded
window.addEventListener('load', function() {
    console.log('Page fully loaded, fixing tabs');
    
    setTimeout(() => {
        // Fix active tab visibility
        const activeTab = document.querySelector('.tab-pane.active');
        if (activeTab) {
            activeTab.style.display = 'block';
            console.log(`Ensuring active tab #${activeTab.id} is visible`);
            loadDataForTab(`#${activeTab.id}`);
        } else {
            // If no active tab, activate the first one
            const firstTab = document.querySelector('.tab-pane');
            if (firstTab) {
                firstTab.classList.add('active');
                firstTab.classList.add('show');
                firstTab.style.display = 'block';
                
                // Also activate the corresponding tab button
                const firstTabButton = document.querySelector(`[data-bs-target="#${firstTab.id}"]`);
                if (firstTabButton) {
                    firstTabButton.classList.add('active');
                    firstTabButton.setAttribute('aria-selected', 'true');
                }
                
                console.log(`No active tab found, activating #${firstTab.id}`);
                loadDataForTab(`#${firstTab.id}`);
            }
        }
    }, 500);
});