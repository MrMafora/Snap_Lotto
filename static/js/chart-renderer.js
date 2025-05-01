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
        // Find the first chart container (parent element for frequency chart)
        // Using the parent of the frequency chart title to ensure we get the right one
        const chartTitle = document.querySelector('.frequency-chart-title');
        const chartCard = chartTitle ? chartTitle.closest('.chart-card') : 
                         document.querySelectorAll('.chart-card')[0]; // Fallback to the first chart card
        
        if (!chartCard) {
            console.error('Chart card not found');
            return;
        }
        
        console.log('Found chart card:', chartCard);
        
        // Sort data by frequency (descending) and get only top 10
        const sortedData = [...frequencyData]
            .sort((a, b) => b.frequency - a.frequency)
            .filter(item => item.lotteryType === 'All Lottery Types' || item.lotteryType === frequencyData[0].lotteryType)
            .slice(0, 10);
            
        // Use a completely blank slate approach - build the entire chart from scratch
        // Clear everything
        chartCard.innerHTML = '';
        
        // Create the header
        const header = document.createElement('h5');
        header.className = 'mb-4';
        header.textContent = 'Most Frequent Numbers';
        chartCard.appendChild(header);
        
        // Create the Y-axis labels (40, 32, 24, 16, 8, 0)
        const yAxisValues = [40, 32, 24, 16, 8, 0];
        const chartContainer = document.createElement('div');
        chartContainer.style.position = 'relative';
        chartContainer.style.height = '250px';
        chartContainer.style.marginBottom = '20px';
        
        // Add Y-axis labels
        yAxisValues.forEach((value, index) => {
            const label = document.createElement('div');
            label.style.position = 'absolute';
            label.style.left = '0';
            // Position vertically based on index
            label.style.top = `${index * 20}%`;
            label.style.color = '#666';
            label.style.fontSize = '12px';
            label.textContent = value;
            chartContainer.appendChild(label);
        });
        
        // Create container for the bars
        const barsContainer = document.createElement('div');
        barsContainer.style.position = 'absolute';
        barsContainer.style.left = '30px'; // Leave space for Y-axis labels
        barsContainer.style.right = '0';
        barsContainer.style.top = '0';
        barsContainer.style.bottom = '30px'; // Leave space for X-axis labels
        barsContainer.style.display = 'flex';
        barsContainer.style.alignItems = 'flex-end';
        barsContainer.style.justifyContent = 'space-between';
        
        // Add horizontal grid lines
        for (let i = 1; i <= 5; i++) {
            const gridLine = document.createElement('div');
            gridLine.style.position = 'absolute';
            gridLine.style.left = '30px';
            gridLine.style.right = '0';
            gridLine.style.top = `${i * 20}%`;
            gridLine.style.height = '1px';
            gridLine.style.backgroundColor = '#eee';
            chartContainer.appendChild(gridLine);
        }
        
        // Calculate max frequency for scaling
        const maxFrequency = sortedData[0]?.frequency || 40;
        
        // Bar colors
        const barColors = [
            '#e03237', // Red for most frequent
            '#ffe11d', // Yellow for 2nd most frequent
            '#19a03a', // Green for 3rd most frequent
            '#67c6ed', '#67c6ed', '#67c6ed', '#67c6ed', '#67c6ed', '#67c6ed', '#67c6ed' // Blue for the rest
        ];
        
        // Create each bar
        sortedData.forEach((item, index) => {
            const { number, frequency } = item;
            
            // Create bar container
            const barContainer = document.createElement('div');
            barContainer.style.display = 'flex';
            barContainer.style.flexDirection = 'column';
            barContainer.style.alignItems = 'center';
            barContainer.style.width = '8%';
            barContainer.style.position = 'relative';
            
            // Create the bar
            const bar = document.createElement('div');
            // Calculate height based on maximum value (maxFrequency)
            const barHeight = (frequency / maxFrequency) * 100;
            bar.style.width = '70%';
            bar.style.height = `${barHeight}%`;
            bar.style.backgroundColor = barColors[index];
            bar.style.borderTopLeftRadius = '3px';
            bar.style.borderTopRightRadius = '3px';
            
            // Add bar to container
            barContainer.appendChild(bar);
            
            // Add to bars container
            barsContainer.appendChild(barContainer);
            
            // Create X-axis label (number)
            const label = document.createElement('div');
            label.style.position = 'absolute';
            label.style.bottom = '-25px';
            label.style.width = '100%';
            label.style.textAlign = 'center';
            label.style.fontSize = '12px';
            label.style.fontWeight = 'bold';
            label.textContent = number;
            barContainer.appendChild(label);
        });
        
        // Add bars container to chart
        chartContainer.appendChild(barsContainer);
        
        // Add chart container to card
        chartCard.appendChild(chartContainer);
        
        // Add legend below chart
        const legend = document.createElement('div');
        legend.className = 'd-flex mt-2';
        legend.innerHTML = `
            <div class="me-3 small"><span class="badge" style="background-color: #e03237;">&nbsp;</span> Most frequent</div>
            <div class="me-3 small"><span class="badge" style="background-color: #ffe11d;">&nbsp;</span> 2nd most frequent</div>
            <div class="small"><span class="badge" style="background-color: #19a03a;">&nbsp;</span> 3rd most frequent</div>
        `;
        chartCard.appendChild(legend);
        
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