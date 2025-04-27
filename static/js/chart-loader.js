/**
 * Enhanced Chart Loading and Rendering Module
 * This module handles fetching lottery frequency data and rendering charts
 */

// Cache for chart data to prevent unnecessary API calls
let chartDataCache = null;
let currentLotteryType = 'all';
let currentTimePeriod = 'all';

/**
 * Initialize event listeners for chart interaction
 */
function initChartControls() {
    // Add event listeners to lottery type filters
    document.querySelectorAll('[data-lottery-type]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update active state
            document.querySelectorAll('[data-lottery-type]').forEach(el => el.classList.remove('active'));
            e.target.classList.add('active');
            
            // Get the selected lottery type
            const lotteryType = e.target.getAttribute('data-lottery-type');
            currentLotteryType = lotteryType;
            
            // Update the displayed filter
            document.querySelector('.current-lottery-type').textContent = e.target.textContent;
            
            // Fetch new data with the selected filter
            fetchChartData(lotteryType, currentTimePeriod);
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
            currentTimePeriod = timePeriod;
            
            // Update the displayed filter
            document.querySelector('.current-time-period').textContent = e.target.textContent;
            
            // Fetch new data with the selected filter
            fetchChartData(currentLotteryType, timePeriod);
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
        
        // Reset globals
        currentLotteryType = 'all';
        currentTimePeriod = 'all';
        
        // Fetch data with reset filters
        fetchChartData('all', 'all');
    });
    
    // Initial data load
    fetchChartData('all', 'all');
}

/**
 * Fetch chart data from API
 * @param {string} lotteryType - Type of lottery to fetch data for
 * @param {string} timePeriod - Time period to fetch data for
 */
function fetchChartData(lotteryType, timePeriod) {
    // Show loading indicators
    document.querySelectorAll('.chart-loading').forEach(indicator => {
        indicator.classList.remove('d-none');
    });
    
    // Clear any existing charts while loading
    const barChartContainer = document.querySelector('.bar-chart-container');
    if (barChartContainer) {
        // Save any header element present
        const header = barChartContainer.querySelector('h6');
        barChartContainer.innerHTML = `
            <div class="d-flex justify-content-center align-items-center" style="height: 150px;">
                <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                <span class="ms-2">Loading chart data...</span>
            </div>
        `;
        // Restore header if it existed
        if (header) {
            barChartContainer.prepend(header);
        }
    }
    
    // Build the API URL with query parameters - properly handle the lottery type parameter
    // We need to keep the empty string if it's 'all' or not specified
    const params = new URLSearchParams();
    
    // Only add lottery_type if it's not 'all'
    if (lotteryType && lotteryType !== 'all') {
        // Make sure to always use the normalized terminology
        const normalizedType = normalizeLotteryType(lotteryType);
        params.append('lottery_type', normalizedType);
    }
    
    // Helper function to normalize lottery type names for consistency
    function normalizeLotteryType(type) {
        // If the type already uses "Lottery" terminology, return as is
        if (type.includes("Lottery")) {
            return type;
        }
        
        // Otherwise, map "Lotto" to "Lottery" while preserving other parts of the name
        return type.replace(/\bLotto\b/g, "Lottery");
    }
    
    // Add days parameter with default 365 for 'all'
    params.append('days', timePeriod === 'all' ? '365' : timePeriod);
    
    const apiUrl = `/api/lottery-analysis/frequency?${params.toString()}`;
    
    console.log("Fetching data from: " + apiUrl);
    
    // Fetch data from the API
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Chart data received:", Object.keys(data));
            
            // Cache the chart data
            chartDataCache = data;
            
            // Update the charts with the new data
            updateCharts(data);
            
            // Hide loading indicators
            document.querySelectorAll('.chart-loading').forEach(indicator => {
                indicator.classList.add('d-none');
            });
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
            
            // Hide loading indicators even on error
            document.querySelectorAll('.chart-loading').forEach(indicator => {
                indicator.classList.add('d-none');
            });
            
            // Show a more user-friendly error message in the chart container
            const barChartContainer = document.querySelector('.bar-chart-container');
            if (barChartContainer) {
                barChartContainer.innerHTML = `
                    <div class="alert alert-danger text-center my-5">
                        <p>Error loading chart data. Please try again later.</p>
                        <button class="btn btn-sm btn-outline-danger mt-2" onclick="fetchChartData('${lotteryType}', '${timePeriod}')">
                            Retry
                        </button>
                    </div>
                `;
            }
        });
}

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chart controls
    initChartControls();
});