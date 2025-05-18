/**
 * Chart Support for Snap Lottery
 * This file provides utility functions and fixes for integrating Chart.js with our application
 */

// Create a script element to add Chart.js if it's not already loaded
if (typeof Chart === 'undefined') {
  console.log("Loading Chart.js library dynamically");
  const chartScript = document.createElement('script');
  chartScript.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
  chartScript.onload = function() {
    console.log("Chart.js loaded successfully");
    initializeCharts();
  };
  document.head.appendChild(chartScript);
} else {
  console.log("Chart.js already loaded");
  initializeCharts();
}

// Initialize any charts on the page once Chart.js is available
function initializeCharts() {
  // Trigger the chart loader if it exists
  if (typeof fetchChartData === 'function') {
    console.log("Triggering chart data fetch");
    fetchChartData('all', 'all');
  }
}

// Helper function to process frequency data from API
function processFrequencyData(data) {
  // If data is not in the right structure, transform it
  if (!data || !data.data) {
    return {
      frequencyData: {},
      divisionData: {},
      lotteryTypes: data?.lottery_types || [],
      stats: data?.summary || {}
    };
  }
  
  return {
    frequencyData: data.data,
    divisionData: {}, // Not all APIs return division data
    lotteryTypes: data.lottery_types || [],
    stats: data.summary || {}
  };
}

// Override the original renderCharts function to handle data format issues
const originalRenderCharts = window.renderCharts;
window.renderCharts = function(data) {
  console.log("Processing chart data with format fix");
  
  // Process the data to ensure correct format
  const processedData = processFrequencyData(data);
  
  // Call the original function if it exists
  if (typeof originalRenderCharts === 'function') {
    originalRenderCharts(processedData);
  } else {
    console.log("Updating frequency chart");
    
    // Use the chart-renderer functions directly
    if (typeof renderFrequencyChart === 'function') {
      renderFrequencyChart(processedData.frequencyData);
    } else {
      console.warn("No frequency data to render");
    }
    
    if (typeof renderDivisionChart === 'function') {
      renderDivisionChart(processedData.divisionData);
    } else {
      console.warn("No division data to render");
    }
    
    if (typeof renderLotteryTypeSelector === 'function') {
      renderLotteryTypeSelector(processedData.lotteryTypes);
    } else {
      console.warn("No lottery types data available");
    }
    
    if (typeof updateStatsSummary === 'function') {
      updateStatsSummary(processedData.stats);
    } else {
      console.warn("No stats data available");
    }
  }
};