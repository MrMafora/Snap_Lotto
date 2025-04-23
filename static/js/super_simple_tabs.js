/* 
 * Super Simple Tab Switcher
 * A bare-minimum solution that works across all browsers 
 */

// Wait for page to load fully
document.addEventListener('DOMContentLoaded', function() {
    console.log('Super Simple Tabs loaded');
    
    // Find all super-simple tab buttons
    const buttons = document.querySelectorAll('.super-simple-tab-btn');
    console.log(`Found ${buttons.length} super simple tab buttons`);
    
    // Add click handlers to each button
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get target tab ID from button attribute
            const tabId = this.getAttribute('data-tab-id');
            if (!tabId) {
                console.error('Button missing data-tab-id attribute');
                return;
            }
            
            console.log(`Super simple tab button clicked for: ${tabId}`);
            
            // Hide all tabs
            const allTabs = document.querySelectorAll('.tab-pane');
            allTabs.forEach(tab => {
                tab.style.display = 'none';
                tab.classList.remove('active', 'show');
            });
            
            // Show target tab
            const targetTab = document.getElementById(tabId);
            if (targetTab) {
                targetTab.style.display = 'block';
                targetTab.classList.add('active', 'show');
                
                // Update all button states
                buttons.forEach(button => {
                    button.classList.remove('active');
                    button.classList.remove('btn-primary');
                    button.classList.add('btn-secondary');
                });
                
                // Update this button state
                this.classList.add('active');
                this.classList.remove('btn-secondary');
                this.classList.add('btn-primary');
                
                // If this is a data tab, load its data
                if (tabId !== 'frequency') {
                    const loadingEl = document.getElementById(`${tabId}-loading`);
                    const contentEl = document.getElementById(`${tabId}-content`);
                    
                    if (loadingEl && contentEl) {
                        // Only load if content isn't already loaded
                        if (contentEl.innerHTML.trim() === '') {
                            loadingEl.style.display = 'block';
                            contentEl.style.display = 'none';
                            
                            // Determine API endpoint
                            let endpoint = '';
                            
                            switch(tabId) {
                                case 'patterns':
                                    endpoint = '/api/lottery-analysis/patterns?lottery_type=&days=365';
                                    break;
                                case 'timeseries':
                                    endpoint = '/api/lottery-analysis/time-series?lottery_type=&days=365';
                                    break;
                                case 'winners':
                                    endpoint = '/api/lottery-analysis/winners?lottery_type=&days=365';
                                    break;
                                case 'correlations':
                                    endpoint = '/api/lottery-analysis/correlations?lottery_type=&days=365';
                                    break;
                            }
                            
                            if (endpoint) {
                                console.log(`Loading data from ${endpoint}`);
                                
                                // Use fetch with minimal settings
                                fetch(endpoint)
                                    .then(response => {
                                        if (!response.ok) {
                                            throw new Error(`HTTP error! Status: ${response.status}`);
                                        }
                                        return response.json();
                                    })
                                    .then(data => {
                                        console.log(`Data loaded successfully for ${tabId}`);
                                        
                                        // Display the data
                                        let html = '';
                                        
                                        if (tabId === 'patterns') {
                                            html = `<div class="alert alert-success">Pattern analysis data loaded successfully!</div>`;
                                            if (data && data.patterns) {
                                                Object.entries(data.patterns).forEach(([lottery_type, patterns]) => {
                                                    if (patterns && patterns.length > 0) {
                                                        html += `
                                                            <div class="col-md-6 mb-4">
                                                                <div class="card shadow">
                                                                    <div class="card-header">${lottery_type} Patterns</div>
                                                                    <div class="card-body">
                                                                        <ul class="list-group">
                                                        `;
                                                        
                                                        patterns.slice(0, 5).forEach(pattern => {
                                                            html += `
                                                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                                                    ${pattern.description}
                                                                    <span class="badge bg-primary rounded-pill">${pattern.frequency}</span>
                                                                </li>
                                                            `;
                                                        });
                                                        
                                                        html += `
                                                                        </ul>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        `;
                                                    }
                                                });
                                            }
                                        } else if (tabId === 'timeseries') {
                                            html = `<div class="alert alert-success">Time Series data loaded successfully!</div>`;
                                            if (data && data.time_series) {
                                                Object.entries(data.time_series).forEach(([lottery_type, series]) => {
                                                    html += `
                                                        <div class="col-md-6 mb-4">
                                                            <div class="card shadow">
                                                                <div class="card-header">${lottery_type} Time Series</div>
                                                                <div class="card-body">
                                                                    <p>Recent trend: ${series.trend || 'No clear trend'}</p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    `;
                                                });
                                            }
                                        } else if (tabId === 'winners') {
                                            html = `<div class="alert alert-success">Winner analysis data loaded successfully!</div>`;
                                            if (data && data.winners) {
                                                Object.entries(data.winners).forEach(([lottery_type, winners]) => {
                                                    html += `
                                                        <div class="col-md-6 mb-4">
                                                            <div class="card shadow">
                                                                <div class="card-header">${lottery_type} Winners</div>
                                                                <div class="card-body">
                                                    `;
                                                    
                                                    if (winners && winners.divisions) {
                                                        html += '<ul class="list-group">';
                                                        Object.entries(winners.divisions).slice(0, 5).forEach(([division, stats]) => {
                                                            html += `
                                                                <li class="list-group-item">
                                                                    <div class="d-flex justify-content-between">
                                                                        <span>${division}</span>
                                                                        <span>${stats.total_winners} winners</span>
                                                                    </div>
                                                                    <div class="small text-muted">
                                                                        Average prize: ${stats.average_prize || 'Unknown'}
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
                                                    `;
                                                });
                                            }
                                        } else if (tabId === 'correlations') {
                                            html = `<div class="alert alert-success">Correlation data loaded successfully!</div>`;
                                            if (data && data.correlations) {
                                                html += `
                                                    <div class="col-12 mb-4">
                                                        <div class="card shadow">
                                                            <div class="card-header">Lottery Type Correlations</div>
                                                            <div class="card-body">
                                                                <div class="table-responsive">
                                                                    <table class="table table-bordered">
                                                                        <thead>
                                                                            <tr>
                                                                                <th>Type A</th>
                                                                                <th>Type B</th>
                                                                                <th>Correlation</th>
                                                                            </tr>
                                                                        </thead>
                                                                        <tbody>
                                                `;
                                                
                                                data.correlations.forEach(corr => {
                                                    html += `
                                                        <tr>
                                                            <td>${corr.type_a}</td>
                                                            <td>${corr.type_b}</td>
                                                            <td>${corr.correlation.toFixed(2)}</td>
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
                                            }
                                        }
                                        
                                        // Update content and hide loading indicator
                                        contentEl.innerHTML = html;
                                        loadingEl.style.display = 'none';
                                        contentEl.style.display = 'block';
                                    })
                                    .catch(error => {
                                        console.error(`Error loading ${tabId} data:`, error);
                                        
                                        // Show error and hide loading indicator
                                        contentEl.innerHTML = `
                                            <div class="alert alert-danger">
                                                <h5>Error Loading Data</h5>
                                                <p>${error.message}</p>
                                                <button class="btn btn-outline-danger btn-sm mt-2" 
                                                        onclick="document.querySelector('[data-tab-id=\\'${tabId}\\']').click()">
                                                    <i class="fas fa-sync-alt"></i> Try Again
                                                </button>
                                            </div>
                                        `;
                                        loadingEl.style.display = 'none';
                                        contentEl.style.display = 'block';
                                    });
                            } else {
                                // No endpoint for this tab
                                loadingEl.style.display = 'none';
                                contentEl.style.display = 'block';
                            }
                        } else {
                            // Content already loaded
                            loadingEl.style.display = 'none';
                            contentEl.style.display = 'block';
                        }
                    }
                }
            } else {
                console.error(`Tab #${tabId} not found`);
            }
        });
    });
});