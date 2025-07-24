/**
 * Chart Renderer for Snap Lotto
 * Responsible for creating and updating chart visualizations with data from the API
 */
console.log('CHART RENDERER JS: External chart renderer file loaded successfully');

// Function to render the frequency chart with the provided data
function renderExternalFrequencyChart(frequencyData) {
    console.log('CHART RENDERER: renderExternalFrequencyChart called with:', frequencyData);
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
        
        // Create a container for the number frequency chart with responsive spacing
        const frequencyChart = document.createElement('div');
        frequencyChart.className = 'frequency-chart d-flex align-items-end justify-content-center pb-2';
        frequencyChart.style.height = '200px';
        
        // Responsive gap based on screen width
        const screenWidth = window.innerWidth;
        const gap = screenWidth < 480 ? '2px' : screenWidth < 768 ? '4px' : '6px';
        frequencyChart.style.gap = gap;
        
        frequencyChart.style.width = '100%';
        frequencyChart.style.padding = '10px 5px'; // Minimal padding for mobile
        frequencyChart.style.maxWidth = '100%';
        frequencyChart.style.margin = '0';
        frequencyChart.style.boxSizing = 'border-box';
        frequencyChart.style.overflowX = 'hidden'; // Prevent horizontal scroll
        
        // Sort data by frequency (descending)
        const sortedData = [...frequencyData].sort((a, b) => b.frequency - a.frequency);
        
        // Get the maximum frequency for scaling
        const maxFrequency = sortedData[0]?.frequency || 1;
        
        // Variables for color coding top numbers
        const colorClasses = [
            'bg-danger',    // 1st place (red)
            'bg-warning',   // 2nd place (yellow)
            'bg-success'    // 3rd place (green)
        ];
        
        // Create bar for ONLY the top 10 numbers
        const top10Data = sortedData.slice(0, 10);
        console.log('CHART RENDERER: Displaying exactly', top10Data.length, 'bars:', top10Data);
        
        top10Data.forEach((item, index) => {
            const { number, frequency } = item;
            
            // Calculate height percentage with better visual balance and symmetry
            // Use a more gradual scale for better visual harmony
            const minHeight = 25; // Minimum height for smallest bars
            const maxHeight = 100; // Maximum height for tallest bars
            const heightRange = maxHeight - minHeight;
            
            // Create more symmetric scaling using a gentler curve
            const normalizedFreq = frequency / maxFrequency;
            const heightPercentage = minHeight + (normalizedFreq * heightRange * 0.8);
            
            // Calculate responsive bar width first
            const barWidth = screenWidth < 480 ? '24px' : screenWidth < 768 ? '30px' : '36px';
            
            // Create column for this number with responsive width
            const barColumn = document.createElement('div');
            barColumn.className = 'bar-column interactive-bar-column text-center position-relative';
            barColumn.setAttribute('data-number', number);
            barColumn.setAttribute('data-frequency', frequency);
            barColumn.setAttribute('data-bs-title', `Number ${number} appeared ${frequency} times`);
            barColumn.setAttribute('data-bs-toggle', 'tooltip');
            barColumn.setAttribute('data-bs-placement', 'top');
            
            // Make sure the column width matches the bar width
            barColumn.style.minWidth = barWidth;
            barColumn.style.maxWidth = barWidth;
            
            // Create interactive bar container with proper height and bottom alignment
            const barContainer = document.createElement('div');
            barContainer.className = 'interactive-bar-container';
            barContainer.style.height = '170px';
            barContainer.style.display = 'flex';
            barContainer.style.alignItems = 'flex-end'; // Align bars to bottom
            
            // Create the actual bar with appropriate height and color
            const bar = document.createElement('div');
            bar.className = `interactive-bar ${index < 3 ? colorClasses[index] : 'bg-primary'}`;
            bar.style.height = `${heightPercentage}%`;
            bar.style.width = barWidth;
            
            bar.style.borderRadius = '4px';
            bar.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            bar.style.transition = 'transform 0.2s';
            bar.setAttribute('data-number', number);
            bar.setAttribute('data-frequency', frequency);
            
            // Add the number label below
            const numberLabel = document.createElement('div');
            numberLabel.className = 'number-label mt-1';
            numberLabel.textContent = number;
            
            // Add hover effects for bar
            bar.addEventListener('mouseover', function() {
                // Scale up the bar slightly on hover
                this.style.transform = 'scaleY(1.05)';
                this.style.transition = 'transform 0.2s';
                
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
                // Return to normal size
                this.style.transform = 'scaleY(1)';
                
                // Remove any tooltips
                const tooltipId = this.getAttribute('data-tooltip-id');
                if (tooltipId) {
                    const tooltips = document.querySelectorAll('.chart-tooltip');
                    tooltips.forEach(tooltip => tooltip.remove());
                }
            });
            
            // Add click event listener for interactive functionality
            bar.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Chart bar clicked for number:', number);
                
                // Call the global highlight function if available
                if (typeof window.highlightNumber === 'function') {
                    window.highlightNumber(number, frequency);
                } else {
                    console.error('highlightNumber function not available');
                }
            });
            
            // Make bar column clickable too
            barColumn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Chart column clicked for number:', number);
                
                if (typeof window.highlightNumber === 'function') {
                    window.highlightNumber(number, frequency);
                } else {
                    console.error('highlightNumber function not available');
                }
            });
            
            // Assemble the components
            barContainer.appendChild(bar);
            barColumn.appendChild(barContainer);
            barColumn.appendChild(numberLabel);
            frequencyChart.appendChild(barColumn);
        });
        
        // Add the frequency chart to the container
        barChartContainer.appendChild(frequencyChart);
        
        // Add a legend for color coding
        const legend = document.createElement('div');
        legend.className = 'frequency-legend d-flex justify-content-center mt-3 small text-muted';
        legend.innerHTML = `
            <div class="me-3"><span class="badge bg-danger">&nbsp;</span> Most frequent</div>
            <div class="me-3"><span class="badge bg-warning">&nbsp;</span> 2nd most frequent</div>
            <div><span class="badge bg-success">&nbsp;</span> 3rd most frequent</div>
        `;
        barChartContainer.appendChild(legend);
        
        // Add click event listeners to all bar elements after a short delay
        setTimeout(() => {
            const barColumns = document.querySelectorAll('.interactive-bar-column');
            console.log('Chart renderer: Adding click handlers to', barColumns.length, 'bar columns');
            
            barColumns.forEach(column => {
                const number = column.getAttribute('data-number');
                const frequency = column.getAttribute('data-frequency');
                
                if (number && frequency) {
                    column.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Bar column clicked:', number, frequency);
                        
                        if (typeof window.highlightNumber === 'function') {
                            window.highlightNumber(parseInt(number), parseInt(frequency));
                        } else {
                            console.error('highlightNumber function not available');
                        }
                    });
                    
                    // Also add click handlers to child bar elements
                    const bars = column.querySelectorAll('.interactive-bar');
                    bars.forEach(bar => {
                        bar.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log('Bar element clicked:', number, frequency);
                            
                            if (typeof window.highlightNumber === 'function') {
                                window.highlightNumber(parseInt(number), parseInt(frequency));
                            }
                        });
                    });
                }
            });
        }, 200);
        
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

// Function to render Hot & Cold Numbers section
window.renderHotColdNumbers = function(frequencyData) {
    console.log('CHART RENDERER: renderHotColdNumbers called with:', frequencyData);
    
    if (!frequencyData || !Array.isArray(frequencyData) || frequencyData.length === 0) {
        console.warn('No frequency data available for hot/cold numbers');
        return;
    }
    
    try {
        // Sort data by frequency (descending for hot, ascending for cold)
        const sortedData = [...frequencyData].sort((a, b) => b.frequency - a.frequency);
        
        // Get hot numbers (top 5 most frequent)
        const hotNumbers = sortedData.slice(0, 5);
        
        // Get cold numbers (bottom 5 least frequent)
        const coldNumbers = sortedData.slice(-5).reverse(); // Reverse to show least frequent first
        
        // Update Hot Numbers section
        const hotNumbersContainer = document.getElementById('hotNumbersContainer');
        console.log('CHART RENDERER: Found hotNumbersContainer:', !!hotNumbersContainer, 'Hot numbers:', hotNumbers.length);
        
        if (hotNumbersContainer && hotNumbers.length > 0) {
            const colors = ['lottery-ball-red', 'lottery-ball-yellow', 'lottery-ball-green', 'lottery-ball-blue', 'lottery-ball-red'];
            let hotHTML = '';
            
            hotNumbers.forEach((item, index) => {
                hotHTML += `
                    <div class="hot-number-item interactive-number me-1 mb-1" data-number="${item.number}" data-frequency="${item.frequency}" style="cursor: pointer;">
                        <span class="lottery-ball ${colors[index]}">
                            <span class="number">${item.number}</span>
                        </span>
                        <small class="frequency-label d-block text-center mt-1" style="font-size: 0.65rem;">${item.frequency}x</small>
                    </div>
                `;
            });
            
            console.log('CHART RENDERER: Setting hotNumbersContainer innerHTML to:', hotHTML.substring(0, 200) + '...');
            hotNumbersContainer.innerHTML = hotHTML;
            
            // Add click event listeners to hot numbers
            setTimeout(() => {
                hotNumbersContainer.querySelectorAll('.interactive-number').forEach(element => {
                    element.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        const number = parseInt(this.getAttribute('data-number'));
                        const frequency = parseInt(this.getAttribute('data-frequency'));
                        console.log('Hot number clicked:', number, frequency);
                        if (typeof window.highlightNumber === 'function') {
                            window.highlightNumber(number, frequency);
                        }
                    });
                });
            }, 100);
        }
        
        // Update Cold Numbers section
        const coldNumbersContainer = document.getElementById('coldNumbersContainer');
        console.log('CHART RENDERER: Found coldNumbersContainer:', !!coldNumbersContainer, 'Cold numbers:', coldNumbers.length);
        
        if (coldNumbersContainer && coldNumbers.length > 0) {
            let coldHTML = '';
            
            coldNumbers.forEach((item, index) => {
                coldHTML += `
                    <div class="cold-number-item interactive-number me-1 mb-1" data-number="${item.number}" data-frequency="${item.frequency}" style="cursor: pointer;">
                        <span class="lottery-ball lottery-ball-blue">
                            <span class="number">${item.number}</span>
                        </span>
                        <small class="frequency-label d-block text-center mt-1" style="font-size: 0.65rem;">${item.frequency}x</small>
                    </div>
                `;
            });
            
            console.log('CHART RENDERER: Setting coldNumbersContainer innerHTML');
            coldNumbersContainer.innerHTML = coldHTML;
            
            // Add click event listeners to cold numbers
            setTimeout(() => {
                coldNumbersContainer.querySelectorAll('.interactive-number').forEach(element => {
                    element.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        const number = parseInt(this.getAttribute('data-number'));
                        const frequency = parseInt(this.getAttribute('data-frequency'));
                        console.log('Cold number clicked:', number, frequency);
                        if (typeof window.highlightNumber === 'function') {
                            window.highlightNumber(number, frequency);
                        }
                    });
                });
            }, 100);
        }
        
        // Update Numbers Not Drawn Recently section
        const absentNumbersContainer = document.getElementById('absentNumbersContainer');
        console.log('CHART RENDERER: Found absentNumbersContainer:', !!absentNumbersContainer);
        
        if (absentNumbersContainer && coldNumbers.length > 0) {
            let absentHTML = '';
            
            // Show the 5 least frequent numbers as "not drawn recently"
            const absentNumbers = coldNumbers.slice(0, 5);
            absentNumbers.forEach((item, index) => {
                absentHTML += `
                    <div class="absent-number-item interactive-number me-1 mb-1" data-number="${item.number}" data-frequency="${item.frequency}" style="cursor: pointer;">
                        <span class="lottery-ball lottery-ball-green">
                            <span class="number">${item.number}</span>
                        </span>
                        <small class="frequency-label d-block text-center mt-1" style="font-size: 0.65rem;">${item.frequency}x</small>
                    </div>
                `;
            });
            
            console.log('CHART RENDERER: Setting absentNumbersContainer innerHTML');
            absentNumbersContainer.innerHTML = absentHTML;
            
            // Add click event listeners to absent numbers
            setTimeout(() => {
                absentNumbersContainer.querySelectorAll('.interactive-number').forEach(element => {
                    element.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        const number = parseInt(this.getAttribute('data-number'));
                        const frequency = parseInt(this.getAttribute('data-frequency'));
                        console.log('Absent number clicked:', number, frequency);
                        if (typeof window.highlightNumber === 'function') {
                            window.highlightNumber(number, frequency);
                        }
                    });
                });
            }, 100);
        }
        
    } catch (error) {
        console.error('Error rendering hot/cold numbers:', error);
    }
};

// Function to render division statistics chart
function renderDivisionChart(divisionData) {
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