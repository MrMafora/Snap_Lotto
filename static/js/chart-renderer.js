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
        // Instead of using complex selectors, just get the first chart-card element
        // This is simpler and should be more reliable
        const chartCards = document.querySelectorAll('.chart-card');
        
        // Get the first chart card
        const chartCard = chartCards[0];
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
            
        // Use a simple approach with direct HTML
        const template = `
            <h5 class="mb-4">Most Frequent Numbers</h5>
            
            <div style="margin-bottom: 30px;">
                <div style="display: flex; flex-direction: column; height: 200px; position: relative;">
                    <!-- Y-axis labels -->
                    <div style="position: absolute; left: 0; top: 0%; font-size: 12px; color: #666;">40</div>
                    <div style="position: absolute; left: 0; top: 20%; font-size: 12px; color: #666;">32</div>
                    <div style="position: absolute; left: 0; top: 40%; font-size: 12px; color: #666;">24</div>
                    <div style="position: absolute; left: 0; top: 60%; font-size: 12px; color: #666;">16</div>
                    <div style="position: absolute; left: 0; top: 80%; font-size: 12px; color: #666;">8</div>
                    <div style="position: absolute; left: 0; bottom: 0; font-size: 12px; color: #666;">0</div>
                    
                    <!-- Chart bars area -->
                    <div id="chart-bars" style="position: absolute; left: 30px; right: 10px; top: 0; bottom: 30px; display: flex; align-items: flex-end; justify-content: space-between;">
                        <!-- Bars will be inserted here dynamically -->
                    </div>
                    
                    <!-- X-axis labels area -->
                    <div id="x-axis-labels" style="position: absolute; left: 30px; right: 10px; bottom: 0; height: 30px; display: flex; justify-content: space-between;">
                        <!-- Number labels will be inserted here dynamically -->
                    </div>
                </div>
            </div>
            
            <!-- Legend -->
            <div class="d-flex mt-2">
                <div class="me-3 small"><span class="badge" style="background-color: #e03237;">&nbsp;</span> Most frequent</div>
                <div class="me-3 small"><span class="badge" style="background-color: #ffe11d;">&nbsp;</span> 2nd most frequent</div>
                <div class="small"><span class="badge" style="background-color: #19a03a;">&nbsp;</span> 3rd most frequent</div>
            </div>
        `;
        
        // Insert the template
        chartCard.innerHTML = template;
        
        // Get the containers for bars and labels
        const barsContainer = document.getElementById('chart-bars');
        const labelsContainer = document.getElementById('x-axis-labels');
        
        // Bar colors
        const barColors = [
            '#e03237', // Red for most frequent
            '#ffe11d', // Yellow for 2nd most frequent
            '#19a03a', // Green for 3rd most frequent
            '#67c6ed', '#67c6ed', '#67c6ed', '#67c6ed', '#67c6ed', '#67c6ed', '#67c6ed' // Blue for the rest
        ];
        
        // Calculate max frequency for scaling
        const maxFrequency = sortedData[0]?.frequency || 40;
        
        // Add bars and labels
        sortedData.forEach((item, index) => {
            const { number, frequency } = item;
            
            // Calculate height percentage based on max frequency
            const heightPercentage = Math.max(5, (frequency / maxFrequency) * 100);
            
            // Create bar
            const barDiv = document.createElement('div');
            barDiv.style.width = '8%';
            barDiv.style.height = `${heightPercentage}%`;
            barDiv.style.backgroundColor = barColors[index];
            barDiv.style.borderTopLeftRadius = '3px';
            barDiv.style.borderTopRightRadius = '3px';
            barDiv.style.position = 'relative';
            barDiv.style.cursor = 'pointer';
            barDiv.style.transition = 'all 0.2s ease';
            
            // Hover effects
            barDiv.addEventListener('mouseenter', function(e) {
                // Highlight the bar
                this.style.transform = 'scale(1.05)';
                this.style.boxShadow = '0 0 8px rgba(0,0,0,0.3)';
                
                // Create tooltip
                const tooltip = document.createElement('div');
                tooltip.className = 'chart-tooltip';
                tooltip.style.position = 'absolute';
                tooltip.style.bottom = '105%';
                tooltip.style.left = '50%';
                tooltip.style.transform = 'translateX(-50%)';
                tooltip.style.backgroundColor = 'rgba(0,0,0,0.8)';
                tooltip.style.color = 'white';
                tooltip.style.padding = '6px 10px';
                tooltip.style.borderRadius = '4px';
                tooltip.style.fontSize = '12px';
                tooltip.style.whiteSpace = 'nowrap';
                tooltip.style.zIndex = '1000';
                tooltip.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
                tooltip.innerHTML = `
                    <div><strong>Number:</strong> ${number}</div>
                    <div><strong>Frequency:</strong> ${frequency} times</div>
                    <div><strong>Percentage:</strong> ${((frequency / maxFrequency) * 100).toFixed(1)}%</div>
                `;
                
                // Add small arrow at bottom
                tooltip.style.setProperty('--tooltip-arrow', '');
                tooltip.style.setProperty('--tooltip-arrow-color', 'rgba(0,0,0,0.8)');
                
                // Append tooltip to bar
                this.appendChild(tooltip);
            });
            
            barDiv.addEventListener('mouseleave', function() {
                // Reset highlight
                this.style.transform = 'scale(1)';
                this.style.boxShadow = 'none';
                
                // Remove tooltip
                const tooltip = this.querySelector('.chart-tooltip');
                if (tooltip) {
                    tooltip.remove();
                }
            });
            
            barsContainer.appendChild(barDiv);
            
            // Create label
            const labelDiv = document.createElement('div');
            labelDiv.style.width = '8%';
            labelDiv.style.textAlign = 'center';
            labelDiv.style.fontSize = '12px';
            labelDiv.style.fontWeight = 'bold';
            labelDiv.textContent = number;
            labelsContainer.appendChild(labelDiv);
        });
        
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