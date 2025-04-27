/**
 * Chart Rendering Module
 * Handles rendering of frequency charts and number visualizations
 */

/**
 * Update all chart visualizations with new data
 * @param {Object} data - Chart data from API
 */
function updateCharts(data) {
    // Check if we have valid data
    if (!data || typeof data !== 'object') {
        console.error('Invalid chart data received');
        return;
    }
    
    // Update frequency chart
    updateFrequencyChart(data);
    
    // Update hot and cold numbers section
    updateHotColdNumbers(data);
    
    // Update division statistics (if available)
    if (typeof updateDivisionChart === 'function') {
        updateDivisionChart(data);
    }
}

/**
 * Update the frequency chart visualization
 * @param {Object} data - Chart data from API
 */
function updateFrequencyChart(data) {
    console.log("Updating frequency chart");
    
    // Get the bar chart container
    const barChartContainer = document.querySelector('.bar-chart-container');
    if (!barChartContainer) {
        console.error('Bar chart container not found');
        return;
    }
    
    // Reset the container styles for a fresh implementation
    barChartContainer.style.position = 'relative';
    barChartContainer.style.height = '300px';
    barChartContainer.style.width = '100%';
    barChartContainer.style.overflow = 'hidden';
    
    // Find the lottery type with the most data
    let selectedLotteryType = null;
    let maxFrequencyData = [];
    
    for (const lotteryType in data) {
        if (data[lotteryType] && 
            data[lotteryType].frequency && 
            data[lotteryType].frequency.length > maxFrequencyData.length) {
            maxFrequencyData = data[lotteryType].frequency;
            selectedLotteryType = lotteryType;
        }
    }
    
    // If we have no data, show a message and return
    if (!selectedLotteryType) {
        barChartContainer.innerHTML = '<div class="text-center my-5">No frequency data available for the selected filters.</div>';
        return;
    }
    
    // Get the frequency and top numbers data
    const frequencyData = data[selectedLotteryType].frequency || [];
    const topNumbers = data[selectedLotteryType].top_numbers || [];
    
    // If no frequency data or top numbers, show a message and return
    if (!frequencyData.length || !topNumbers.length) {
        barChartContainer.innerHTML = '<div class="text-center my-5">No frequency data available for the selected filters.</div>';
        return;
    }
    
    // Clear the container
    barChartContainer.innerHTML = '';
    
    // Create the chart header
    const header = document.createElement('h6');
    header.className = 'mb-3';
    header.innerHTML = 'Most Frequent Numbers <small class="text-muted">(' + selectedLotteryType + ')</small>';
    barChartContainer.appendChild(header);
    
    // Create the main chart container
    const chartWrapper = document.createElement('div');
    chartWrapper.style.position = 'relative';
    chartWrapper.style.height = '220px';
    chartWrapper.style.marginBottom = '20px';
    barChartContainer.appendChild(chartWrapper);
    
    // Calculate max frequency for scaling
    let maxFrequency = 0;
    topNumbers.forEach(item => {
        if (Array.isArray(item) && item.length >= 2) {
            maxFrequency = Math.max(maxFrequency, item[1]);
        }
    });
    
    // Y-axis setup
    const yAxis = document.createElement('div');
    yAxis.style.position = 'absolute';
    yAxis.style.left = '0';
    yAxis.style.top = '0';
    yAxis.style.bottom = '30px';
    yAxis.style.width = '30px';
    chartWrapper.appendChild(yAxis);
    
    // Calculate appropriate step size
    const stepSize = maxFrequency <= 10 ? 2 : 
                  maxFrequency <= 20 ? 4 : 
                  maxFrequency <= 32 ? 5 : 8;
    
    // Round max Y value to next multiple of step size
    const maxYValue = Math.ceil(maxFrequency / stepSize) * stepSize;
    
    // Create Y-axis labels
    for (let i = 0; i <= 4; i++) {
        const value = Math.round((4-i) * maxYValue / 4);
        const label = document.createElement('div');
        label.textContent = value;
        label.style.position = 'absolute';
        label.style.right = '7px';
        label.style.top = `${i * 25}%`;
        label.style.fontSize = '12px';
        label.style.color = '#666';
        yAxis.appendChild(label);
    }
    
    // Create chart area
    const chartArea = document.createElement('div');
    chartArea.style.position = 'absolute';
    chartArea.style.left = '30px';
    chartArea.style.right = '0';
    chartArea.style.top = '0';
    chartArea.style.bottom = '30px';
    chartArea.style.borderLeft = '1px solid #ddd';
    chartArea.style.borderBottom = '1px solid #ddd';
    chartWrapper.appendChild(chartArea);
    
    // Add grid lines
    for (let i = 1; i <= 4; i++) {
        const gridLine = document.createElement('div');
        gridLine.style.position = 'absolute';
        gridLine.style.left = '0';
        gridLine.style.right = '0';
        gridLine.style.top = `${i * 25}%`;
        gridLine.style.height = '1px';
        gridLine.style.backgroundColor = '#eee';
        chartArea.appendChild(gridLine);
    }
    
    // Create bars container
    const barsContainer = document.createElement('div');
    barsContainer.style.display = 'flex';
    barsContainer.style.justifyContent = 'space-around';
    barsContainer.style.height = '100%';
    barsContainer.style.padding = '0 20px';
    chartArea.appendChild(barsContainer);
    
    // Fixed bar colors from most to least
    const barColors = [
        '#e03237',  // Red - 1st place
        '#ffe11d',  // Yellow - 2nd place
        '#19a03a',  // Green - 3rd place
        '#67c6ed',  // Blue - others
        '#67c6ed'   // Blue - others
    ];
    
    // Create bars for top 5 numbers
    const displayNumbers = topNumbers.slice(0, 5);
    displayNumbers.forEach((item, index) => {
        if (!Array.isArray(item) || item.length < 2) return;
        
        const [number, frequency] = item;
        
        // Create bar column
        const barColumn = document.createElement('div');
        barColumn.className = 'bar-column';
        barColumn.style.display = 'flex';
        barColumn.style.flexDirection = 'column-reverse';
        barColumn.style.alignItems = 'center';
        barColumn.style.width = '18%';
        barColumn.style.height = '100%';
        barColumn.dataset.number = number;
        barColumn.dataset.frequency = frequency;
        barsContainer.appendChild(barColumn);
        
        // Calculate bar height as percentage of max
        const heightPercent = (frequency / maxYValue) * 100;
        
        // Create bar with container for better styling
        const barContainer = document.createElement('div');
        barContainer.style.position = 'relative';
        barContainer.style.width = '80%';
        barContainer.style.height = `${heightPercent}%`;
        barColumn.appendChild(barContainer);
        
        // Create the actual bar
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.position = 'absolute';
        bar.style.bottom = '0';
        bar.style.left = '0';
        bar.style.right = '0';
        bar.style.height = '100%';
        bar.style.backgroundColor = barColors[Math.min(index, barColors.length - 1)];
        bar.style.borderTopLeftRadius = '3px';
        bar.style.borderTopRightRadius = '3px';
        bar.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
        barContainer.appendChild(bar);
        
        // Add frequency label
        const freqLabel = document.createElement('span');
        freqLabel.style.position = 'absolute';
        freqLabel.style.top = '-15px';
        freqLabel.style.left = '50%';
        freqLabel.style.transform = 'translateX(-50%)';
        freqLabel.style.fontSize = '10px';
        freqLabel.style.color = '#666';
        freqLabel.textContent = frequency;
        barContainer.appendChild(freqLabel);
    });
    
    // Add X-axis labels
    const xAxis = document.createElement('div');
    xAxis.style.position = 'absolute';
    xAxis.style.left = '30px';
    xAxis.style.right = '0';
    xAxis.style.bottom = '0';
    xAxis.style.height = '30px';
    xAxis.style.display = 'flex';
    xAxis.style.justifyContent = 'space-around';
    xAxis.style.padding = '5px 20px';
    chartWrapper.appendChild(xAxis);
    
    // Add number labels
    displayNumbers.forEach(item => {
        if (!Array.isArray(item) || item.length < 2) return;
        
        const [number] = item;
        const label = document.createElement('div');
        label.style.fontSize = '12px';
        label.style.fontWeight = 'bold';
        label.style.textAlign = 'center';
        label.style.width = '18%';
        label.style.color = '#333';
        label.textContent = number;
        xAxis.appendChild(label);
    });
}

/**
 * Update hot and cold numbers display
 * @param {Object} data - Chart data from API
 */
function updateHotColdNumbers(data) {
    // Get best available data from the API response
    let selectedLotteryType = null;
    let maxFrequencyData = [];
    
    // Find the lottery type with the most data
    for (const lotteryType in data) {
        if (data[lotteryType] && 
            data[lotteryType].frequency && 
            data[lotteryType].frequency.length > maxFrequencyData.length) {
            maxFrequencyData = data[lotteryType].frequency;
            selectedLotteryType = lotteryType;
        }
    }
    
    // If no data, display empty message
    if (!selectedLotteryType) {
        document.getElementById('hotNumbersContainer').innerHTML = '<div class="text-muted">No hot numbers data available for the selected filters</div>';
        document.getElementById('coldNumbersContainer').innerHTML = '<div class="text-muted">No cold numbers data available for the selected filters</div>';
        document.getElementById('absentNumbersContainer').innerHTML = '<div class="text-muted">No absent numbers data available for the selected filters</div>';
        return;
    }
    
    // Get top numbers (hot numbers)
    const topNumbers = data[selectedLotteryType].top_numbers || [];
    
    // Update hot numbers display
    if (topNumbers.length > 0) {
        let hotNumbersHTML = '';
        for (let i = 0; i < Math.min(5, topNumbers.length); i++) {
            const [number, frequency] = topNumbers[i];
            const colorClass = ['lottery-ball-red', 'lottery-ball-yellow', 'lottery-ball-green', 'lottery-ball-blue', 'lottery-ball-red'][i % 5];
            
            hotNumbersHTML += `
                <div class="hot-number-item me-2 mb-2">
                    <span class="lottery-ball lottery-ball-sm ${colorClass}">
                        <span class="number">${number}</span>
                    </span>
                    <small class="frequency-label d-block text-center mt-1">${frequency}x</small>
                </div>
            `;
        }
        document.getElementById('hotNumbersContainer').innerHTML = hotNumbersHTML;
    } else {
        document.getElementById('hotNumbersContainer').innerHTML = '<div class="text-muted">No hot numbers data available</div>';
    }
    
    // Create cold numbers from frequency data
    const frequencyData = data[selectedLotteryType].frequency || [];
    if (frequencyData.length > 0) {
        // Create array of [number, frequency] pairs
        const numberFrequencies = [];
        for (let i = 0; i < frequencyData.length; i++) {
            if (frequencyData[i] > 0) { // Skip zeroes
                numberFrequencies.push({
                    number: i + 1,
                    frequency: frequencyData[i]
                });
            }
        }
        
        // Sort by frequency (ascending)
        const coldNumbers = numberFrequencies
            .sort((a, b) => a.frequency - b.frequency)
            .slice(0, 5)
            .map(item => [item.number, item.frequency]);
        
        // Update cold numbers display
        if (coldNumbers.length > 0) {
            let coldNumbersHTML = '';
            for (let i = 0; i < coldNumbers.length; i++) {
                const [number, frequency] = coldNumbers[i];
                coldNumbersHTML += `
                    <div class="cold-number-item me-2 mb-2">
                        <span class="lottery-ball lottery-ball-sm lottery-ball-blue">
                            <span class="number">${number}</span>
                        </span>
                        <small class="frequency-label d-block text-center mt-1">${frequency}x</small>
                    </div>
                `;
            }
            document.getElementById('coldNumbersContainer').innerHTML = coldNumbersHTML;
        } else {
            document.getElementById('coldNumbersContainer').innerHTML = '<div class="text-muted">No cold numbers data available</div>';
        }
    } else {
        document.getElementById('coldNumbersContainer').innerHTML = '<div class="text-muted">No cold numbers data available</div>';
    }
    
    // Update absent numbers (if available)
    const absentNumbers = data[selectedLotteryType].absent_numbers || 
                        data[selectedLotteryType].not_drawn_recently;
    
    if (absentNumbers && absentNumbers.length > 0) {
        let absentNumbersHTML = '';
        for (let i = 0; i < Math.min(5, absentNumbers.length); i++) {
            const [number, days] = absentNumbers[i];
            absentNumbersHTML += `
                <div class="absent-number-item me-2 mb-2">
                    <span class="lottery-ball lottery-ball-sm lottery-ball-green">
                        <span class="number">${number}</span>
                    </span>
                    <small class="frequency-label d-block text-center mt-1">${days} days</small>
                </div>
            `;
        }
        document.getElementById('absentNumbersContainer').innerHTML = absentNumbersHTML;
    } else {
        document.getElementById('absentNumbersContainer').innerHTML = '<div class="text-muted">No absent numbers data available</div>';
    }
}