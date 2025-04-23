/**
 * Ultra-simple Tab Navigation System
 * A minimal, dependency-free tab navigation system
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Ultra Simple Tab Navigation loaded");
    
    // Find all buttons with the simple-tab class
    const tabButtons = document.querySelectorAll('.simple-tab-button');
    console.log(`Found ${tabButtons.length} simple tab buttons`);
    
    // Set up click handlers
    tabButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Get target tab from data attribute
            const targetId = this.getAttribute('data-target');
            if (!targetId) {
                console.error("No target specified for tab button");
                return;
            }
            
            console.log(`Simple tab button clicked for: ${targetId}`);
            
            // 1. Hide all tab content
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
                pane.classList.remove('show');
                pane.style.display = 'none';
            });
            
            // 2. Show the target content
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('active');
                targetPane.classList.add('show');
                targetPane.style.display = 'block';
                
                // 3. Update button states
                tabButtons.forEach(btn => {
                    btn.classList.remove('active');
                    btn.classList.remove('btn-primary');
                    btn.classList.add('btn-outline-secondary');
                });
                
                // 4. Mark this button as active
                this.classList.add('active');
                this.classList.remove('btn-outline-secondary');
                this.classList.add('btn-primary');
                
                // 5. Load data if needed
                const loadingDiv = document.getElementById(`${targetId}-loading`);
                const contentDiv = document.getElementById(`${targetId}-content`);
                
                if (loadingDiv && contentDiv) {
                    // Only load data if content is empty
                    if (contentDiv.innerHTML.trim() === '') {
                        loadingDiv.style.display = 'block';
                        contentDiv.style.display = 'none';
                        
                        // Simple fetch to load data
                        let apiUrl = null;
                        
                        // Map tab ID to API endpoint
                        switch (targetId) {
                            case 'patterns':
                                apiUrl = '/api/lottery-analysis/patterns?lottery_type=&days=365';
                                break;
                            case 'timeseries':
                                apiUrl = '/api/lottery-analysis/time-series?lottery_type=&days=365';
                                break;
                            case 'winners':
                                apiUrl = '/api/lottery-analysis/winners?lottery_type=&days=365';
                                break;
                            case 'correlations':
                                apiUrl = '/api/lottery-analysis/correlations?lottery_type=&days=365';
                                break;
                        }
                        
                        if (apiUrl) {
                            console.log(`Loading data from ${apiUrl}`);
                            
                            // Simple fetch with minimal headers
                            fetch(apiUrl, {
                                method: 'GET',
                                headers: {
                                    'X-Requested-With': 'XMLHttpRequest',
                                    'Accept': 'application/json'
                                }
                            })
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error(`HTTP error! Status: ${response.status}`);
                                }
                                return response.json();
                            })
                            .then(data => {
                                // Display the data
                                console.log(`Data loaded for ${targetId}`);
                                
                                // Hide loading indicator
                                loadingDiv.style.display = 'none';
                                
                                // Generate content based on tab
                                if (targetId === 'patterns') {
                                    displayPatternData(data, contentDiv);
                                } else if (targetId === 'timeseries') {
                                    displayTimeSeriesData(data, contentDiv);
                                } else if (targetId === 'winners') {
                                    displayWinnersData(data, contentDiv);
                                } else if (targetId === 'correlations') {
                                    displayCorrelationsData(data, contentDiv);
                                } else {
                                    contentDiv.innerHTML = `<div class="alert alert-info">Data loaded successfully</div>`;
                                }
                                
                                // Show content
                                contentDiv.style.display = 'block';
                            })
                            .catch(error => {
                                console.error(`Error loading data for ${targetId}:`, error);
                                
                                // Show error message
                                loadingDiv.style.display = 'none';
                                contentDiv.innerHTML = `
                                    <div class="alert alert-danger">
                                        <h5>Error Loading Data</h5>
                                        <p>${error.message}</p>
                                        <p>Please try refreshing the page or check your connection.</p>
                                    </div>
                                `;
                                contentDiv.style.display = 'block';
                            });
                        } else {
                            // No API URL defined for this tab
                            loadingDiv.style.display = 'none';
                            contentDiv.style.display = 'block';
                        }
                    } else {
                        // Content already loaded, just show it
                        loadingDiv.style.display = 'none';
                        contentDiv.style.display = 'block';
                    }
                }
            } else {
                console.error(`Target tab pane #${targetId} not found`);
            }
        });
    });
    
    // Helper functions for displaying different data types
    function displayPatternData(data, container) {
        let html = '<div class="col-12"><h4 class="mb-4">Pattern Analysis Results</h4></div>';
        
        // Check if we have valid data
        if (!data || !data.patterns || Object.keys(data.patterns).length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning">
                        <h5>No Pattern Data Available</h5>
                        <p>No patterns could be found in the current lottery dataset.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        // Simple display of pattern data
        Object.entries(data.patterns).forEach(([lottery_type, patterns]) => {
            html += `
                <div class="col-md-6 mb-4">
                    <div class="card shadow h-100">
                        <div class="card-header py-3">
                            <h6 class="m-0 font-weight-bold text-primary">${lottery_type} Patterns</h6>
                        </div>
                        <div class="card-body">
                            <div class="patterns-section">
                                <h5 class="card-title">Top Patterns</h5>
                                <ul class="list-group">
            `;
            
            // Add pattern details
            if (patterns && patterns.length > 0) {
                patterns.slice(0, 5).forEach(pattern => {
                    html += `
                        <li class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>${pattern.description}</span>
                                <span class="badge bg-primary">${pattern.frequency} occurrences</span>
                            </div>
                        </li>
                    `;
                });
            } else {
                html += `
                    <li class="list-group-item">No patterns detected for this lottery type</li>
                `;
            }
            
            html += `
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    function displayTimeSeriesData(data, container) {
        let html = '<div class="col-12"><h4 class="mb-4">Time Series Analysis</h4></div>';
        
        // Check if we have valid data
        if (!data || !data.time_series || Object.keys(data.time_series).length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning">
                        <h5>No Time Series Data Available</h5>
                        <p>No time series data could be found in the current lottery dataset.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        // Simple display of time series data
        Object.entries(data.time_series).forEach(([lottery_type, series]) => {
            html += `
                <div class="col-md-6 mb-4">
                    <div class="card shadow h-100">
                        <div class="card-header py-3">
                            <h6 class="m-0 font-weight-bold text-primary">${lottery_type} Time Series</h6>
                        </div>
                        <div class="card-body">
                            <div class="time-series-section">
                                <h5 class="card-title">Trends Over Time</h5>
                                <p class="card-text">
                                    Recent trend: ${series.trend || 'No clear trend'}
                                </p>
                                <ul class="list-group">
            `;
            
            // Add time series details
            if (series && series.data && series.data.length > 0) {
                series.data.slice(0, 5).forEach(point => {
                    html += `
                        <li class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>${point.date}</span>
                                <span class="badge bg-info">${point.value}</span>
                            </div>
                        </li>
                    `;
                });
            } else {
                html += `
                    <li class="list-group-item">No time series data for this lottery type</li>
                `;
            }
            
            html += `
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    function displayWinnersData(data, container) {
        let html = '<div class="col-12"><h4 class="mb-4">Winner Analysis</h4></div>';
        
        // Check if we have valid data
        if (!data || !data.winners || Object.keys(data.winners).length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning">
                        <h5>No Winner Data Available</h5>
                        <p>No winner data could be found in the current lottery dataset.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        // Simple display of winner data
        Object.entries(data.winners).forEach(([lottery_type, winners]) => {
            html += `
                <div class="col-md-6 mb-4">
                    <div class="card shadow h-100">
                        <div class="card-header py-3">
                            <h6 class="m-0 font-weight-bold text-primary">${lottery_type} Winners</h6>
                        </div>
                        <div class="card-body">
                            <div class="winners-section">
                                <h5 class="card-title">Winner Statistics</h5>
                                <ul class="list-group">
            `;
            
            // Add winner details
            if (winners && winners.divisions && Object.keys(winners.divisions).length > 0) {
                Object.entries(winners.divisions).slice(0, 5).forEach(([division, stats]) => {
                    html += `
                        <li class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <span>${division}</span>
                                <span class="badge bg-success">${stats.total_winners} winners</span>
                            </div>
                            <div class="small text-muted">
                                Average prize: ${stats.average_prize || 'Unknown'}
                            </div>
                        </li>
                    `;
                });
            } else {
                html += `
                    <li class="list-group-item">No winner data for this lottery type</li>
                `;
            }
            
            html += `
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    function displayCorrelationsData(data, container) {
        let html = '<div class="col-12"><h4 class="mb-4">Lottery Type Correlations</h4></div>';
        
        // Check if we have valid data
        if (!data || !data.correlations || data.correlations.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning">
                        <h5>No Correlation Data Available</h5>
                        <p>No correlations could be found between lottery types.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        // Display correlations in a table
        html += `
            <div class="col-12 mb-4">
                <div class="card shadow">
                    <div class="card-header py-3">
                        <h6 class="m-0 font-weight-bold text-primary">Lottery Type Correlations</h6>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-bordered">
                                <thead class="table-light">
                                    <tr>
                                        <th>Lottery Type A</th>
                                        <th>Lottery Type B</th>
                                        <th>Correlation</th>
                                        <th>Significance</th>
                                    </tr>
                                </thead>
                                <tbody>
        `;
        
        // Add each correlation row
        data.correlations.forEach(corr => {
            let strengthClass = "text-info";
            if (Math.abs(corr.correlation) > 0.7) {
                strengthClass = "text-danger fw-bold";
            } else if (Math.abs(corr.correlation) > 0.4) {
                strengthClass = "text-warning";
            }
            
            html += `
                <tr>
                    <td>${corr.type_a}</td>
                    <td>${corr.type_b}</td>
                    <td class="${strengthClass}">${corr.correlation.toFixed(2)}</td>
                    <td>${corr.significance || 'Unknown'}</td>
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
        
        container.innerHTML = html;
    }
    
    // Click the first button automatically to show initial content
    const firstTab = document.querySelector('.simple-tab-button');
    if (firstTab) {
        // Only auto-click if we're not on the frequency tab already
        const freqTab = document.getElementById('frequency');
        if (freqTab && !freqTab.classList.contains('active')) {
            console.log("Auto-clicking first simple tab button");
            firstTab.click();
        }
    }
});