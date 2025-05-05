/**
 * Process Monitoring System - Client-side component
 * 
 * This script monitors client-side performance metrics and user interactions
 * to help identify bottlenecks and debug performance issues.
 * 
 * Key features:
 * - Button click tracking
 * - Advertisement event monitoring
 * - File upload tracking
 * - API call timing
 * - Performance metrics collection
 * - Navigation and page load timing
 * 
 * All collected data is sent to the server for analysis and visualization
 */

window.ProcessMonitor = (function() {
    // Store monitoring data
    let monitoringData = {
        interactions: [],
        clicks: [],
        navigations: [],
        fileUploads: [],
        apiCalls: [],
        advertisements: [],
        resourceLoads: [],
        timers: [],
        errors: []
    };
    
    // Configuration
    const config = {
        enabled: true,
        trackClicks: true,
        trackNavigation: true,
        trackFileUploads: true,
        trackApiCalls: true,
        trackAdvertisements: true,
        trackResourceLoads: true,
        trackScriptExecutions: true,
        logToConsole: true,
        serverEndpoint: '/api/process-monitor/client-event',
        uploadInterval: 5000,  // 5 seconds
        flushBeforeUnload: true
    };
    
    // Periodic upload timer
    let uploadTimer = null;
    
    // Session ID to group related events
    const sessionId = Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    
    // Get current timestamp in ISO format
    function getTimestamp() {
        return new Date().toISOString();
    }
    
    // Format a duration in ms for display
    function formatDuration(ms) {
        if (ms < 1000) {
            return `${ms.toFixed(2)}ms`;
        } else {
            return `${(ms / 1000).toFixed(2)}s`;
        }
    }
    
    // Log an event to the monitoring system
    function logEvent(category, data) {
        const eventData = {
            ...data,
            timestamp: getTimestamp(),
            sessionId: sessionId,
            url: window.location.href,
            page: window.location.pathname
        };
        
        if (monitoringData[category]) {
            monitoringData[category].push(eventData);
        }
        
        if (config.logToConsole) {
            console.debug(`[ProcessMonitor] [${category}]`, eventData);
        }
        
        return eventData;
    }
    
    // Send accumulated data to the server
    function uploadData(forceSend = false) {
        // Don't send if no data or if module is disabled
        if (!config.enabled) return;
        
        // Count total events
        let totalEvents = 0;
        Object.keys(monitoringData).forEach(key => {
            totalEvents += monitoringData[key].length;
        });
        
        // Skip sending if no data and not forced
        if (totalEvents === 0 && !forceSend) return;
        
        // Prepare data for sending
        const payload = {
            sessionId: sessionId,
            timestamp: getTimestamp(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            data: {}
        };
        
        // Only include non-empty categories
        Object.keys(monitoringData).forEach(key => {
            if (monitoringData[key].length > 0) {
                payload.data[key] = [...monitoringData[key]];
                // Clear data after copying
                monitoringData[key] = [];
            }
        });
        
        // Send data to server
        try {
            fetch(config.serverEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-ProcessMonitor-Session': sessionId
                },
                body: JSON.stringify(payload),
                // Use keepalive for unload events
                keepalive: forceSend
            }).then(response => {
                if (!response.ok) {
                    console.warn(`[ProcessMonitor] Failed to upload data: ${response.status}`);
                }
            }).catch(error => {
                console.error(`[ProcessMonitor] Error uploading data: ${error}`);
            });
        } catch (e) {
            console.error(`[ProcessMonitor] Failed to send data: ${e}`);
        }
    }
    
    // Start periodic data uploads
    function startPeriodicUploads() {
        if (uploadTimer) clearInterval(uploadTimer);
        
        uploadTimer = setInterval(() => {
            uploadData();
        }, config.uploadInterval);
    }
    
    // Track button clicks
    function trackButtonClick(e) {
        if (!config.trackClicks) return;
        
        // Find the clicked element or closest button/link
        const target = e.target.closest('button, a, [role="button"], input[type="submit"], input[type="button"], .btn');
        if (!target) return;
        
        // Get element position and size
        const rect = target.getBoundingClientRect();
        
        // Extract useful attributes for identifying the element
        const id = target.id || '';
        const classes = target.className || '';
        const text = target.innerText || target.textContent || target.value || '';
        const href = target.href || '';
        
        // Special handling for ticket scanner buttons
        const isViewResultsButton = id === 'view-results-btn' || 
                                    text.includes('View Results') || 
                                    classes.includes('view-results');
        
        const isScanButton = id === 'scan-ticket-btn' || 
                             text.includes('Scan Ticket') || 
                             classes.includes('scan-ticket');
        
        // Create event data
        const data = {
            elementType: target.tagName.toLowerCase(),
            elementId: id,
            elementClass: classes,
            elementText: text,
            href: href,
            location: {
                x: e.clientX,
                y: e.clientY
            },
            elementRect: {
                top: rect.top,
                left: rect.left,
                width: rect.width,
                height: rect.height
            },
            isViewResultsButton: isViewResultsButton,
            isScanButton: isScanButton,
            specialHandling: isViewResultsButton || isScanButton
        };
        
        logEvent('clicks', data);
        
        // Additional tracking for specific buttons
        if (isViewResultsButton) {
            logEvent('interactions', {
                type: 'view_results_click',
                button: text,
                timestamp: Date.now()
            });
        } else if (isScanButton) {
            logEvent('interactions', {
                type: 'scan_ticket_click',
                button: text,
                timestamp: Date.now()
            });
        }
    }
    
    // Track page navigation
    function trackNavigation() {
        if (!config.trackNavigation) return;
        
        // Collect performance timing data
        let timingData = {};
        
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            
            timingData = {
                navigationStart: timing.navigationStart,
                redirectTime: timing.redirectEnd - timing.redirectStart,
                dnsTime: timing.domainLookupEnd - timing.domainLookupStart,
                connectTime: timing.connectEnd - timing.connectStart,
                requestTime: timing.responseStart - timing.requestStart,
                responseTime: timing.responseEnd - timing.responseStart,
                domProcessingTime: timing.domComplete - timing.domLoading,
                domContentLoadedTime: timing.domContentLoadedEventEnd - timing.navigationStart,
                loadTime: timing.loadEventEnd - timing.navigationStart
            };
        }
        
        const data = {
            from: document.referrer || 'direct',
            to: window.location.href,
            title: document.title,
            timing: timingData,
            timestamp: Date.now()
        };
        
        logEvent('navigations', data);
    }
    
    // Track file uploads
    function trackFileUpload() {
        if (!config.trackFileUploads) return;
        
        // Find all file inputs and attach listeners
        document.querySelectorAll('input[type="file"]').forEach(input => {
            // Skip if already tracked
            if (input.dataset.monitored) return;
            
            // Mark as tracked
            input.dataset.monitored = 'true';
            
            // Add change event listener
            input.addEventListener('change', function(e) {
                if (!this.files || !this.files.length) return;
                
                // Collect info for each selected file
                const files = Array.from(this.files).map(file => ({
                    name: file.name,
                    type: file.type,
                    size: file.size,
                    lastModified: new Date(file.lastModified).toISOString()
                }));
                
                // Get form information
                const form = this.closest('form');
                const formId = form ? form.id || '' : '';
                const formAction = form ? form.action || '' : '';
                
                // Log the file selection event
                const data = {
                    elementId: this.id || '',
                    elementName: this.name || '',
                    formId: formId,
                    formAction: formAction,
                    files: files,
                    isTicketUpload: this.id === 'ticket-image' || this.name === 'ticket_image',
                    timestamp: Date.now()
                };
                
                logEvent('fileUploads', data);
                
                // Special handling for ticket image uploads
                if (data.isTicketUpload) {
                    logEvent('interactions', {
                        type: 'ticket_image_selected',
                        fileCount: files.length,
                        fileTypes: files.map(f => f.type),
                        fileSizes: files.map(f => f.size),
                        timestamp: Date.now()
                    });
                }
            });
        });
    }
    
    // Override fetch and XMLHttpRequest to track API calls
    function trackApiCalls() {
        if (!config.trackApiCalls) return;
        
        // Store original methods before overriding
        const originalFetch = window.fetch;
        const originalXhrOpen = XMLHttpRequest.prototype.open;
        const originalXhrSend = XMLHttpRequest.prototype.send;
        
        // Override fetch API
        window.fetch = function() {
            const startTime = Date.now();
            let method = 'GET';
            let url = arguments[0];
            let requestSize = 0;
            
            // Extract URL from Request object
            if (typeof url === 'object' && url instanceof Request) {
                method = url.method;
                url = url.url;
            }
            
            // Extract method from options
            if (arguments[1] && arguments[1].method) {
                method = arguments[1].method;
            }
            
            // Track request body size
            if (arguments[1] && arguments[1].body) {
                if (typeof arguments[1].body === 'string') {
                    requestSize = arguments[1].body.length;
                } else if (arguments[1].body instanceof FormData) {
                    // FormData size is approximate
                    requestSize = -1;
                } else if (arguments[1].body instanceof Blob) {
                    requestSize = arguments[1].body.size;
                }
            }
            
            // Check if this is a process monitor payload to avoid infinite loops
            if (url.includes('/api/process-monitor/') || url.includes('process-monitor-ping')) {
                return originalFetch.apply(this, arguments);
            }
            
            // Log the API call start
            const requestId = Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            
            logEvent('apiCalls', {
                id: requestId,
                method: method,
                url: url,
                phase: 'start',
                startTime: startTime,
                requestSize: requestSize
            });
            
            // Make the actual fetch call
            return originalFetch.apply(this, arguments)
                .then(response => {
                    const endTime = Date.now();
                    const duration = endTime - startTime;
                    
                    // Clone the response to read its size
                    const responseClone = response.clone();
                    
                    // Process the response
                    responseClone.text().then(text => {
                        logEvent('apiCalls', {
                            id: requestId,
                            method: method,
                            url: url,
                            phase: 'complete',
                            status: response.status,
                            contentType: response.headers.get('Content-Type'),
                            endTime: endTime,
                            duration: duration,
                            responseSize: text.length,
                            isTicketScan: url.includes('/scan-ticket')
                        });
                        
                        // Special handling for ticket scan responses
                        if (url.includes('/scan-ticket')) {
                            try {
                                const data = JSON.parse(text);
                                logEvent('interactions', {
                                    type: 'ticket_scan_response',
                                    status: response.status,
                                    hasError: !!data.error,
                                    lottery_type: data.lottery_type || 'unknown',
                                    draw_number: data.draw_number || 'unknown',
                                    timestamp: endTime
                                });
                            } catch (e) {
                                // Ignore parsing errors
                            }
                        }
                    }).catch(err => {
                        // Log errors but don't reject the promise
                        console.warn('[ProcessMonitor] Error reading response:', err);
                    });
                    
                    return response;
                })
                .catch(error => {
                    const endTime = Date.now();
                    const duration = endTime - startTime;
                    
                    logEvent('apiCalls', {
                        id: requestId,
                        method: method,
                        url: url,
                        phase: 'error',
                        endTime: endTime,
                        duration: duration,
                        error: error.message
                    });
                    
                    if (url.includes('/scan-ticket')) {
                        logEvent('interactions', {
                            type: 'ticket_scan_error',
                            error: error.message,
                            timestamp: endTime
                        });
                    }
                    
                    throw error;
                });
        };
        
        // Override XMLHttpRequest.open
        XMLHttpRequest.prototype.open = function(method, url) {
            this._monitorData = {
                method: method,
                url: url,
                startTime: Date.now(),
                requestId: Date.now() + '-' + Math.random().toString(36).substr(2, 9)
            };
            
            // Check if this is a process monitor call
            if (url.includes('/api/process-monitor/') || url.includes('process-monitor-ping')) {
                this._skipMonitoring = true;
            } else {
                logEvent('apiCalls', {
                    id: this._monitorData.requestId,
                    method: method,
                    url: url,
                    phase: 'start',
                    startTime: this._monitorData.startTime
                });
            }
            
            return originalXhrOpen.apply(this, arguments);
        };
        
        // Override XMLHttpRequest.send
        XMLHttpRequest.prototype.send = function(data) {
            if (this._monitorData && !this._skipMonitoring) {
                // Track request size
                let requestSize = 0;
                if (data) {
                    if (typeof data === 'string') {
                        requestSize = data.length;
                    } else if (data instanceof FormData) {
                        requestSize = -1;  // Can't accurately determine FormData size
                    } else if (data instanceof Blob) {
                        requestSize = data.size;
                    }
                }
                
                this._monitorData.requestSize = requestSize;
                
                // Set up response handler
                const xhr = this;
                const originalOnReadyStateChange = xhr.onreadystatechange;
                
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        const endTime = Date.now();
                        const duration = endTime - xhr._monitorData.startTime;
                        
                        logEvent('apiCalls', {
                            id: xhr._monitorData.requestId,
                            method: xhr._monitorData.method,
                            url: xhr._monitorData.url,
                            phase: 'complete',
                            status: xhr.status,
                            contentType: xhr.getResponseHeader('Content-Type'),
                            endTime: endTime,
                            duration: duration,
                            responseSize: xhr.responseText ? xhr.responseText.length : 0,
                            isTicketScan: xhr._monitorData.url.includes('/scan-ticket')
                        });
                        
                        // Special handling for ticket scan responses
                        if (xhr._monitorData.url.includes('/scan-ticket') && xhr.responseText) {
                            try {
                                const data = JSON.parse(xhr.responseText);
                                logEvent('interactions', {
                                    type: 'ticket_scan_response',
                                    status: xhr.status,
                                    hasError: !!data.error,
                                    lottery_type: data.lottery_type || 'unknown',
                                    draw_number: data.draw_number || 'unknown',
                                    timestamp: endTime
                                });
                            } catch (e) {
                                // Ignore parsing errors
                            }
                        }
                    }
                    
                    if (originalOnReadyStateChange) {
                        originalOnReadyStateChange.apply(this, arguments);
                    }
                };
            }
            
            return originalXhrSend.apply(this, arguments);
        };
    }
    
    // Monitor advertisement events in dual-ad-manager.js
    function monitorAdvertisements() {
        if (!config.trackAdvertisements) return;
        
        // Ensure we don't try to patch before the object exists
        function waitForAdManagerAndPatch() {
            // Look for global ad manager or via the window object
            const adManager = window.DualAdManager || window.dualAdManager;
            
            if (adManager) {
                // Only patch if not already patched
                if (!adManager._monitored) {
                    patchAdManager(adManager);
                }
            } else {
                // Wait and try again
                setTimeout(waitForAdManagerAndPatch, 500);
            }
        }
        
        function patchAdManager(adManager) {
            console.log('[ProcessMonitor] Patching advertisement manager...');
            
            // Mark as monitored to prevent double patching
            adManager._monitored = true;
            
            // Functions to monitor
            const functionsToPatch = [
                'showPublicServiceAd',
                'startPublicServiceCountdown',
                'completePublicServiceAd',
                'showMonetizationAd',
                'startMonetizationCountdown',
                'completeMonetizationAd',
                'hideAllAds',
                'handleViewResultsClick',
                'showResultsWithAd',
                'processTicketWithAds'
            ];
            
            // Patch each function
            functionsToPatch.forEach(funcName => {
                if (typeof adManager[funcName] === 'function') {
                    const originalFunc = adManager[funcName];
                    
                    adManager[funcName] = function() {
                        const startTime = Date.now();
                        const eventId = startTime + '-' + Math.random().toString(36).substr(2, 9);
                        
                        logEvent('advertisements', {
                            id: eventId,
                            function: funcName,
                            phase: 'start',
                            arguments: Array.from(arguments).map(arg => {
                                // Safely stringify arguments
                                if (typeof arg === 'function') return 'function';
                                if (arg === null) return null;
                                if (arg === undefined) return undefined;
                                if (typeof arg === 'object') {
                                    try {
                                        return JSON.stringify(arg);
                                    } catch (e) {
                                        return '[Object]';
                                    }
                                }
                                return arg;
                            }),
                            startTime: startTime
                        });
                        
                        try {
                            const result = originalFunc.apply(this, arguments);
                            
                            logEvent('advertisements', {
                                id: eventId,
                                function: funcName,
                                phase: 'complete',
                                duration: Date.now() - startTime,
                                endTime: Date.now()
                            });
                            
                            return result;
                        } catch (e) {
                            logEvent('advertisements', {
                                id: eventId,
                                function: funcName,
                                phase: 'error',
                                error: e.message,
                                stack: e.stack,
                                duration: Date.now() - startTime,
                                endTime: Date.now()
                            });
                            
                            throw e;
                        }
                    };
                }
            });
            
            console.log('[ProcessMonitor] Advertisement manager successfully patched');
        }
        
        // Start the monitoring
        waitForAdManagerAndPatch();
        
        // Also monitor the DOM for advertisement elements
        const adSelectors = [
            '#public-service-ad-overlay',
            '#monetization-ad-overlay',
            '.ad-overlay',
            '#first-countdown-container',
            '#second-countdown-container',
            '#view-results-button'
        ];
        
        // Create a MutationObserver to watch for ad elements
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) {  // Element node
                            // Check if any of our ad selectors match
                            adSelectors.forEach(selector => {
                                if (node.matches?.(selector) || node.querySelector?.(selector)) {
                                    logEvent('advertisements', {
                                        type: 'dom_change',
                                        selector: selector,
                                        action: 'added',
                                        timestamp: Date.now()
                                    });
                                }
                            });
                        }
                    });
                    
                    mutation.removedNodes.forEach(node => {
                        if (node.nodeType === 1) {  // Element node
                            // Check if any of our ad selectors match
                            adSelectors.forEach(selector => {
                                if (node.matches?.(selector) || node.querySelector?.(selector)) {
                                    logEvent('advertisements', {
                                        type: 'dom_change',
                                        selector: selector,
                                        action: 'removed',
                                        timestamp: Date.now()
                                    });
                                }
                            });
                        }
                    });
                } else if (mutation.type === 'attributes') {
                    // Check for style/visibility changes on ad elements
                    if (adSelectors.some(selector => mutation.target.matches?.(selector))) {
                        const target = mutation.target;
                        
                        if (mutation.attributeName === 'style') {
                            const display = target.style.display;
                            const visibility = target.style.visibility;
                            const opacity = target.style.opacity;
                            
                            logEvent('advertisements', {
                                type: 'style_change',
                                element: target.id || target.className,
                                display: display,
                                visibility: visibility,
                                opacity: opacity,
                                timestamp: Date.now()
                            });
                        } else if (mutation.attributeName === 'class') {
                            logEvent('advertisements', {
                                type: 'class_change',
                                element: target.id || target.className,
                                className: target.className,
                                timestamp: Date.now()
                            });
                        }
                    }
                }
            });
        });
        
        // Start observing the document body
        observer.observe(document.body, {
            childList: true,
            attributes: true,
            subtree: true,
            attributeFilter: ['style', 'class']
        });
    }
    
    // Monitor performance and resource usage
    function monitorPerformance() {
        // Create a metric collection function
        function collectMetrics() {
            const metrics = {
                timestamp: Date.now(),
                memory: window.performance?.memory ? {
                    usedJSHeapSize: window.performance.memory.usedJSHeapSize,
                    totalJSHeapSize: window.performance.memory.totalJSHeapSize,
                    jsHeapSizeLimit: window.performance.memory.jsHeapSizeLimit
                } : null,
                timing: window.performance?.timing ? {
                    navigationStart: window.performance.timing.navigationStart,
                    loadEventEnd: window.performance.timing.loadEventEnd,
                    domComplete: window.performance.timing.domComplete
                } : null
            };
            
            logEvent('resourceLoads', metrics);
        }
        
        // Collect initial metrics after page load
        window.addEventListener('load', () => {
            setTimeout(collectMetrics, 1000);
        });
        
        // Schedule periodic collection
        setInterval(collectMetrics, 10000);  // Every 10 seconds
    }
    
    // Set up error tracking
    function monitorErrors() {
        // Catch unhandled exceptions
        window.addEventListener('error', event => {
            logEvent('errors', {
                type: 'error',
                message: event.message,
                source: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error ? (event.error.stack || event.error.toString()) : null,
                timestamp: Date.now()
            });
        });
        
        // Catch unhandled promise rejections
        window.addEventListener('unhandledrejection', event => {
            logEvent('errors', {
                type: 'unhandledrejection',
                reason: event.reason ? event.reason.toString() : 'Unknown',
                stack: event.reason && event.reason.stack ? event.reason.stack : null,
                timestamp: Date.now()
            });
        });
    }
    
    // Track script execution time using Performance API
    function monitorScriptExecutions() {
        if (!config.trackScriptExecutions || !window.performance || !window.performance.getEntriesByType) {
            return;
        }
        
        // Track initial script executions
        window.addEventListener('load', () => {
            const resourceEntries = window.performance.getEntriesByType('resource');
            
            // Find script resources
            const scriptResources = resourceEntries.filter(entry => {
                return entry.initiatorType === 'script' || 
                       (entry.name && entry.name.endsWith('.js'));
            });
            
            // Log the script load times
            scriptResources.forEach(entry => {
                if (entry.duration > 100) {  // Only log scripts that took more than 100ms
                    logEvent('resourceLoads', {
                        type: 'script_load',
                        name: entry.name,
                        duration: entry.duration,
                        size: entry.encodedBodySize || entry.transferSize || 0,
                        startTime: entry.startTime,
                        timestamp: Date.now()
                    });
                }
            });
        });
    }
    
    // Initialize the monitoring system
    function init(customConfig = {}) {
        // Apply custom configuration
        Object.assign(config, customConfig);
        
        if (!config.enabled) return;
        
        // Set up the event handlers
        if (config.trackClicks) {
            document.addEventListener('click', trackButtonClick, { capture: true });
        }
        
        if (config.trackNavigation) {
            // Track initial navigation
            trackNavigation();
            
            // Track future navigation events
            window.addEventListener('popstate', trackNavigation);
        }
        
        if (config.trackFileUploads) {
            // Initial setup
            trackFileUpload();
            
            // Setup MutationObserver to detect dynamically added file inputs
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    if (mutation.type === 'childList') {
                        // Check if any new file inputs were added
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === 1) {  // Element node
                                // Check the node itself
                                if (node.tagName === 'INPUT' && node.type === 'file') {
                                    trackFileUpload();
                                }
                                
                                // Check children
                                const fileInputs = node.querySelectorAll('input[type="file"]');
                                if (fileInputs.length > 0) {
                                    trackFileUpload();
                                }
                            }
                        });
                    }
                });
            });
            
            // Start observing document for added file inputs
            observer.observe(document.documentElement, {
                childList: true,
                subtree: true
            });
        }
        
        if (config.trackApiCalls) {
            trackApiCalls();
        }
        
        if (config.trackAdvertisements) {
            monitorAdvertisements();
        }
        
        if (config.trackResourceLoads) {
            monitorPerformance();
        }
        
        if (config.trackScriptExecutions) {
            monitorScriptExecutions();
        }
        
        // Monitor for errors
        monitorErrors();
        
        // Start periodic uploads
        startPeriodicUploads();
        
        // Initialize beforeunload handler
        if (config.flushBeforeUnload) {
            window.addEventListener('beforeunload', () => {
                uploadData(true);
            });
        }
        
        // Log initialization
        console.log('[ProcessMonitor] Initialized with session ID:', sessionId);
        
        // Create a special timer for ticket scanner
        if (window.location.pathname.includes('ticket-scanner') || 
            document.getElementById('ticket-form')) {
            console.log('[ProcessMonitor] Ticket Scanner page detected, activating specialized monitoring');
            
            // Add special monitoring for ticket scanner form
            const form = document.getElementById('ticket-form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    logEvent('interactions', {
                        type: 'ticket_form_submit',
                        timestamp: Date.now()
                    });
                });
            }
            
            // Monitor View Results button
            const viewResultsBtn = document.getElementById('view-results-btn') || 
                                 document.querySelector('.view-results-btn');
            if (viewResultsBtn) {
                viewResultsBtn.addEventListener('click', function(e) {
                    logEvent('interactions', {
                        type: 'view_results_button_click',
                        disabled: this.disabled,
                        classes: this.className,
                        timestamp: Date.now()
                    });
                });
            }
        }
    }
    
    // Debug helper to view the current monitoring data
    function debug() {
        console.group('[ProcessMonitor] Current Monitoring Data');
        
        Object.keys(monitoringData).forEach(category => {
            console.group(`${category} (${monitoringData[category].length} events)`);
            if (monitoringData[category].length > 0) {
                console.table(monitoringData[category]);
            }
            console.groupEnd();
        });
        
        console.groupEnd();
    }
    
    // Public API
    return {
        init: init,
        logEvent: logEvent,
        trackEvent: function(category, data) {
            return logEvent(category, data);
        },
        uploadData: uploadData,
        debug: debug,
        getSessionId: function() {
            return sessionId;
        },
        getMonitoringData: function() {
            return monitoringData;
        },
        clearData: function() {
            Object.keys(monitoringData).forEach(key => {
                monitoringData[key] = [];
            });
        }
    };
})();

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize with default config
    window.ProcessMonitor.init();
    
    // Log the page load event
    window.ProcessMonitor.logEvent('interactions', {
        type: 'page_loaded',
        url: window.location.href,
        title: document.title,
        timestamp: Date.now()
    });
});