/**
 * Ad Helper Functions for Snap Lotto
 * This file contains helper functions for the advertisement system
 */

// Helper function to get ads by placement
function getAdsByPlacement(placement) {
    console.log(`Getting ads for placement: ${placement}`);
    
    // Check if the ads object exists and has the placement
    if (!window.AdManager || !window.AdManager.ads || !window.AdManager.ads[placement]) {
        console.warn(`No ads found for placement: ${placement}`);
        return [];
    }
    
    // Get the ads for this placement
    const ads = window.AdManager.ads[placement];
    
    // If ads is already an array, return it
    if (Array.isArray(ads)) {
        console.log(`Found ${ads.length} ads for placement: ${placement}`);
        return ads;
    }
    
    // If ads is a single object, convert to array
    if (ads && typeof ads === 'object') {
        console.log(`Found 1 ad for placement: ${placement}`);
        return [ads];
    }
    
    // Default return empty array
    console.warn(`No valid ads found for placement: ${placement}`);
    return [];
}

// Export the function to the window object
window.getAdsByPlacement = getAdsByPlacement;