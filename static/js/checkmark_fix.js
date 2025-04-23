/**
 * Simplified Checkmark Fix Script
 * This script directly creates new checkmark indicators instead of modifying existing ones
 */

// Execute after page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple Checkmark Fix script loaded and active');
    
    // Watch for scan results appearing in the page
    watchForScanResults();
    
    // Create indicator to show the fix is active
    createDiagnosticElement();
});

/**
 * Creates a small diagnostic element in the corner of the page
 */
function createDiagnosticElement() {
    const diagnostic = document.createElement('div');
    diagnostic.id = 'checkmark-fix-indicator';
    diagnostic.style.position = 'fixed';
    diagnostic.style.bottom = '5px';
    diagnostic.style.right = '5px';
    diagnostic.style.backgroundColor = 'rgba(0,0,0,0.6)';
    diagnostic.style.color = 'white';
    diagnostic.style.padding = '3px 6px';
    diagnostic.style.fontSize = '10px';
    diagnostic.style.borderRadius = '3px';
    diagnostic.style.zIndex = '9999';
    diagnostic.innerHTML = 'Checkmark fix active ✓';
    document.body.appendChild(diagnostic);
}

/**
 * Sets up a mutation observer to watch for scan results appearing
 */
function watchForScanResults() {
    // Check for scan results container becoming visible
    const resultsContainer = document.getElementById('results-container');
    
    if (resultsContainer) {
        console.log('Watching for scan results to appear');
        
        // Create observer to watch for class changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'class' && 
                    !resultsContainer.classList.contains('d-none')) {
                    // Results became visible, add our checkmarks with a delay
                    console.log('Scan results detected, applying checkmark fix');
                    setTimeout(addCheckmarksToMatchedBalls, 1000);
                    
                    // Also set an interval to keep applying them as new results load
                    setInterval(addCheckmarksToMatchedBalls, 1500);
                }
            });
        });
        
        // Start observing
        observer.observe(resultsContainer, { attributes: true });
    }
}

/**
 * Adds explicit checkmark symbols to matched balls
 */
function addCheckmarksToMatchedBalls() {
    // Get all matched balls
    const matchedBalls = document.querySelectorAll('.ball-matched');
    
    // Update diagnostic
    const diagnostic = document.getElementById('checkmark-fix-indicator');
    if (diagnostic) {
        diagnostic.innerHTML = `Matched balls found: ${matchedBalls.length} ✓`;
    }
    
    // For each matched ball
    matchedBalls.forEach(ball => {
        // Add "FIXED" class to track which ones we've processed
        if (!ball.classList.contains('checkmark-FIXED')) {
            ball.classList.add('checkmark-FIXED');
            
            // Check if it already has a match indicator
            let existingIndicator = ball.querySelector('.match-indicator');
            
            // If no indicator or it's empty, create a new one
            if (!existingIndicator || existingIndicator.innerHTML.trim() === '') {
                // Remove any existing indicator
                if (existingIndicator) {
                    existingIndicator.remove();
                }
                
                // Create a completely new indicator element
                const checkmark = document.createElement('div');
                checkmark.className = 'match-indicator';
                
                // Use text content for maximum compatibility
                checkmark.textContent = '✓';
                
                // Find the game type from classes
                const classList = Array.from(ball.classList);
                let gameClass = '';
                
                // Determine which game type this is for
                if (ball.parentElement && ball.parentElement.hasAttribute('data-game-type')) {
                    const gameType = ball.parentElement.getAttribute('data-game-type');
                    
                    if (gameType.includes('Powerball Plus')) {
                        gameClass = 'match-powerball-plus';
                    } else if (gameType.includes('Powerball')) {
                        gameClass = 'match-powerball';
                    } else if (gameType.includes('Lotto Plus 1')) {
                        gameClass = 'match-lotto-plus-1';
                    } else if (gameType.includes('Lotto Plus 2')) {
                        gameClass = 'match-lotto-plus-2';
                    } else {
                        gameClass = 'match-powerball'; // Default
                    }
                } else {
                    // Default if we can't determine
                    gameClass = 'match-powerball';
                }
                
                // Add the appropriate class
                checkmark.classList.add(gameClass);
                
                // Add to the ball
                ball.appendChild(checkmark);
                
                console.log('Added new checkmark to matched ball');
            }
        }
    });
}