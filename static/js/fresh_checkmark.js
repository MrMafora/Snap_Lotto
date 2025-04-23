/**
 * Fresh Checkmark System
 * Adds color-coded checkmarks to matched lottery balls
 * Uses bold, accessible colors for each game type to help people with vision issues
 */
(function() {
    console.log("Fresh checkmark system initialized");
    
    // Function to add checkmarks to matched balls
    function addCheckmarksToMatchedBalls() {
        // First clear any existing indicators to prevent duplicates
        console.log("Clearing existing indicators");
        const existingIndicators = document.querySelectorAll('.match-indicator');
        existingIndicators.forEach(indicator => {
            indicator.remove();
        });
        
        // Find all matched balls
        console.log("Finding matched balls");
        const matchedBalls = document.querySelectorAll('.ball-matched');
        console.log(`Found ${matchedBalls.length} matched balls`);
        
        // Add checkmark to each matched ball
        matchedBalls.forEach((ball, index) => {
            // Create checkmark indicator
            const indicator = document.createElement('div');
            indicator.className = 'match-indicator';
            
            // Add game-specific class if available
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
            
            // Set checkmark text
            indicator.textContent = '✓';
            
            // Add to ball
            ball.appendChild(indicator);
        });
        
        console.log("Checkmarks added to matched balls");
    }
    
    // Run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(addCheckmarksToMatchedBalls, 1000);
        });
    } else {
        setTimeout(addCheckmarksToMatchedBalls, 1000);
    }
    
    // Run when View Results button is clicked
    document.addEventListener('click', function(e) {
        if (e.target && (e.target.id === 'view-results-btn' || 
                         (e.target.parentNode && e.target.parentNode.id === 'view-results-btn'))) {
            console.log("View Results button clicked, adding checkmarks");
            setTimeout(addCheckmarksToMatchedBalls, 300);
        }
    });
    
    // Also run periodically to catch dynamic updates
    setInterval(addCheckmarksToMatchedBalls, 2000);
    
    // Watch for DOM changes that might indicate new results
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                setTimeout(addCheckmarksToMatchedBalls, 300);
            }
        });
    });
    
    // Start observing the document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();