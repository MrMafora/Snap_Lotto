/**
 * Chart Renderer for Snap Lotto
 * Responsible for creating and updating chart visualizations with data from the API
 */

// Function to render the frequency chart with the provided data
function renderFrequencyChart(frequencyData) {
    // Log the received data to help with debugging
    console.log('Frequency data received:', frequencyData);
    
    if (!frequencyData || !Array.isArray(frequencyData) || frequencyData.length === 0) {
        console.warn('No frequency data to render');
        return;
    }
    
    try {
        // Get chart container
        const barChartContainer = document.querySelector('.bar-chart-container');
        if (!barChartContainer) {
            console.error('Bar chart container not found');
            return;
        }
        
        // Clear previous chart
        barChartContainer.innerHTML = '';
        
        // Add title (only once)
        const chartTitle = document.createElement('h5');
        chartTitle.className = 'mb-3';
        chartTitle.textContent = 'Most Frequent Numbers';
        barChartContainer.appendChild(chartTitle);
        
        // Sort data by frequency (descending) and get only top 10
        const sortedData = [...frequencyData]
            .sort((a, b) => b.frequency - a.frequency)
            .filter(item => item.lotteryType === 'All Lottery Types' || item.lotteryType === frequencyData[0].lotteryType)
            .slice(0, 10);
        
        // Get the maximum frequency for scaling
        const maxFrequency = sortedData[0]?.frequency || 1;
        
        // Create a container for the chart
        const chartOuterContainer = document.createElement('div');
        chartOuterContainer.className = 'mb-3';
        
        // Create a container for the number frequency chart with Y-axis labels
        const chartContainer = document.createElement('div');
        chartContainer.className = 'd-flex';
        
        // Create Y-axis labels
        const yAxis = document.createElement('div');
        yAxis.className = 'y-axis me-2 d-flex flex-column justify-content-between';
        yAxis.style.height = '180px';  // Slightly smaller to match image
        
        // Standard y-axis values as seen in the image
        const yValues = [40, 32, 24, 16, 8, 0];
        
        // Create labels using fixed values from the image
        yValues.forEach(value => {
            const yLabel = document.createElement('div');
            yLabel.className = 'text-end small text-muted';
            yLabel.style.fontSize = '12px';
            yLabel.textContent = value;
            yAxis.appendChild(yLabel);
        });
        
        // Create a container for the actual frequency chart
        const frequencyChart = document.createElement('div');
        frequencyChart.className = 'frequency-chart d-flex align-items-end justify-content-between pb-2 flex-grow-1';
        frequencyChart.style.height = '180px'; // Match height with y-axis
        
        // Variables for color coding top numbers (using exact colors from screenshot)
        const colorClasses = [
            'bg-danger',    // 1st place (red)
            'bg-warning',   // 2nd place (yellow)
            'bg-success',   // 3rd place (green)
            'bg-primary',   // Use primary for the rest
            'bg-primary',
            'bg-primary',
            'bg-primary',
            'bg-primary',
            'bg-primary',
            'bg-primary'
        ];
        
        // Create bar for each number (top 10 only)
        sortedData.forEach((item, index) => {
            const { number, frequency } = item;
            
            // Calculate height percentage based on max frequency
            const heightPercentage = (frequency / maxFrequency) * 100;
            
            // Create column for this number
            const barColumn = document.createElement('div');
            barColumn.className = 'bar-column text-center position-relative';
            barColumn.style.width = '40px'; // Fixed width for bars
            barColumn.style.margin = '0 5px'; // Small gap between bars
            
            // Create the bar with fixed width and variable height
            const bar = document.createElement('div');
            bar.className = `interactive-bar ${colorClasses[index]}`;
            bar.style.height = `${heightPercentage}%`;
            bar.style.width = '100%';
            bar.style.borderRadius = '3px';
            // Add margin to bottom to ensure bars appear above the number
            bar.style.marginBottom = '5px';
            bar.setAttribute('data-number', number);
            bar.setAttribute('data-frequency', frequency);
            
            // Add the number label below
            const numberLabel = document.createElement('div');
            numberLabel.className = 'number-label';
            numberLabel.style.fontSize = '14px';
            numberLabel.textContent = number;
            
            // Add hover effects for bar
            bar.addEventListener('mouseover', function() {
                // Create a tooltip
                const tooltip = document.createElement('div');
                tooltip.className = 'chart-tooltip';
                tooltip.innerHTML = `Number ${number}<br>Appeared ${frequency} times`;
                tooltip.style.position = 'absolute';
                tooltip.style.backgroundColor = 'rgba(0,0,0,0.8)';
                tooltip.style.color = 'white';
                tooltip.style.padding = '5px 10px';
                tooltip.style.borderRadius = '4px';
                tooltip.style.fontSize = '12px';
                tooltip.style.zIndex = '1000';
                
                // Position tooltip above the bar
                const rect = this.getBoundingClientRect();
                tooltip.style.left = rect.left + 'px';
                tooltip.style.top = (rect.top - 40) + 'px';
                
                document.body.appendChild(tooltip);
                this.setAttribute('data-tooltip-id', Date.now());
            });
            
            bar.addEventListener('mouseout', function() {
                // Remove any tooltips
                const tooltipId = this.getAttribute('data-tooltip-id');
                if (tooltipId) {
                    const tooltips = document.querySelectorAll('.chart-tooltip');
                    tooltips.forEach(tooltip => tooltip.remove());
                }
            });
            
            // Create a container for the bar and label
            const barContainer = document.createElement('div');
            barContainer.className = 'd-flex flex-column align-items-center';
            barContainer.style.height = '100%';
            
            // Create a div for the bar that takes full height
            const barWrap = document.createElement('div');
            barWrap.className = 'd-flex align-items-end';
            barWrap.style.height = '100%';
            barWrap.appendChild(bar);
            
            // Add the bar wrapper and number label to the container
            barContainer.appendChild(barWrap);
            barContainer.appendChild(numberLabel);
            
            // Add the container to the column
            barColumn.appendChild(barContainer);
            
            // Add column to the chart
            frequencyChart.appendChild(barColumn);
        });
        
        // Add y-axis and frequency chart to the container
        chartContainer.appendChild(yAxis);
        chartContainer.appendChild(frequencyChart);
        
        // Add the chart container to the outer container
        chartOuterContainer.appendChild(chartContainer);
        
        // Add to main container
        barChartContainer.appendChild(chartOuterContainer);
        
        // Add a legend for color coding as shown in the screenshot
        const legend = document.createElement('div');
        legend.className = 'd-flex mt-2';
        legend.innerHTML = `
            <div class="me-3 small"><span class="badge bg-danger">&nbsp;</span> Most frequent</div>
            <div class="me-3 small"><span class="badge bg-warning">&nbsp;</span> 2nd most frequent</div>
            <div class="small"><span class="badge bg-success">&nbsp;</span> 3rd most frequent</div>
        `;
        barChartContainer.appendChild(legend);
        
    } catch (error) {
        console.error('Error rendering frequency chart:', error);
        // Show error in container
        const barChartContainer = document.querySelector('.bar-chart-container');
        if (barChartContainer) {
            barChartContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error rendering chart. Please try again later.
                </div>
            `;
        }
    }
}

// Function to render division statistics chart
function renderDivisionChart(divisionData) {
    // Log the received data to help with debugging
    console.log('Division data received:', divisionData);
    
    if (!divisionData || !Array.isArray(divisionData) || divisionData.length === 0) {
        console.warn('No division data to render');
        return;
    }
    
    try {
        // Get chart container
        const divisionChartContainer = document.querySelector('.division-chart-container');
        if (!divisionChartContainer) {
            console.error('Division chart container not found');
            return;
        }
        
        // Clear previous chart
        divisionChartContainer.innerHTML = '';
        
        // Create a container for the chart and legend
        const chartRow = document.createElement('div');
        chartRow.className = 'row';
        
        // Create pie chart container
        const pieContainer = document.createElement('div');
        pieContainer.className = 'col-md-6 d-flex justify-content-center align-items-center';
        
        // Create SVG for pie chart
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '200');
        svg.setAttribute('height', '200');
        svg.setAttribute('viewBox', '0 0 100 100');
        
        // Colors for pie segments
        const colors = [
            '#dc3545', // Division 1 (red)
            '#fd7e14', // Division 2 (orange)
            '#ffc107', // Division 3 (yellow)
            '#198754', // Division 4 (green)
            '#0d6efd', // Division 5 (blue)
            '#6f42c1', // Division 6 (purple)
            '#6c757d'  // Division 7+ (gray)
        ];
        
        // Calculate total winners
        const totalWinners = divisionData.reduce((sum, item) => sum + item.winners, 0);
        
        // Track the starting angle for each segment
        let startAngle = 0;
        
        // Create pie segments
        divisionData.forEach((item, index) => {
            const { division, winners } = item;
            
            // Calculate percentage and angles for this segment
            const percentage = (winners / totalWinners) * 100;
            const angle = (percentage / 100) * 360;
            const endAngle = startAngle + angle;
            
            // Convert angles to radians for calculation
            const startRad = (startAngle - 90) * Math.PI / 180;
            const endRad = (endAngle - 90) * Math.PI / 180;
            
            // Calculate coordinates
            const x1 = 50 + 50 * Math.cos(startRad);
            const y1 = 50 + 50 * Math.sin(startRad);
            const x2 = 50 + 50 * Math.cos(endRad);
            const y2 = 50 + 50 * Math.sin(endRad);
            
            // Determine if this segment is large (> 180 degrees)
            const largeArcFlag = angle > 180 ? 1 : 0;
            
            // Create pie segment path
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', `M 50 50 L ${x1} ${y1} A 50 50 0 ${largeArcFlag} 1 ${x2} ${y2} Z`);
            path.setAttribute('fill', colors[index % colors.length]);
            path.setAttribute('class', 'pie-segment');
            path.setAttribute('data-division', division);
            path.setAttribute('data-winners', winners);
            path.setAttribute('data-percentage', percentage.toFixed(1));
            
            // Add hover interactivity
            path.addEventListener('mouseover', function() {
                // Highlight this segment
                this.style.opacity = '1';
                this.style.transform = 'scale(1.03)';
                this.style.transformOrigin = 'center';
                this.style.transition = 'all 0.2s ease';
                
                // Create tooltip with data
                const tooltip = document.createElement('div');
                tooltip.className = 'chart-tooltip pie-tooltip';
                tooltip.innerHTML = `Division ${division}<br>${winners} winners<br>${percentage.toFixed(1)}% of total`;
                tooltip.style.position = 'absolute';
                tooltip.style.backgroundColor = 'rgba(0,0,0,0.8)';
                tooltip.style.color = 'white';
                tooltip.style.padding = '5px 10px';
                tooltip.style.borderRadius = '4px';
                tooltip.style.fontSize = '12px';
                tooltip.style.zIndex = '1000';
                
                // Position tooltip near segment
                const rect = this.getBoundingClientRect();
                tooltip.style.left = (rect.left + rect.width/2) + 'px';
                tooltip.style.top = (rect.top + rect.height/2 - 40) + 'px';
                
                document.body.appendChild(tooltip);
            });
            
            path.addEventListener('mouseout', function() {
                // Reset styling
                this.style.opacity = '1';
                this.style.transform = 'scale(1)';
                
                // Remove tooltip
                const tooltips = document.querySelectorAll('.pie-tooltip');
                tooltips.forEach(tooltip => tooltip.remove());
            });
            
            svg.appendChild(path);
            
            // Update start angle for next segment
            startAngle = endAngle;
        });
        
        pieContainer.appendChild(svg);
        
        // Create legend container
        const legendContainer = document.createElement('div');
        legendContainer.className = 'col-md-6';
        
        // Create legend list
        const legend = document.createElement('div');
        legend.className = 'division-legend';
        
        divisionData.forEach((item, index) => {
            const { division, winners } = item;
            const percentage = (winners / totalWinners) * 100;
            
            // Create legend item
            const legendItem = document.createElement('div');
            legendItem.className = 'legend-item mb-1 d-flex align-items-center px-2 py-1 rounded';
            legendItem.setAttribute('data-division', division);
            
            legendItem.innerHTML = `
                <span class="color-dot me-2" style="background-color: ${colors[index % colors.length]}; width: 12px; height: 12px; display: inline-block; border-radius: 50%;"></span>
                <span>Division ${division}: ${winners} winners (${percentage.toFixed(1)}%)</span>
            `;
            
            // Add hover interactivity to legend items
            legendItem.addEventListener('mouseover', function() {
                this.style.fontWeight = 'bold';
                this.style.backgroundColor = 'rgba(0,0,0,0.05)';
                
                // Highlight corresponding pie segment
                const pieSegments = document.querySelectorAll('.pie-segment');
                pieSegments.forEach(segment => {
                    if (segment.getAttribute('data-division') === division) {
                        segment.style.opacity = '1';
                        segment.style.transform = 'scale(1.03)';
                        segment.style.transformOrigin = 'center';
                    } else {
                        segment.style.opacity = '0.7';
                    }
                });
            });
            
            legendItem.addEventListener('mouseout', function() {
                this.style.fontWeight = 'normal';
                this.style.backgroundColor = 'transparent';
                
                // Reset all pie segments
                const pieSegments = document.querySelectorAll('.pie-segment');
                pieSegments.forEach(segment => {
                    segment.style.opacity = '1';
                    segment.style.transform = 'scale(1)';
                });
            });
            
            legend.appendChild(legendItem);
        });
        
        legendContainer.appendChild(legend);
        
        // Assemble the chart
        chartRow.appendChild(pieContainer);
        chartRow.appendChild(legendContainer);
        divisionChartContainer.appendChild(chartRow);
        
    } catch (error) {
        console.error('Error rendering division chart:', error);
        // Show error in container
        const divisionChartContainer = document.querySelector('.division-chart-container');
        if (divisionChartContainer) {
            divisionChartContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error rendering division chart. Please try again later.
                </div>
            `;
        }
    }
}

// Function to highlight a specific pie segment
function highlightPieSegment(division) {
    const pieSegments = document.querySelectorAll('.pie-segment');
    pieSegments.forEach(segment => {
        if (segment.getAttribute('data-division') === division) {
            segment.style.opacity = '1';
            segment.style.transform = 'scale(1.03)';
            segment.style.transformOrigin = 'center';
            segment.style.transition = 'all 0.2s ease';
            
            // Create tooltip with data
            const winners = segment.getAttribute('data-winners');
            const percentage = segment.getAttribute('data-percentage');
            
            const tooltip = document.createElement('div');
            tooltip.className = 'chart-tooltip pie-tooltip';
            tooltip.innerHTML = `Division ${division}<br>${winners} winners<br>${percentage}% of total`;
            tooltip.style.position = 'absolute';
            tooltip.style.backgroundColor = 'rgba(0,0,0,0.8)';
            tooltip.style.color = 'white';
            tooltip.style.padding = '5px 10px';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '12px';
            tooltip.style.zIndex = '1000';
            
            // Position tooltip near segment
            const rect = segment.getBoundingClientRect();
            tooltip.style.left = (rect.left + rect.width/2) + 'px';
            tooltip.style.top = (rect.top - 40) + 'px';
            
            document.body.appendChild(tooltip);
        } else {
            segment.style.opacity = '0.7';
        }
    });
}

// Function to reset all pie segments to normal
function resetPieSegments() {
    const pieSegments = document.querySelectorAll('.pie-segment');
    pieSegments.forEach(segment => {
        segment.style.opacity = '1';
        segment.style.transform = 'scale(1)';
    });
    
    // Remove any tooltips
    const tooltips = document.querySelectorAll('.pie-tooltip');
    tooltips.forEach(tooltip => tooltip.remove());
}

// Function to update lottery type selector based on available data
function renderLotteryTypeSelector(lotteryTypes) {
    // Log the received lottery types to help with debugging
    console.log('Lottery types received:', lotteryTypes);
    
    if (!lotteryTypes || !Array.isArray(lotteryTypes)) {
        console.warn('No lottery types data available');
        return;
    }
    
    // Find lottery type dropdown container
    const lotteryTypeDropdown = document.querySelector('.lottery-type-dropdown');
    if (!lotteryTypeDropdown) {
        console.warn('Lottery type dropdown not found');
        return;
    }
    
    try {
        // Update available lottery types in the dropdown
        const items = lotteryTypeDropdown.querySelectorAll('.dropdown-item[data-lottery-type]');
        
        // First add the "All" option
        if (items.length === 0) {
            const allItem = document.createElement('a');
            allItem.className = 'dropdown-item active';
            allItem.href = '#';
            allItem.textContent = 'All Lottery Types';
            allItem.setAttribute('data-lottery-type', 'all');
            lotteryTypeDropdown.appendChild(allItem);
            
            // Add event listener
            allItem.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Update active state
                document.querySelectorAll('[data-lottery-type]').forEach(el => el.classList.remove('active'));
                this.classList.add('active');
                
                // Update displayed filter
                document.querySelector('.current-lottery-type').textContent = this.textContent;
                
                // Fetch data
                fetchChartData('all', document.querySelector('.current-time-period').textContent === 'All Time' ? 'all' : '365');
            });
        }
        
        // Then add each lottery type
        lotteryTypes.forEach(type => {
            // Skip if this type already exists in the dropdown
            const existing = Array.from(items).find(item => item.textContent === type);
            if (existing) return;
            
            // Create new dropdown item
            const item = document.createElement('a');
            item.className = 'dropdown-item';
            item.href = '#';
            item.textContent = type;
            item.setAttribute('data-lottery-type', type);
            lotteryTypeDropdown.appendChild(item);
            
            // Add event listener
            item.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Update active state
                document.querySelectorAll('[data-lottery-type]').forEach(el => el.classList.remove('active'));
                this.classList.add('active');
                
                // Update displayed filter
                document.querySelector('.current-lottery-type').textContent = this.textContent;
                
                // Fetch data
                fetchChartData(type, document.querySelector('.current-time-period').textContent === 'All Time' ? 'all' : '365');
            });
        });
    } catch (error) {
        console.error('Error updating lottery type selector:', error);
    }
}

// Function to update stats summary with latest data
function updateStatsSummary(stats) {
    // Log the stats data to help with debugging
    console.log('Stats data received:', stats);
    
    if (!stats) {
        console.warn('No stats data available');
        return;
    }
    
    try {
        // Find the stats container
        const statsContainer = document.querySelector('.stats-summary');
        if (!statsContainer) {
            console.warn('Stats summary container not found');
            return;
        }
        
        // Update total draws
        const totalDraws = statsContainer.querySelector('.total-draws');
        if (totalDraws && stats.totalDraws) {
            totalDraws.textContent = stats.totalDraws.toLocaleString();
        }
        
        // Update total prize money
        const totalPrizeMoney = statsContainer.querySelector('.total-prize-money');
        if (totalPrizeMoney && stats.totalPrizeMoney) {
            totalPrizeMoney.textContent = `R${stats.totalPrizeMoney.toLocaleString()}`;
        }
        
        // Update total winners
        const totalWinners = statsContainer.querySelector('.total-winners');
        if (totalWinners && stats.totalWinners) {
            totalWinners.textContent = stats.totalWinners.toLocaleString();
        }
        
        // Update largest jackpot
        const largestJackpot = statsContainer.querySelector('.largest-jackpot');
        if (largestJackpot && stats.largestJackpot) {
            largestJackpot.textContent = `R${stats.largestJackpot.toLocaleString()}`;
        }
    } catch (error) {
        console.error('Error updating stats summary:', error);
    }
}