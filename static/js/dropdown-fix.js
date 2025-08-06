/**
 * Dropdown Fix for Data Analytics Preview Card
 * Ensures the filter dropdown works properly
 */

console.log('DROPDOWN FIX: Loading dedicated dropdown handler...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DROPDOWN FIX: DOM loaded, initializing dropdown...');
    
    // Wait for elements to be available
    setTimeout(function() {
        initializeFilterDropdown();
    }, 100);
});

function initializeFilterDropdown() {
    console.log('DROPDOWN FIX: Starting initialization...');
    
    const dropdownButton = document.getElementById('dataFilterDropdown');
    const dropdownMenu = document.querySelector('#dataFilterDropdown + .dropdown-menu');
    
    console.log('DROPDOWN FIX: Button found:', !!dropdownButton);
    console.log('DROPDOWN FIX: Menu found:', !!dropdownMenu);
    
    if (!dropdownButton || !dropdownMenu) {
        console.warn('DROPDOWN FIX: Elements not found, retrying in 500ms...');
        setTimeout(initializeFilterDropdown, 500);
        return;
    }
    
    console.log('DROPDOWN FIX: Adding click handler to button...');
    
    // Remove any existing listeners to avoid conflicts
    const newButton = dropdownButton.cloneNode(true);
    dropdownButton.parentNode.replaceChild(newButton, dropdownButton);
    
    // Add click handler
    newButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('DROPDOWN FIX: Button clicked!');
        
        const menu = this.nextElementSibling;
        const isOpen = menu.classList.contains('show') || menu.style.display === 'block';
        
        if (isOpen) {
            console.log('DROPDOWN FIX: Closing dropdown');
            menu.classList.remove('show');
            menu.style.display = 'none';
            this.setAttribute('aria-expanded', 'false');
        } else {
            console.log('DROPDOWN FIX: Opening dropdown');
            menu.classList.add('show');
            menu.style.display = 'block';
            this.setAttribute('aria-expanded', 'true');
            
            // Position the menu
            const rect = this.getBoundingClientRect();
            menu.style.position = 'absolute';
            menu.style.top = '100%';
            menu.style.right = '0';
            menu.style.left = 'auto';
            menu.style.zIndex = '1050';
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const button = document.getElementById('dataFilterDropdown');
        const menu = document.querySelector('#dataFilterDropdown + .dropdown-menu');
        
        if (button && menu && !button.contains(e.target) && !menu.contains(e.target)) {
            menu.classList.remove('show');
            menu.style.display = 'none';
            button.setAttribute('aria-expanded', 'false');
        }
    });
    
    // Handle filter selection
    const menuItems = dropdownMenu.querySelectorAll('.dropdown-item');
    menuItems.forEach(function(item) {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('DROPDOWN FIX: Filter selected:', this.textContent.trim());
            
            // Update active state
            const isLotteryFilter = this.hasAttribute('data-lottery-type');
            const isTimeFilter = this.hasAttribute('data-time-period');
            
            if (isLotteryFilter) {
                dropdownMenu.querySelectorAll('[data-lottery-type]').forEach(el => el.classList.remove('active'));
                this.classList.add('active');
                
                // Update badge
                const badge = document.querySelector('.current-lottery-type');
                if (badge) badge.textContent = this.textContent.trim();
            } else if (isTimeFilter) {
                dropdownMenu.querySelectorAll('[data-time-period]').forEach(el => el.classList.remove('active'));
                this.classList.add('active');
                
                // Update badge
                const badge = document.querySelector('.current-time-period');
                if (badge) badge.textContent = this.textContent.trim();
            }
            
            // Close dropdown
            dropdownMenu.classList.remove('show');
            dropdownMenu.style.display = 'none';
            newButton.setAttribute('aria-expanded', 'false');
            
            // Trigger chart update if available
            if (typeof fetchChartData === 'function') {
                const lotteryType = document.querySelector('.current-lottery-type').textContent;
                const timePeriod = document.querySelector('.current-time-period').textContent;
                console.log('DROPDOWN FIX: Updating charts with filters:', lotteryType, timePeriod);
                fetchChartData(lotteryType === 'All Types' ? 'all' : lotteryType, timePeriod === 'All Time' ? 'all' : '365');
            }
        });
    });
    
    console.log('DROPDOWN FIX: Initialization complete!');
}