/**
 * Direct Checkmark System - Force applies color-coded checkmarks to matched lottery balls
 * This is a direct, brute-force approach to ensure checkmarks are visible
 * Each lottery game type has its own distinct, accessible color for better visibility
 */
(function() {
    console.log("Direct checkmark system initialized");
    
    // Function to add checkmarks to balls that don't have them
    function addCheckmarksDirectly() {
        // Target all ball-matched elements without checkmarks
        const matchedBalls = document.querySelectorAll('.ball-matched');
        
        console.log(`Adding checkmarks to ${matchedBalls.length} matched balls`);
        
        matchedBalls.forEach(ball => {
            // Check if this ball already has a checkmark
            const existingIndicator = ball.querySelector('.match-indicator');
            
            if (!existingIndicator) {
                // Create new checkmark indicator
                const indicator = document.createElement('div');
                indicator.className = 'match-indicator';
                indicator.textContent = '✓';
                
                // Determine game type based on title or class
                if (ball.title) {
                    // Powerball Games
                    if (ball.title.includes('Powerball Plus')) {
                        indicator.classList.add('match-powerball-plus');
                        if (ball.title.includes('Bonus')) {
                            indicator.classList.add('match-powerball-plus-bonus');
                        }
                    } 
                    else if (ball.title.includes('Powerball')) {
                        indicator.classList.add('match-powerball');
                        if (ball.title.includes('Bonus')) {
                            indicator.classList.add('match-powerball-bonus');
                        }
                    } 
                    // Lotto Games
                    else if (ball.title.includes('Lotto Plus 2')) {
                        indicator.classList.add('match-lotto-plus-2');
                        if (ball.title.includes('Bonus')) {
                            indicator.classList.add('match-lotto-plus-2-bonus');
                        }
                    }
                    else if (ball.title.includes('Lotto Plus 1')) {
                        indicator.classList.add('match-lotto-plus-1');
                        if (ball.title.includes('Bonus')) {
                            indicator.classList.add('match-lotto-plus-1-bonus');
                        }
                    }
                    else if (ball.title.includes('Lotto') && !ball.title.includes('Daily')) {
                        indicator.classList.add('match-lotto');
                        if (ball.title.includes('Bonus')) {
                            indicator.classList.add('match-lotto-bonus');
                        }
                    }
                    // Daily Lotto
                    else if (ball.title.includes('Daily Lotto')) {
                        indicator.classList.add('match-daily-lotto');
                        if (ball.title.includes('Bonus')) {
                            indicator.classList.add('match-daily-lotto-bonus');
                        }
                    }
                    // Fallback based on nearby elements
                    else {
                        const gameHeader = document.getElementById('primary-game-label');
                        if (gameHeader) {
                            const gameText = gameHeader.textContent;
                            if (gameText.includes('Powerball Plus')) {
                                indicator.classList.add('match-powerball-plus');
                            } else if (gameText.includes('Powerball')) {
                                indicator.classList.add('match-powerball');
                            } else if (gameText.includes('Lotto Plus 2')) {
                                indicator.classList.add('match-lotto-plus-2');
                            } else if (gameText.includes('Lotto Plus 1')) {
                                indicator.classList.add('match-lotto-plus-1');
                            } else if (gameText.includes('Lotto') && !gameText.includes('Daily')) {
                                indicator.classList.add('match-lotto');
                            } else if (gameText.includes('Daily Lotto')) {
                                indicator.classList.add('match-daily-lotto');
                            } else {
                                // Default to Powerball styling
                                indicator.classList.add('match-powerball');
                            }
                        } else {
                            // Default to Powerball styling if can't determine
                            indicator.classList.add('match-powerball');
                        }
                    }
                } else {
                    // Default to Powerball styling
                    indicator.classList.add('match-powerball');
                }
                
                // Add to ball
                ball.appendChild(indicator);
                console.log("Added checkmark to ball:", ball.textContent);
            } 
            // Ensure existing indicators have the checkmark text
            else if (!existingIndicator.textContent || existingIndicator.textContent.trim() === '') {
                existingIndicator.textContent = '✓';
                console.log("Updated existing indicator on ball:", ball.textContent);
            }
        });
    }
    
    // Run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(addCheckmarksDirectly, 1000);
        });
    } else {
        setTimeout(addCheckmarksDirectly, 1000);
    }
    
    // Run when View Results button is clicked
    document.addEventListener('click', function(e) {
        if (e.target && (e.target.id === 'view-results-btn' || 
                         (e.target.parentNode && e.target.parentNode.id === 'view-results-btn'))) {
            console.log("View Results button clicked, adding direct checkmarks");
            // Wait a moment for the display to update
            setTimeout(addCheckmarksDirectly, 300);
            // And once more to catch any late-rendered content
            setTimeout(addCheckmarksDirectly, 1000);
        }
    });
    
    // Also run periodically to catch dynamic updates
    setInterval(addCheckmarksDirectly, 2000);
    
    // Watch for DOM changes specifically for matched balls
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.classList && node.classList.contains('ball-matched')) {
                            // If a matched ball was added, add checkmark
                            setTimeout(addCheckmarksDirectly, 100);
                        } else if (node.querySelectorAll) {
                            // Check children
                            const matchedChildren = node.querySelectorAll('.ball-matched');
                            if (matchedChildren.length > 0) {
                                setTimeout(addCheckmarksDirectly, 100);
                            }
                        }
                    }
                });
            }
        });
    });
    
    // Start observing with a more targeted approach
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log("Direct checkmark system fully initialized");
})();