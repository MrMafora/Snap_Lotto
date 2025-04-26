/**
 * Mobile Ticket Display Enhancer
 * Ensures proper display of lottery balls on mobile devices
 * Fixes layout issues, sizing, and spacing for small screens
 */

document.addEventListener("DOMContentLoaded", function() {
    // Only apply fixes on mobile
    if (window.innerWidth <= 576) {
        console.log("Mobile display fixes activated");
        
        // Function to fix lottery ball display
        function enhanceMobileDisplay() {
            // 1. Fix results container spacing
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.style.paddingBottom = '150px';
            }
            
            // 2. Fix ticket numbers container
            const ticketNumbersContainer = document.getElementById('ticket-numbers');
            if (ticketNumbersContainer) {
                // Give plenty of space for the rows
                ticketNumbersContainer.style.paddingBottom = '50px';
                
                // Ensure each row has proper spacing
                const rowContainers = ticketNumbersContainer.querySelectorAll('.mb-3');
                rowContainers.forEach(row => {
                    row.style.marginBottom = '30px';
                    row.style.paddingBottom = '20px';
                    row.style.borderBottom = '1px solid #eee';
                    row.style.overflow = 'visible';
                    row.style.position = 'relative';
                });
                
                // Ensure flex containers wrap properly
                const flexContainers = ticketNumbersContainer.querySelectorAll('.d-flex');
                flexContainers.forEach(container => {
                    container.style.display = 'flex';
                    container.style.flexWrap = 'wrap';
                    container.style.gap = '10px';
                    container.style.marginBottom = '25px';
                    container.style.width = '100%';
                    container.style.position = 'relative';
                    container.style.overflow = 'visible';
                });
                
                // Make strong text more visible
                const strongElements = ticketNumbersContainer.querySelectorAll('strong');
                strongElements.forEach(el => {
                    el.style.fontSize = '16px';
                    el.style.marginBottom = '10px';
                    el.style.display = 'block';
                });
                
                // Improve lottery ball display
                const lotteryBalls = document.querySelectorAll('.lottery-ball');
                lotteryBalls.forEach(ball => {
                    ball.style.width = '38px';
                    ball.style.height = '38px';
                    ball.style.fontSize = '16px';
                    ball.style.lineHeight = '38px';
                    ball.style.margin = '5px';
                    ball.style.display = 'inline-flex';
                    ball.style.alignItems = 'center';
                    ball.style.justifyContent = 'center';
                    ball.style.position = 'relative';
                    ball.style.zIndex = '1';
                });
                
                // Improve plus sign spacing
                const plusSigns = document.querySelectorAll('.mx-2');
                plusSigns.forEach(plus => {
                    plus.style.margin = '0 10px';
                    plus.style.display = 'inline-block';
                });
                
                // Increase font size for match indicators
                const matchIndicators = document.querySelectorAll('.match-indicator');
                matchIndicators.forEach(indicator => {
                    indicator.style.fontSize = '14px';
                    indicator.style.fontWeight = 'bold';
                });
            }
            
            // 3. Fix winning numbers display
            const winningNumbersContainer = document.getElementById('winning-numbers');
            if (winningNumbersContainer) {
                winningNumbersContainer.style.display = 'flex';
                winningNumbersContainer.style.flexWrap = 'wrap';
                winningNumbersContainer.style.gap = '10px';
                winningNumbersContainer.style.paddingBottom = '20px';
            }
            
            // 4. Fix matched numbers display
            const matchedNumbersContainer = document.getElementById('matched-numbers');
            if (matchedNumbersContainer) {
                matchedNumbersContainer.style.display = 'flex';
                matchedNumbersContainer.style.flexWrap = 'wrap';
                matchedNumbersContainer.style.gap = '10px';
            }
            
            // 5. Improve visibility of matched balls
            const matchedBalls = document.querySelectorAll('.ball-matched');
            matchedBalls.forEach(ball => {
                ball.style.boxShadow = '0 0 10px rgba(255, 215, 0, 0.8)';
                ball.style.border = '2px solid gold';
                ball.style.transform = 'scale(1.1)';
                ball.style.zIndex = '2';
            });
        }
        
        // Run the enhancer function
        enhanceMobileDisplay();
        
        // Set up a mutation observer to apply fixes to dynamically added content
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length) {
                        setTimeout(enhanceMobileDisplay, 100);
                    }
                });
            });
            
            observer.observe(resultsContainer, {
                childList: true,
                subtree: true
            });
        }
        
        // Set up a window resize handler
        window.addEventListener('resize', function() {
            if (window.innerWidth <= 576) {
                enhanceMobileDisplay();
            }
        });
    }
});