/**
 * Chart Loader for Snap Lotto
 * Handles loading chart data from API endpoints and prepares data for rendering
 */

// Initialize variables when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to lottery type filters
    document.querySelectorAll('[data-lottery-type]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update active state
            document.querySelectorAll('[data-lottery-type]').forEach(el => el.classList.remove('active'));
            e.target.classList.add('active');
            
            // Get the selected lottery type
            const lotteryType = e.target.getAttribute('data-lottery-type');
            
            // Update the displayed filter
            document.querySelector('.current-lottery-type').textContent = e.target.textContent;
            
            // Fetch new data with the selected filter
            fetchChartData(lotteryType, document.querySelector('.current-time-period').textContent === 'All Time' ? 'all' : '365');
        });
    });
    
    // Add event listeners to time period filters
    document.querySelectorAll('[data-time-period]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update active state
            document.querySelectorAll('[data-time-period]').forEach(el => el.classList.remove('active'));
            e.target.classList.add('active');
            
            // Get the selected time period
            const timePeriod = e.target.getAttribute('data-time-period');
            
            // Update the displayed filter
            document.querySelector('.current-time-period').textContent = e.target.textContent;
            
            // Fetch new data with the selected filter
            fetchChartData(document.querySelector('.current-lottery-type').textContent === 'All Lottery Types' ? 'all' : 'Lottery', timePeriod);
        });
    });
    
    // Add event listener to reset button
    document.querySelector('.reset-filters')?.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Reset active states
        document.querySelector('[data-lottery-type="all"]')?.classList.add('active');
        document.querySelectorAll('[data-lottery-type]').forEach(el => {
            if (el.getAttribute('data-lottery-type') !== 'all') {
                el.classList.remove('active');
            }
        });
        
        document.querySelector('[data-time-period="all"]')?.classList.add('active');
        document.querySelectorAll('[data-time-period]').forEach(el => {
            if (el.getAttribute('data-time-period') !== 'all') {
                el.classList.remove('active');
            }
        });
        
        // Reset displayed filters
        document.querySelector('.current-lottery-type').textContent = 'All Lottery Types';
        document.querySelector('.current-time-period').textContent = 'All Time';
        
        // Fetch data with reset filters
        fetchChartData('all', 'all');
    });

    // Initial load data - only if we're on the visualizations page
    if (window.location.pathname === '/visualizations') {
        fetchChartData('all', 'all');
    }
});

// Function to fetch chart data via AJAX
function fetchChartData(lotteryType, timePeriod) {
    // Show loading state for charts
    document.querySelectorAll('.chart-loading').forEach(indicator => {
        indicator.classList.remove('d-none');
    });
    
    // Get the bar chart container for showing loading/error states
    const barChartContainer = document.querySelector('.bar-chart-container');
    if (barChartContainer) {
        barChartContainer.innerHTML = `
            <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading chart data...</span>
            </div>
        `;
    }
    
    // Get the division chart container for showing loading state
    const divisionChartContainer = document.querySelector('.division-chart-container');
    if (divisionChartContainer) {
        divisionChartContainer.innerHTML = `
            <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading division data...</span>
            </div>
        `;
    }
    
    // Convert string parameters to API-compatible format
    const apiLotteryType = lotteryType === 'all' ? null : lotteryType;
    const apiDays = timePeriod === 'all' ? null : timePeriod;
    
    // Log what we're fetching
    console.log(`Fetching data from: /api/lottery-analysis/frequency?days=${apiDays || '365'}`);
    
    // Fetch the data from the API
    fetch(`/api/lottery-analysis/frequency?${apiLotteryType ? 'lottery_type=' + encodeURIComponent(apiLotteryType) + '&' : ''}days=${apiDays || '365'}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Pass data to chart renderer functions
            console.log("Chart data received:", data);
            renderCharts(data);
        })
        .catch(error => {
            console.error("Error fetching chart data:", error);
            // Show error in chart containers
            if (barChartContainer) {
                barChartContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading chart data. Please try again later.
                    </div>
                `;
            }
            
            if (divisionChartContainer) {
                divisionChartContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading division data. Please try again later.
                    </div>
                `;
            }
        })
        .finally(() => {
            // Hide loading indicators
            document.querySelectorAll('.chart-loading').forEach(indicator => {
                indicator.classList.add('d-none');
            });
        });
}

// Process data for rendering
function renderCharts(data) {
    console.log("Updating frequency chart");
    
    // Convert authentic South African lottery frequency data to chart format
    if (data && typeof data === 'object') {
        const frequencyData = [];
        
        // Process the authentic frequency data from all lottery types
        Object.keys(data).forEach(lotteryType => {
            const lotteryData = data[lotteryType];
            if (lotteryData && lotteryData.frequency && Array.isArray(lotteryData.frequency)) {
                // Convert frequency array to number-frequency pairs
                lotteryData.frequency.forEach((freq, index) => {
                    if (freq > 0) {
                        const existingData = frequencyData.find(item => item.number === (index + 1));
                        if (existingData) {
                            existingData.frequency += freq;
                        } else {
                            frequencyData.push({
                                number: index + 1,
                                frequency: freq
                            });
                        }
                    }
                });
            }
        });
        
        // Render the authentic frequency chart if we have data
        if (typeof renderFrequencyChart === 'function' && frequencyData.length > 0) {
            renderFrequencyChart(frequencyData);
        }
        
        // Render Hot & Cold Numbers section with the same authentic data
        if (typeof renderHotColdNumbers === 'function' && frequencyData.length > 0) {
            renderHotColdNumbers(frequencyData);
        }
    }
    
    if (typeof renderDivisionChart === 'function') {
        renderDivisionChart(data.divisionData);
    }
    
    if (typeof renderLotteryTypeSelector === 'function') {
        renderLotteryTypeSelector(data.lotteryTypes);
    }
    
    if (typeof updateStatsSummary === 'function') {
        updateStatsSummary(data.stats);
    }
}