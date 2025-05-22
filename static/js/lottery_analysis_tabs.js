/**
 * Lottery Analysis Tabs - Handles tab switching and loading tab data
 */

// Define displayTabData and loadTabData in the global scope
window.displayTabData = function(tabId, data) {
    console.log(`Displaying data for tab: ${tabId}`);
    const contentEl = document.getElementById(`${tabId}-content`);
    let html = '';
    
    // Generate appropriate HTML based on tab type and data
    if (tabId === 'patterns') {
        if (data && data.patterns) {
            Object.entries(data.patterns).forEach(([lottery_type, patterns]) => {
                if (patterns && patterns.length > 0) {
                    html += `
                        <div class="col-md-6 mb-4">
                            <div class="card border-left-primary shadow h-100 py-2">
                                <div class="card-body">
                                    <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                                        ${lottery_type}
                                    </div>
                                    <div class="h5 mb-0 font-weight-bold text-gray-800">
                                        Pattern Analysis
                                    </div>
                                    <div class="mt-3">
                                        <ul class="list-group">
                    `;
                    
                    patterns.slice(0, 5).forEach(pattern => {
                        html += `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                ${pattern.description}
                                <span class="badge badge-primary badge-pill">${pattern.frequency}</span>
                            </li>
                        `;
                    });
                    
                    html += `
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            });
        }
        
        if (html === '') {
            html = `
                <div class="col-12">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle mr-1"></i> No pattern analysis data available for the selected lottery type(s).
                    </div>
                </div>
            `;
        }
    } 
    else if (tabId === 'timeseries') {
        if (data && data.time_series) {
            Object.entries(data.time_series).forEach(([lottery_type, typeData]) => {
                html += `
                    <div class="col-md-6 mb-4">
                        <div class="card border-left-info shadow h-100 py-2">
                            <div class="card-body">
                                <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
                                    ${lottery_type}
                                </div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">
                                    Time Series Analysis
                                </div>
                                <div class="mt-2">
                                    <img src="data:image/png;base64,${typeData.chart_base64}" 
                                        alt="Time Series Analysis for ${lottery_type}" 
                                        class="img-fluid">
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        if (html === '') {
            html = `
                <div class="col-12">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle mr-1"></i> No time series data available for the selected lottery type(s).
                    </div>
                </div>
            `;
        }
    } 
    else if (tabId === 'winners') {
        if (data && data.winners) {
            Object.entries(data.winners).forEach(([lottery_type, winners]) => {
                html += `
                    <div class="col-md-6 mb-4">
                        <div class="card border-left-success shadow h-100 py-2">
                            <div class="card-body">
                                <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                                    ${lottery_type}
                                </div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">
                                    Winner Analysis
                                </div>
                                <div class="mt-3">
                `;
                
                if (winners && winners.divisions) {
                    html += '<ul class="list-group">';
                    Object.entries(winners.divisions).slice(0, 5).forEach(([division, stats]) => {
                        html += `
                            <li class="list-group-item">
                                <div class="d-flex justify-content-between">
                                    <span>${division}</span>
                                    <span>${stats.total_winners} winner(s)</span>
                                </div>
                                <div class="small text-muted">
                                    Average prize: ${stats.average_prize || 'Not available'}
                                </div>
                            </li>
                        `;
                    });
                    html += '</ul>';
                } else {
                    html += '<p>No winner data available</p>';
                }
                
                html += `
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        if (html === '') {
            html = `
                <div class="col-12">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle mr-1"></i> No winner data available for the selected lottery type(s).
                    </div>
                </div>
            `;
        }
    } 
    else if (tabId === 'correlations') {
        if (data && data.correlations && data.correlations.length > 0) {
            html += `
                <div class="col-12 mb-4">
                    <div class="card shadow">
                        <div class="card-body">
                            <h5 class="font-weight-bold text-primary mb-3">Cross-Lottery Correlations</h5>
                            <div class="table-responsive">
                                <table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>Type A</th>
                                            <th>Type B</th>
                                            <th>Correlation</th>
                                            <th>Strength</th>
                                        </tr>
                                    </thead>
                                    <tbody>
            `;
            
            data.correlations.forEach(corr => {
                let strengthClass = 'text-muted';
                let strength = 'Weak';
                
                if (Math.abs(corr.correlation) > 0.7) {
                    strengthClass = 'text-danger font-weight-bold';
                    strength = 'Strong';
                } else if (Math.abs(corr.correlation) > 0.4) {
                    strengthClass = 'text-warning';
                    strength = 'Moderate';
                }
                
                html += `
                    <tr>
                        <td>${corr.type_a}</td>
                        <td>${corr.type_b}</td>
                        <td>${corr.correlation.toFixed(2)}</td>
                        <td class="${strengthClass}">${strength}</td>
                    </tr>
                `;
            });
            
            html += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            if (data.chart_base64) {
                html += `
                    <div class="col-12 mb-4">
                        <div class="card shadow">
                            <div class="card-body">
                                <h5 class="font-weight-bold text-primary mb-3">Correlation Matrix</h5>
                                <img src="data:image/png;base64,${data.chart_base64}" 
                                     alt="Lottery Type Correlation Matrix" 
                                     class="img-fluid">
                            </div>
                        </div>
                    </div>
                `;
            }
        } else {
            html = `
                <div class="col-12">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle mr-1"></i> No correlation data available. Need at least two lottery types with sufficient data for correlation analysis.
                    </div>
                </div>
            `;
        }
    }
    
    // Update the content and hide loading
    contentEl.innerHTML = html;
    document.getElementById(`${tabId}-loading`).style.display = 'none';
    contentEl.style.display = 'block';
};

// Define loadTabData in the global scope for direct access
window.loadTabData = function(tabId) {
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const lotteryType = urlParams.get('lottery_type') || '';
    const days = urlParams.get('days') || '365';
    
    console.log(`Loading data for tab: ${tabId}`);
    
    const loadingEl = document.getElementById(`${tabId}-loading`);
    const contentEl = document.getElementById(`${tabId}-content`);
    
    if (!loadingEl || !contentEl) {
        console.error(`Elements for tab ${tabId} not found`);
        return;
    }
    
    // Show loading, hide content
    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';
    
    // Build API endpoint
    let endpoint = '';
    switch(tabId) {
        case 'patterns':
            endpoint = `/api/lottery-analysis/patterns?lottery_type=${lotteryType}&days=${days}`;
            break;
        case 'timeseries':
            endpoint = `/api/lottery-analysis/time-series?lottery_type=${lotteryType}&days=${days}`;
            break;
        case 'winners':
            endpoint = `/api/lottery-analysis/winners?lottery_type=${lotteryType}&days=${days}`;
            break;
        case 'correlations':
            endpoint = `/api/lottery-analysis/correlations?lottery_type=${lotteryType}&days=${days}`;
            break;
        default:
            console.error(`Unknown tab ID: ${tabId}`);
            loadingEl.style.display = 'none';
            contentEl.innerHTML = `<div class="alert alert-danger">Unknown tab ID: ${tabId}</div>`;
            contentEl.style.display = 'block';
            return;
    }
    
    console.log(`Fetching data from ${endpoint}`);
    
    // Fetch data from API
    fetch(endpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`Data loaded successfully for ${tabId}`);
            window.displayTabData(tabId, data);
        })
        .catch(error => {
            console.error(`Error loading ${tabId} data:`, error);
            contentEl.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle mr-1"></i> Error loading data: ${error.message}
                        <button class="btn btn-outline-danger btn-sm ml-3" onclick="window.loadTabData('${tabId}')">Try Again</button>
                    </div>
                </div>
            `;
            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        });
};

// Initialize tab functionality when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Lottery Analysis Tab System loaded');
    
    // Function to manually set up Bootstrap tabs since we may not have all Bootstrap JS loaded
    function setupTabs() {
        const tabLinks = document.querySelectorAll('a[data-toggle="tab"]');
        console.log(`Found ${tabLinks.length} tab links`);
        
        tabLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get the target tab ID from the href
                const targetId = this.getAttribute('href').substring(1);
                console.log(`Tab clicked: ${targetId}`);
                
                // Hide all tabs
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('show', 'active');
                });
                
                // Show the selected tab
                const targetTab = document.getElementById(targetId);
                if (targetTab) {
                    targetTab.classList.add('show', 'active');
                }
                
                // Update the active state of the tab buttons
                tabLinks.forEach(btn => {
                    btn.classList.remove('active');
                    btn.setAttribute('aria-selected', 'false');
                });
                
                // Set this tab as active
                this.classList.add('active');
                this.setAttribute('aria-selected', 'true');
                
                // Load data for this tab if needed
                if (targetId !== 'frequency') {
                    // Check if data is already loaded
                    const contentEl = document.getElementById(`${targetId}-content`);
                    if (contentEl && contentEl.innerHTML.trim() === '') {
                        window.loadTabData(targetId);
                    }
                }
            });
        });
    }
    
    // Initialize our custom tab system
    setupTabs();
    
    // Hook up reload buttons
    document.getElementById('reload-patterns')?.addEventListener('click', () => {
        const contentEl = document.getElementById('patterns-content');
        if (contentEl) contentEl.innerHTML = '';
        window.loadTabData('patterns');
    });
    
    document.getElementById('reload-timeseries')?.addEventListener('click', () => {
        const contentEl = document.getElementById('timeseries-content');
        if (contentEl) contentEl.innerHTML = '';
        window.loadTabData('timeseries');
    });
    
    document.getElementById('reload-winners')?.addEventListener('click', () => {
        const contentEl = document.getElementById('winners-content');
        if (contentEl) contentEl.innerHTML = '';
        window.loadTabData('winners');
    });
    
    document.getElementById('reload-correlations')?.addEventListener('click', () => {
        const contentEl = document.getElementById('correlations-content');
        if (contentEl) contentEl.innerHTML = '';
        window.loadTabData('correlations');
    });
    
    // Function to reload all tab data
    window.reloadAllData = function() {
        const tabs = ['patterns', 'timeseries', 'winners', 'correlations'];
        tabs.forEach(tabId => {
            const contentEl = document.getElementById(`${tabId}-content`);
            if (contentEl) contentEl.innerHTML = '';
            // Only load if tab exists
            if (document.getElementById(tabId)) {
                window.loadTabData(tabId);
            }
        });
        alert('All analysis data is being refreshed. This may take a moment.');
    };
});