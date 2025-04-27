/**
 * Helper function to get available ads by placement
 * Supports dual ad system with standard 15-second ads and 
 * special 5-second missing children ads
 */

(function() {
    // Define our ad inventory
    const adInventory = {
        // Scanner placement ads (shown during ticket scanning)
        scanner: [
            {
                id: 'standard-ad-1',
                name: 'Standard Advertisement',
                type: 'standard',
                duration: 15, // 15 seconds
                image: '/static/ads/standard-ad-1.svg',
                file_url: '/static/ads/standard-ad-1.svg', // Used by new ad loader
                image_url: '/static/ads/standard-ad-1.svg', // Used by new ad loader
                alt: 'Advertisement',
                url: 'https://www.example.com/ad1',
                loading_duration: 5, // 5 seconds for loading overlay
                custom_message: 'Processing your lottery ticket...'
            },
            {
                id: 'missing-children-1',
                name: 'Missing Children Alert',
                type: 'missing_children',
                duration: 5, // 5 seconds
                image: '/static/images/missing_children_sample.svg',
                file_url: null, // No video file
                image_url: '/static/images/missing_children_sample.svg', // Used by new ad loader
                alt: 'Missing Children Alert',
                url: 'https://www.missingchildren.org.za',
                loading_duration: 5, // 5 seconds for loading overlay
                custom_message: 'Help find missing children in South Africa'
            }
        ],
        
        // Results placement ads (shown with lottery results)
        results: [
            {
                id: 'standard-ad-2',
                name: 'Results Advertisement',
                type: 'standard',
                duration: 10, // 10 seconds
                image: '/static/ads/standard-ad-2.svg',
                file_url: '/static/ads/standard-ad-2.svg', // Used by new ad loader
                image_url: '/static/ads/standard-ad-2.svg', // Used by new ad loader
                alt: 'Advertisement',
                url: 'https://www.example.com/ad2',
                loading_duration: 5, // 5 seconds for loading overlay
                custom_message: 'Your results are ready to view'
            }
        ],
        
        // Sidebar placement ads
        sidebar: [
            {
                id: 'standard-ad-3',
                name: 'Sidebar Advertisement',
                type: 'standard',
                duration: 0, // Static ad
                image: '/static/ads/standard-ad-3.svg',
                file_url: '/static/ads/standard-ad-3.svg', // Used by new ad loader
                image_url: '/static/ads/standard-ad-3.svg', // Used by new ad loader
                alt: 'Advertisement',
                url: 'https://www.example.com/ad3',
                loading_duration: 0, // No loading overlay for sidebar ads
                custom_message: null
            }
        ]
    };
    
    /**
     * Get ads for a specific placement
     * @param {string} placement - The ad placement identifier (e.g., 'scanner', 'results')
     * @returns {Array} - Array of ad objects for the specified placement
     */
    window.getAdsByPlacement = function(placement) {
        // If we don't have ads for this placement, return empty array
        if (!adInventory[placement]) {
            console.warn(`No ads defined for placement: ${placement}`);
            return [];
        }
        
        // Return the ads for this placement
        return adInventory[placement];
    };
    
    /**
     * Create a placeholder ad for development
     * @param {string} type - The ad type ('standard' or 'missing_children')
     * @returns {Object} - Mock ad object
     */
    window.createMockAd = function(type = 'standard') {
        if (type === 'missing_children') {
            return {
                id: 'mock-missing-children-ad',
                name: 'Help Find Missing Children',
                type: 'missing_children',
                duration: 5,
                image: '/static/images/missing_children_sample.svg',
                file_url: null, // No video file
                image_url: '/static/images/missing_children_sample.svg',
                alt: 'Missing Children Alert',
                url: 'https://www.missingchildren.org.za',
                loading_duration: 5,
                custom_message: 'Help find missing children in South Africa'
            };
        } else {
            return {
                id: 'mock-standard-ad',
                name: 'Advertisement',
                type: 'standard',
                duration: 15,
                image: '/static/ads/standard-ad-1.svg',
                file_url: '/static/ads/standard-ad-1.svg',
                image_url: '/static/ads/standard-ad-1.svg',
                alt: 'Advertisement',
                url: 'https://www.example.com',
                loading_duration: 5,
                custom_message: 'Processing your lottery ticket...'
            };
        }
    };
    
    // Log that the module is loaded
    console.log('Ad placement helper initialized');
})();