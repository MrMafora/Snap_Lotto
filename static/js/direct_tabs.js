/**
 * Direct Tab Navigation System
 * Provides a simplified tab navigation solution that works without relying on Bootstrap
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Direct Tab Navigation script loaded");
    
    // Find all direct tab buttons (from the card we created in the HTML)
    const directButtons = document.querySelectorAll('.direct-tab-buttons button');
    console.log(`Found ${directButtons.length} direct tab buttons`);
    
    // Set up click handlers
    directButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the target tab id from the button's data attribute
            const tabId = this.getAttribute('data-tab');
            if (!tabId) {
                console.error("Button has no data-tab attribute");
                return;
            }
            
            console.log(`Direct button clicked for tab: ${tabId}`);
            
            // 1. Deactivate all tab buttons in the main tab navigation
            document.querySelectorAll('.nav-tabs .nav-link').forEach(tab => {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            });
            
            // 2. Activate the correct tab button
            const tabButton = document.querySelector(`.nav-tabs .nav-link[data-bs-target="#${tabId}"]`);
            if (tabButton) {
                tabButton.classList.add('active');
                tabButton.setAttribute('aria-selected', 'true');
            } else {
                console.warn(`Could not find tab button for #${tabId}`);
            }
            
            // 3. Hide all tab content panels
            document.querySelectorAll('.tab-content .tab-pane').forEach(pane => {
                pane.classList.remove('active');
                pane.classList.remove('show');
            });
            
            // 4. Show the target tab content
            const targetPane = document.getElementById(tabId);
            if (targetPane) {
                targetPane.classList.add('active');
                targetPane.classList.add('show');
                
                // 5. Load the tab data if needed
                loadTabDataIfNeeded(tabId);
            } else {
                console.error(`Tab pane #${tabId} not found`);
            }
            
            // Highlight the clicked button
            directButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Supporting function to load tab data
    function loadTabDataIfNeeded(tabId) {
        console.log(`Checking if data needs to be loaded for ${tabId}`);
        
        // Check if we have a loading function in the window scope
        if (typeof window.loadTabData === 'function') {
            console.log(`Calling window.loadTabData('${tabId}')`);
            window.loadTabData(tabId);
        } else if (window.directFetch) {
            // Directly make the API call based on tab ID
            let apiUrl = null;
            
            switch (tabId) {
                case 'patterns':
                    apiUrl = '/api/lottery-analysis/patterns?lottery_type=&days=365';
                    break;
                case 'timeseries':
                    apiUrl = '/api/lottery-analysis/time-series?lottery_type=&days=365';
                    break;
                case 'winners':
                    apiUrl = '/api/lottery-analysis/winners?lottery_type=&days=365';
                    break;
                case 'correlations':
                    apiUrl = '/api/lottery-analysis/correlations?days=365';
                    break;
            }
            
            if (apiUrl) {
                console.log(`Direct fetching data from ${apiUrl}`);
                
                // Show loading state
                const loadingEl = document.getElementById(`${tabId}-loading`);
                const contentEl = document.getElementById(`${tabId}-content`);
                
                if (loadingEl && contentEl) {
                    loadingEl.style.display = 'block';
                    contentEl.style.display = 'none';
                    
                    loadingEl.innerHTML = `
                        <div class="spinner-border text-primary" role="status">
                            <span class="sr-only">Loading...</span>
                        </div>
                        <p class="mt-2">Loading data for ${tabId}...</p>
                        <p class="small text-muted">Please wait a moment...</p>
                    `;
                    
                    // Make the API call
                    window.directFetch(apiUrl)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error! Status: ${response.status}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            console.log(`Data loaded for ${tabId}`);
                            
                            // Process data based on tab
                            if (window[`process${tabId.charAt(0).toUpperCase() + tabId.slice(1)}Data`]) {
                                window[`process${tabId.charAt(0).toUpperCase() + tabId.slice(1)}Data`](data, contentEl);
                            } else {
                                console.warn(`No data processor for ${tabId}`);
                                
                                // Default data display
                                contentEl.innerHTML = `
                                    <div class="alert alert-info">
                                        <h4>Data Loaded</h4>
                                        <p>The data has been loaded but no custom processor was found.</p>
                                    </div>
                                `;
                            }
                            
                            // Hide loading, show content
                            loadingEl.style.display = 'none';
                            contentEl.style.display = 'block';
                        })
                        .catch(error => {
                            console.error(`Error loading data for ${tabId}:`, error);
                            
                            // Show error
                            contentEl.innerHTML = `
                                <div class="alert alert-danger">
                                    <h4>Error Loading Data</h4>
                                    <p>${error.message}</p>
                                    <p>Please try refreshing the page or check the console for details.</p>
                                </div>
                            `;
                            
                            loadingEl.style.display = 'none';
                            contentEl.style.display = 'block';
                        });
                }
            }
        } else {
            console.warn("No method available to load tab data");
        }
    }
    
    // Check for direct deep linking to tabs via URL hash
    if (window.location.hash) {
        const hash = window.location.hash.substring(1); // Remove the #
        console.log(`Hash detected: ${hash}`);
        
        // Look for matching tab
        const button = document.querySelector(`.direct-tab-buttons button[data-tab="${hash}"]`);
        if (button) {
            console.log(`Triggering click on button for ${hash}`);
            button.click();
        }
    }
});