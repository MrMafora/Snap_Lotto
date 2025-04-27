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
                type: 'standard',
                duration: 15, // 15 seconds
                image: '/static/ads/standard-ad-1.svg',
                alt: 'Advertisement',
                url: 'https://www.example.com/ad1'
            },
            {
                id: 'missing-children-1',
                type: 'missing_children',
                duration: 5, // 5 seconds
                image: '/static/images/missing_children_sample.svg',
                alt: 'Missing Children Alert',
                url: 'https://www.missingchildren.org.za'
            }
        ],
        
        // Results placement ads (shown with lottery results)
        results: [
            {
                id: 'standard-ad-2',
                type: 'standard',
                duration: 10, // 10 seconds
                image: '/static/ads/standard-ad-2.svg',
                alt: 'Advertisement',
                url: 'https://www.example.com/ad2'
            }
        ],
        
        // Sidebar placement ads
        sidebar: [
            {
                id: 'standard-ad-3',
                type: 'standard',
                duration: 0, // Static ad
                image: '/static/ads/standard-ad-3.svg',
                alt: 'Advertisement',
                url: 'https://www.example.com/ad3'
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
                type: 'missing_children',
                duration: 5,
                image: '/static/images/missing_children_sample.svg',
                alt: 'Missing Children Alert',
                url: 'https://www.missingchildren.org.za'
            };
        } else {
            return {
                id: 'mock-standard-ad',
                type: 'standard',
                duration: 15,
                image: 'https://via.placeholder.com/300x250?text=Advertisement',
                alt: 'Advertisement',
                url: 'https://www.example.com'
            };
        }
    };
    
    // Log that the module is loaded
    console.log('Ad placement helper initialized');
})();