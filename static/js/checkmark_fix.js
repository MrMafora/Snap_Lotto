/**
 * Checkmark Fix Script
 * This script fixes the checkmark display issues in the ticket scanner UI.
 * It replaces all instances of text-based checkmarks with properly rendered
 * HTML entity-based checkmarks.
 */

// Execute after page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Checkmark Fix script loaded and active');
    
    // Create a diagnostic element in the page to show the fix is working
    createDiagnosticElement();
    
    // Initial fix application
    setTimeout(fixCheckmarks, 500);
    
    // Fix checkmarks periodically to ensure they are created properly
    setInterval(fixCheckmarks, 1000);
});

/**
 * Creates a small diagnostic element in the corner of the page
 * This helps confirm the script is loaded and running
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
    diagnostic.innerHTML = 'Checkmark fix active &#10004;';
    document.body.appendChild(diagnostic);
}

/**
 * Fixes all checkmarks in the page by converting the Unicode checkmark to HTML entity
 * This makes checkmarks consistently visible across all browsers and devices
 */
function fixCheckmarks() {
    // Find all elements with match-indicator class
    const matchIndicators = document.querySelectorAll('.match-indicator');
    
    // Display count in the diagnostic element
    const diagnostic = document.getElementById('checkmark-fix-indicator');
    if (diagnostic) {
        diagnostic.innerHTML = `Checkmarks fixed: ${matchIndicators.length} &#10004;`;
    }
    
    // Loop through each match indicator and set correct checkmark
    matchIndicators.forEach(indicator => {
        // Set the checkmark as HTML entity instead of Unicode character
        indicator.innerHTML = '&#10004;';
    });
    
    // Also add an additional CSS class to make sure checkmarks are visible
    document.querySelectorAll('.ball-matched').forEach(ball => {
        ball.classList.add('checkmark-fixed');
    });
}