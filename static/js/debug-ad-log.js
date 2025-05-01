/**
 * Debug Advertisement Logging Fix
 * 
 * This script prevents repeated logging and resolves the issue where
 * "AdManager: First ad complete, enabling view results button" message 
 * appears multiple times in the console.
 */
(function() {
    'use strict';
    
    console.log('Advertisement log debugger loaded');
    
    // Keep track of recent logs to avoid duplication
    let recentLogs = new Set();
    let consoleLogCalled = false;
    
    // Store original console methods
    const originalConsoleLog = console.log;
    
    // Create throttled version of console.log
    console.log = function() {
        // Convert arguments to string for comparison
        const logString = Array.from(arguments).join(' ');
        
        // Special handling for the problematic log message
        if (logString.includes('AdManager: First ad complete, enabling view results button')) {
            // Only log this message if we haven't seen it recently (in the last 2 seconds)
            if (!recentLogs.has('ad-enable-message')) {
                // Add to recent logs
                recentLogs.add('ad-enable-message');
                
                // Set a timeout to remove from recent logs
                setTimeout(() => {
                    recentLogs.delete('ad-enable-message');
                }, 2000);
                
                // Call original
                return originalConsoleLog.apply(console, arguments);
            }
        } else {
            // For all other log messages, use original behavior
            return originalConsoleLog.apply(console, arguments);
        }
    };
    
    // Initialize the original console.log tracking
    function initialize() {
        // Original initialized in anti-flicker.js
        const originalAntiFlickerInterval = window.setInterval;
        
        // Override setInterval to catch interval-based logging
        window.setInterval = function(callback, time, ...args) {
            // If this is a short interval (like checking for UI updates)
            if (time < 1000) {
                const wrappedCallback = function() {
                    // Store console.log state to detect if it's called
                    consoleLogCalled = false;
                    
                    // Run original callback
                    callback();
                };
                
                // Return modified interval
                return originalAntiFlickerInterval(wrappedCallback, time, ...args);
            }
            
            // Return standard interval for other cases
            return originalAntiFlickerInterval(callback, time, ...args);
        };
    }
    
    // Wait for page to load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();