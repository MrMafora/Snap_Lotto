/**
 * Process Monitoring (Client Side)
 * 
 * This module handles client-side process monitoring to track user interactions,
 * performance metrics, and errors that occur in the browser.
 */

(function() {
    'use strict';

    // Configuration
    const DEFAULT_CONFIG = {
        enabled: true,
        sessionId: null,
        serverEndpoint: '/api/process-monitor/client-event',
        autoTrackErrors: true,
        autoTrackPerformance: true,
        autoTrackInteractions: true,
        samplingRate: 1.0  // 1.0 = track everything, 0.5 = track 50%, etc.
    };

    // State
    let config = { ...DEFAULT_CONFIG };
    let initialized = false;
    let performanceMetrics = {
        navigationStart: performance.now(),
        domComplete: null,
        resourcesComplete: null,
        firstPaint: null,
        firstContentfulPaint: null
    };

    /**
     * Initialize the monitoring system with configuration
     * @param {Object} userConfig - Configuration options
     */
    function init(userConfig = {}) {
        // Merge provided config with defaults
        config = { ...DEFAULT_CONFIG, ...userConfig };

        // Generate session ID if not provided
        if (!config.sessionId) {
            config.sessionId = generateSessionId();
        }

        console.log('[ProcessMonitor] Initializing with session ID:', config.sessionId);

        // Set up automatic tracking if enabled
        if (config.enabled) {
            if (config.autoTrackErrors) {
                setupErrorTracking();
            }
            
            if (config.autoTrackPerformance) {
                trackPerformanceMetrics();
            }
            
            if (config.autoTrackInteractions) {
                trackUserInteractions();
            }
        }

        // Mark as initialized
        initialized = true;
        
        // Send initialization event
        trackEvent('init', {
            userAgent: navigator.userAgent,
            screenSize: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            url: window.location.href,
            referrer: document.referrer
        });
        
        return true;
    }

    /**
     * Generate a unique session ID
     * @returns {string} A UUID v4 string
     */
    function generateSessionId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Set up global error tracking
     */
    function setupErrorTracking() {
        // Track unhandled errors
        window.addEventListener('error', function(event) {
            trackEvent('error', {
                message: event.message,
                filename: event.filename,
                lineNumber: event.lineno,
                columnNumber: event.colno,
                stack: event.error ? event.error.stack : null
            });
        });

        // Track unhandled promise rejections
        window.addEventListener('unhandledrejection', function(event) {
            trackEvent('unhandledRejection', {
                reason: String(event.reason),
                stack: event.reason && event.reason.stack ? event.reason.stack : null
            });
        });
        
        // Track AJAX errors by wrapping XMLHttpRequest
        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url) {
            this._monitorMethod = method;
            this._monitorUrl = url;
            return originalXHROpen.apply(this, arguments);
        };
        
        XMLHttpRequest.prototype.send = function() {
            const xhr = this;
            const startTime = performance.now();
            
            xhr.addEventListener('load', function() {
                if (xhr.status >= 400) {
                    trackEvent('xhrError', {
                        method: xhr._monitorMethod,
                        url: xhr._monitorUrl,
                        status: xhr.status,
                        statusText: xhr.statusText,
                        duration: performance.now() - startTime
                    });
                } else {
                    trackEvent('xhrSuccess', {
                        method: xhr._monitorMethod,
                        url: xhr._monitorUrl,
                        status: xhr.status,
                        duration: performance.now() - startTime
                    });
                }
            });
            
            xhr.addEventListener('error', function() {
                trackEvent('xhrError', {
                    method: xhr._monitorMethod,
                    url: xhr._monitorUrl,
                    status: 'network_error',
                    duration: performance.now() - startTime
                });
            });
            
            xhr.addEventListener('timeout', function() {
                trackEvent('xhrTimeout', {
                    method: xhr._monitorMethod,
                    url: xhr._monitorUrl,
                    duration: performance.now() - startTime
                });
            });
            
            return originalXHRSend.apply(this, arguments);
        };
        
        // Track Fetch errors by wrapping fetch
        const originalFetch = window.fetch;
        if (originalFetch) {
            window.fetch = function(input, init) {
                const startTime = performance.now();
                const url = typeof input === 'string' ? input : input.url;
                const method = init && init.method ? init.method : 'GET';
                
                return originalFetch.apply(this, arguments)
                    .then(function(response) {
                        const duration = performance.now() - startTime;
                        
                        if (!response.ok) {
                            trackEvent('fetchError', {
                                method: method,
                                url: url,
                                status: response.status,
                                statusText: response.statusText,
                                duration: duration
                            });
                        } else {
                            trackEvent('fetchSuccess', {
                                method: method,
                                url: url,
                                status: response.status,
                                duration: duration
                            });
                        }
                        
                        return response;
                    })
                    .catch(function(error) {
                        trackEvent('fetchError', {
                            method: method,
                            url: url,
                            status: 'network_error',
                            message: String(error),
                            duration: performance.now() - startTime
                        });
                        
                        throw error;
                    });
            };
        }
    }

    /**
     * Track performance metrics for the page
     */
    function trackPerformanceMetrics() {
        // Track when DOM is fully loaded
        window.addEventListener('DOMContentLoaded', function() {
            performanceMetrics.domComplete = performance.now();
            trackEvent('domComplete', {
                duration: performanceMetrics.domComplete - performanceMetrics.navigationStart
            });
        });

        // Track when page is fully loaded including all resources
        window.addEventListener('load', function() {
            performanceMetrics.resourcesComplete = performance.now();
            
            // Get resource timing data
            if (window.performance && window.performance.getEntriesByType) {
                const resources = window.performance.getEntriesByType('resource');
                
                trackEvent('resourcesComplete', {
                    duration: performanceMetrics.resourcesComplete - performanceMetrics.navigationStart,
                    resourceCount: resources.length,
                    resourceStats: calculateResourceStats(resources)
                });
            } else {
                trackEvent('resourcesComplete', {
                    duration: performanceMetrics.resourcesComplete - performanceMetrics.navigationStart
                });
            }
        });

        // Track first paint and first contentful paint
        if (window.PerformanceObserver) {
            try {
                const paintObserver = new PerformanceObserver((entryList) => {
                    for (const entry of entryList.getEntries()) {
                        if (entry.name === 'first-paint') {
                            performanceMetrics.firstPaint = entry.startTime;
                            trackEvent('firstPaint', {
                                duration: entry.startTime
                            });
                        }
                        if (entry.name === 'first-contentful-paint') {
                            performanceMetrics.firstContentfulPaint = entry.startTime;
                            trackEvent('firstContentfulPaint', {
                                duration: entry.startTime
                            });
                        }
                    }
                });
                
                paintObserver.observe({ entryTypes: ['paint'] });
            } catch (e) {
                console.error('[ProcessMonitor] Error setting up paint observer:', e);
            }
        }
        
        // Track long tasks
        if (window.PerformanceObserver) {
            try {
                const longTaskObserver = new PerformanceObserver((entryList) => {
                    for (const entry of entryList.getEntries()) {
                        trackEvent('longTask', {
                            duration: entry.duration,
                            startTime: entry.startTime,
                            name: entry.name
                        });
                    }
                });
                
                longTaskObserver.observe({ entryTypes: ['longtask'] });
            } catch (e) {
                // Long tasks might not be supported in all browsers
                console.warn('[ProcessMonitor] Long task observation not supported:', e);
            }
        }
    }
    
    /**
     * Calculate statistics for resource timing data
     * @param {Array} resources - Array of resource timing entries
     * @returns {Object} Statistics about resource loading
     */
    function calculateResourceStats(resources) {
        if (!resources || !resources.length) {
            return {};
        }
        
        const byType = {};
        let totalSize = 0;
        let totalDuration = 0;
        
        // Group resources by type
        resources.forEach(resource => {
            const type = getResourceType(resource.name);
            
            if (!byType[type]) {
                byType[type] = {
                    count: 0,
                    size: 0,
                    totalDuration: 0
                };
            }
            
            byType[type].count++;
            
            // Try to get transfer size if available
            if (resource.transferSize) {
                byType[type].size += resource.transferSize;
                totalSize += resource.transferSize;
            }
            
            // Calculate duration
            const duration = resource.responseEnd - resource.startTime;
            byType[type].totalDuration += duration;
            totalDuration += duration;
        });
        
        // Calculate average duration for each type
        Object.keys(byType).forEach(type => {
            byType[type].avgDuration = byType[type].totalDuration / byType[type].count;
        });
        
        return {
            byType: byType,
            totalSize: totalSize,
            totalDuration: totalDuration,
            resourceCount: resources.length
        };
    }
    
    /**
     * Get the resource type based on file extension or URL pattern
     * @param {string} url - The resource URL
     * @returns {string} The type of resource
     */
    function getResourceType(url) {
        // Images
        if (/\.(jpe?g|png|gif|svg|webp|ico)(\?.*)?$/.test(url)) {
            return 'image';
        }
        
        // Scripts
        if (/\.(js)(\?.*)?$/.test(url)) {
            return 'script';
        }
        
        // Styles
        if (/\.(css)(\?.*)?$/.test(url)) {
            return 'style';
        }
        
        // Fonts
        if (/\.(woff2?|ttf|otf|eot)(\?.*)?$/.test(url)) {
            return 'font';
        }
        
        // HTML
        if (/\.(html?|php)(\?.*)?$/.test(url) || url.indexOf('?') > -1) {
            return 'html';
        }
        
        // API calls
        if (/\/(api|graphql)\//.test(url)) {
            return 'api';
        }
        
        // Default
        return 'other';
    }

    /**
     * Track user interactions
     */
    function trackUserInteractions() {
        // Track clicks
        document.addEventListener('click', function(event) {
            const target = event.target;
            
            // Get information about the clicked element
            const elementInfo = {
                tag: target.tagName.toLowerCase(),
                id: target.id || null,
                classes: target.className ? target.className.split(' ').filter(Boolean) : [],
                text: target.innerText ? target.innerText.slice(0, 100) : null
            };
            
            // Special handling for links
            if (target.tagName === 'A' || target.closest('a')) {
                const link = target.tagName === 'A' ? target : target.closest('a');
                elementInfo.href = link.href;
                elementInfo.target = link.target;
            }
            
            // Special handling for buttons
            if (target.tagName === 'BUTTON' || target.closest('button')) {
                const button = target.tagName === 'BUTTON' ? target : target.closest('button');
                elementInfo.type = button.type || 'button';
            }
            
            // Special handling for forms
            if (target.tagName === 'FORM' || target.closest('form')) {
                const form = target.tagName === 'FORM' ? target : target.closest('form');
                elementInfo.formAction = form.action;
                elementInfo.formMethod = form.method;
            }
            
            trackEvent('click', {
                x: event.clientX,
                y: event.clientY,
                element: elementInfo,
                path: getEventPath(event).map(el => ({
                    tag: el.tagName ? el.tagName.toLowerCase() : null,
                    id: el.id || null,
                    classes: el.className ? el.className.split(' ').filter(Boolean) : []
                })).slice(0, 5)  // Limit to 5 ancestors for brevity
            });
        });
        
        // Track form submissions
        document.addEventListener('submit', function(event) {
            const form = event.target;
            
            trackEvent('formSubmit', {
                formId: form.id || null,
                formAction: form.action,
                formMethod: form.method,
                formElements: Array.from(form.elements).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    type: el.type || null,
                    id: el.id || null,
                    name: el.name || null,
                    hasValue: !!el.value
                }))
            });
        });
        
        // Track page visibility changes
        document.addEventListener('visibilitychange', function() {
            trackEvent('visibilityChange', {
                state: document.visibilityState
            });
        });
        
        // Track page unload
        window.addEventListener('beforeunload', function() {
            trackEvent('pageUnload', {
                timeOnPage: performance.now() - performanceMetrics.navigationStart
            });
        });
        
        // Track page scroll
        let lastScrollEvent = 0;
        window.addEventListener('scroll', function() {
            // Throttle scroll events to avoid too many events
            const now = Date.now();
            if (now - lastScrollEvent < 1000) {  // Only track every second
                return;
            }
            
            lastScrollEvent = now;
            
            trackEvent('scroll', {
                scrollX: window.scrollX,
                scrollY: window.scrollY,
                scrollHeight: document.documentElement.scrollHeight,
                scrollWidth: document.documentElement.scrollWidth,
                viewportHeight: window.innerHeight,
                viewportWidth: window.innerWidth,
                percentScrolled: (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100
            });
        });
    }
    
    /**
     * Get the event path (for browsers that don't support event.path)
     * @param {Event} event - The DOM event
     * @returns {Array} An array of elements in the event path
     */
    function getEventPath(event) {
        if (event.path) {
            return event.path;
        }
        
        if (event.composedPath) {
            return event.composedPath();
        }
        
        // Fallback for browsers that don't support either
        let target = event.target;
        const path = [target];
        
        while (target.parentElement) {
            target = target.parentElement;
            path.push(target);
        }
        
        if (path[path.length - 1] !== document) {
            path.push(document);
        }
        
        if (path[path.length - 1] !== window) {
            path.push(window);
        }
        
        return path;
    }

    /**
     * Track a custom event
     * @param {string} type - The type of event
     * @param {Object} details - Details about the event
     */
    function trackEvent(type, details = {}) {
        if (!config.enabled) {
            return;
        }
        
        // Apply sampling rate
        if (config.samplingRate < 1.0 && Math.random() > config.samplingRate) {
            return;
        }
        
        // Create the event data
        const eventData = {
            type: type,
            timestamp: new Date().toISOString(),
            sessionId: config.sessionId,
            url: window.location.href,
            details: details
        };
        
        // Send the event to the server
        sendEventToServer(eventData);
        
        // Also log to console in development
        if (isDevelopment()) {
            console.debug('[ProcessMonitor] Tracked event:', type, details);
        }
    }

    /**
     * Send an event to the server
     * @param {Object} eventData - The event data to send
     */
    function sendEventToServer(eventData) {
        // Skip if no endpoint configured
        if (!config.serverEndpoint) {
            return;
        }
        
        // Use beacon API if available (works better for unload events)
        if (navigator.sendBeacon && (eventData.type === 'pageUnload' || eventData.type === 'visibilityChange')) {
            try {
                navigator.sendBeacon(
                    config.serverEndpoint,
                    JSON.stringify(eventData)
                );
                return;
            } catch (e) {
                console.error('[ProcessMonitor] Error sending beacon:', e);
                // Fall back to fetch
            }
        }
        
        // Use fetch for other events
        fetch(config.serverEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData),
            // Keep-alive to ensure events get sent even on page unload
            keepalive: true
        }).catch(function(error) {
            console.error('[ProcessMonitor] Error sending event:', error);
        });
    }

    /**
     * Check if running in development mode
     * @returns {boolean} Whether in development mode
     */
    function isDevelopment() {
        return window.location.hostname === 'localhost' ||
               window.location.hostname === '127.0.0.1';
    }

    // Register custom user events
    function trackCustomEvent(eventName, details = {}) {
        if (!initialized) {
            console.warn('[ProcessMonitor] Not initialized. Call init() first.');
            return;
        }
        
        trackEvent('custom_' + eventName, details);
    }

    // Register global error
    function trackError(error, additionalInfo = {}) {
        if (!initialized) {
            console.warn('[ProcessMonitor] Not initialized. Call init() first.');
            return;
        }
        
        let errorDetails = {
            message: error.message || String(error),
            stack: error.stack || null,
            ...additionalInfo
        };
        
        trackEvent('manualError', errorDetails);
    }

    // Public API
    window.ProcessMonitor = {
        init: init,
        trackEvent: trackCustomEvent,
        trackError: trackError,
        getSessionId: () => config.sessionId
    };
})();