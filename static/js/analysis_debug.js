/**
 * Analysis Debug Script
 * Add to lottery_analysis.html to help debug issues with tabs not showing data
 */

// Enhanced Fetch functions that log detailed information
function debugFetch(url, options = {}) {
    console.log('[DEBUG] Fetch request:', {
        url,
        options,
        timestamp: new Date().toISOString()
    });
    
    const startTime = performance.now();
    
    return fetch(url, options)
        .then(response => {
            const endTime = performance.now();
            const duration = Math.round(endTime - startTime);
            
            console.log('[DEBUG] Fetch response:', {
                url,
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries([...response.headers.entries()]),
                duration: duration + 'ms',
                timestamp: new Date().toISOString()
            });
            
            // Clone the response to log its content without consuming it
            const clonedResponse = response.clone();
            
            // Log response content for debugging
            clonedResponse.text().then(text => {
                try {
                    // Try to parse as JSON
                    const json = JSON.parse(text);
                    console.log('[DEBUG] Response JSON structure:', {
                        keys: Object.keys(json),
                        topLevelType: typeof json,
                        length: typeof json === 'object' ? Object.keys(json).length : null,
                        isArray: Array.isArray(json),
                        hasData: Object.keys(json).length > 0
                    });
                    
                    // If it's the patterns API response, do specific checks
                    if (url.includes('/api/lottery-analysis/patterns')) {
                        // Check for lottery type data
                        for (const [key, value] of Object.entries(json)) {
                            console.log(`[DEBUG] Pattern data for ${key}:`, {
                                hasClusterData: value && value.cluster_data,
                                hasPcaData: value && value.pca_data,
                                hasChartData: value && value.chart_base64 && value.chart_base64.length > 0
                            });
                        }
                    }
                } catch (e) {
                    // Not valid JSON
                    console.log('[DEBUG] Response is not valid JSON:', {
                        error: e.message,
                        textPreview: text.substring(0, 100) + (text.length > 100 ? '...' : '')
                    });
                }
            });
            
            return response;
        })
        .catch(error => {
            const endTime = performance.now();
            const duration = Math.round(endTime - startTime);
            
            console.error('[DEBUG] Fetch error:', {
                url,
                error: error.toString(),
                stack: error.stack,
                duration: duration + 'ms',
                timestamp: new Date().toISOString()
            });
            
            throw error;
        });
}

// Enable content debugging 
function debugDomChanges(targetId) {
    const target = document.getElementById(targetId);
    if (!target) {
        console.error(`[DEBUG] Cannot find element with ID '${targetId}'`);
        return;
    }
    
    // Log when content changes
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            console.log(`[DEBUG] DOM changed in ${targetId}:`, {
                type: mutation.type,
                addedNodes: mutation.addedNodes.length,
                removedNodes: mutation.removedNodes.length,
                visibleContent: target.offsetHeight > 0 && target.offsetWidth > 0,
                contentLength: target.innerHTML.length
            });
        }
    });
    
    observer.observe(target, { 
        childList: true, 
        subtree: true,
        attributes: true,
        characterData: true
    });
    
    console.log(`[DEBUG] Now monitoring DOM changes in element '${targetId}'`);
}

// Log tab visibility changes
function debugTabVisibility() {
    // Monitor all tab changes
    document.addEventListener('shown.bs.tab', function(event) {
        const targetId = event.target.getAttribute('data-bs-target');
        const targetEl = document.querySelector(targetId);
        
        console.log('[DEBUG] Tab shown:', {
            tabId: event.target.id,
            targetId: targetId,
            tabVisible: targetEl ? (targetEl.offsetHeight > 0 && targetEl.offsetWidth > 0) : false,
            tabHasContent: targetEl ? !!targetEl.innerHTML.trim() : false,
            tabContentLength: targetEl ? targetEl.innerHTML.length : 0
        });
        
        // Check display property of content
        if (targetEl) {
            const computedStyle = window.getComputedStyle(targetEl);
            console.log('[DEBUG] Tab container style:', {
                display: computedStyle.display,
                visibility: computedStyle.visibility,
                height: computedStyle.height,
                width: computedStyle.width,
                overflow: computedStyle.overflow
            });
            
            // Check children visibility
            const children = Array.from(targetEl.children);
            children.forEach(child => {
                const childStyle = window.getComputedStyle(child);
                console.log(`[DEBUG] Child element (${child.tagName}${child.id ? '#'+child.id : ''}) style:`, {
                    display: childStyle.display,
                    visibility: childStyle.visibility,
                    height: childStyle.height,
                    width: childStyle.width
                });
            });
        }
    });
}

// Function to patch the fetchWithCSRF to use debugging
function patchFetchWithCSRF() {
    if (typeof fetchWithCSRF !== 'function') {
        console.error('[DEBUG] fetchWithCSRF not found, cannot patch');
        return;
    }
    
    const originalFetchWithCSRF = fetchWithCSRF;
    window.fetchWithCSRF = function(url, options = {}) {
        console.log('[DEBUG] fetchWithCSRF called:', { url, options });
        
        // Use our debug fetch instead
        const finalOptions = {
            ...options,
            headers: {
                ...(options.headers || {}),
                'X-Debug': 'true'
            }
        };
        
        return debugFetch(url, finalOptions)
            .then(response => {
                console.log('[DEBUG] fetchWithCSRF response received for:', url);
                return response;
            })
            .catch(error => {
                console.error('[DEBUG] fetchWithCSRF error for:', url, error);
                throw error;
            });
    };
    
    console.log('[DEBUG] Successfully patched fetchWithCSRF');
}

// Start debugging when loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] Analysis debug script loaded');
    
    // Patch fetch function
    patchFetchWithCSRF();
    
    // Debug tab visibility
    debugTabVisibility();
    
    // Monitor content areas
    setTimeout(() => {
        debugDomChanges('patterns-content');
        debugDomChanges('timeseries-content');
        debugDomChanges('correlations-content');
        debugDomChanges('winners-content');
    }, 1000);
});