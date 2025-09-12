/**
 * Mobile Performance Optimizations for Snap Lotto
 * Reduces lag and improves responsiveness on mobile devices
 */

// Throttle function for better performance
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Debounce function for input events
function debounce(func, wait, immediate) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Optimized chart rendering with batched DOM updates
function optimizedRenderFrequencyChart(frequencyData) {
    if (!frequencyData || !Array.isArray(frequencyData) || frequencyData.length === 0) {
        return;
    }
    
    const barChartContainer = document.querySelector('.bar-chart-container');
    if (!barChartContainer) return;
    
    // Use document fragment for batch DOM updates
    const fragment = document.createDocumentFragment();
    const frequencyChart = document.createElement('div');
    frequencyChart.className = 'frequency-chart d-flex align-items-end justify-content-center pb-2';
    
    // Mobile-optimized styles
    Object.assign(frequencyChart.style, {
        height: window.innerWidth < 576 ? '150px' : '200px',
        gap: window.innerWidth < 576 ? '4px' : '8px',
        width: '100%',
        padding: window.innerWidth < 576 ? '10px' : '15px 20px',
        maxWidth: '100%',
        margin: '0 auto',
        boxSizing: 'border-box'
    });
    
    const sortedData = [...frequencyData].sort((a, b) => b.frequency - a.frequency);
    const maxFrequency = sortedData[0]?.frequency || 1;
    const top10Data = sortedData.slice(0, 10);
    
    const colorClasses = ['bg-danger', 'bg-warning', 'bg-success'];
    
    // Batch create all bars
    top10Data.forEach((item, index) => {
        const { number, frequency } = item;
        
        const barColumn = document.createElement('div');
        barColumn.className = 'bar-column text-center position-relative';
        
        const barContainer = document.createElement('div');
        barContainer.className = 'interactive-bar-container';
        barContainer.style.height = window.innerWidth < 576 ? '120px' : '170px';
        barContainer.style.display = 'flex';
        barContainer.style.alignItems = 'flex-end';
        
        const bar = document.createElement('div');
        bar.className = `interactive-bar ${index < 3 ? colorClasses[index] : 'bg-primary'}`;
        
        const minHeight = 25;
        const maxHeight = 100;
        const heightRange = maxHeight - minHeight;
        const normalizedFreq = frequency / maxFrequency;
        const heightPercentage = minHeight + (normalizedFreq * heightRange * 0.8);
        
        Object.assign(bar.style, {
            height: `${heightPercentage}%`,
            width: window.innerWidth < 576 ? '28px' : '36px',
            borderRadius: '4px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            transition: 'transform 0.15s ease'
        });
        
        const numberLabel = document.createElement('div');
        numberLabel.className = 'number-label mt-1';
        numberLabel.textContent = number;
        numberLabel.style.fontSize = window.innerWidth < 576 ? '0.75rem' : '0.875rem';
        
        // Optimized touch events for mobile
        if ('ontouchstart' in window) {
            bar.addEventListener('touchstart', function(e) {
                e.preventDefault();
                this.style.transform = 'scaleY(1.05)';
            }, { passive: false });
            
            bar.addEventListener('touchend', function(e) {
                e.preventDefault();
                this.style.transform = 'scaleY(1)';
            }, { passive: false });
        } else {
            // Desktop hover events
            bar.addEventListener('mouseenter', function() {
                this.style.transform = 'scaleY(1.05)';
            });
            
            bar.addEventListener('mouseleave', function() {
                this.style.transform = 'scaleY(1)';
            });
        }
        
        barContainer.appendChild(bar);
        barColumn.appendChild(barContainer);
        barColumn.appendChild(numberLabel);
        frequencyChart.appendChild(barColumn);
    });
    
    // Single DOM update
    fragment.appendChild(frequencyChart);
    
    // Add legend
    const legend = document.createElement('div');
    legend.className = 'frequency-legend d-flex justify-content-center mt-3 small text-muted';
    legend.style.fontSize = window.innerWidth < 576 ? '0.7rem' : '0.875rem';
    legend.innerHTML = `
        <div class="me-2"><span class="badge bg-danger">&nbsp;</span> Most</div>
        <div class="me-2"><span class="badge bg-warning">&nbsp;</span> 2nd</div>
        <div><span class="badge bg-success">&nbsp;</span> 3rd</div>
    `;
    fragment.appendChild(legend);
    
    // Batch DOM update
    barChartContainer.innerHTML = '';
    barChartContainer.appendChild(fragment);
}

// Optimized scroll handler
const optimizedScrollHandler = throttle(function() {
    // Handle scroll-based optimizations
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Hide/show elements based on scroll position for performance
    if (scrollTop > 100) {
        document.body.classList.add('scrolled');
    } else {
        document.body.classList.remove('scrolled');
    }
}, 16); // ~60fps

// Optimized resize handler
const optimizedResizeHandler = debounce(function() {
    // Recalculate layout on resize
    const charts = document.querySelectorAll('.frequency-chart');
    charts.forEach(chart => {
        // Update chart dimensions for new screen size
        if (window.innerWidth < 576) {
            chart.style.height = '150px';
            chart.style.gap = '4px';
            chart.style.padding = '10px';
        } else {
            chart.style.height = '200px';
            chart.style.gap = '8px';
            chart.style.padding = '15px 20px';
        }
    });
}, 250);

// Performance monitoring
function performanceMonitor() {
    if ('performance' in window) {
        const navigationEntry = performance.getEntriesByType('navigation')[0];
        if (navigationEntry) {
            console.log('Page load time:', navigationEntry.loadEventEnd - navigationEntry.loadEventStart + 'ms');
        }
    }
}

// Initialize mobile optimizations
function initMobileOptimizations() {
    // Add event listeners
    window.addEventListener('scroll', optimizedScrollHandler, { passive: true });
    window.addEventListener('resize', optimizedResizeHandler, { passive: true });
    
    // Optimize touch interactions
    if ('ontouchstart' in window) {
        document.body.classList.add('touch-device');
        
        // Disable hover effects on touch devices
        const style = document.createElement('style');
        style.textContent = `
            .touch-device .btn:hover,
            .touch-device .card:hover,
            .touch-device .lottery-ball:hover {
                transform: none !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Reduce animations on slower devices
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
        document.body.classList.add('reduced-animations');
        
        const style = document.createElement('style');
        style.textContent = `
            .reduced-animations * {
                animation-duration: 0.1s !important;
                transition-duration: 0.1s !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Optimize images for mobile
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.loading = 'lazy';
        img.style.willChange = 'auto';
    });
    
    // Add performance monitoring
    if (document.readyState === 'complete') {
        performanceMonitor();
    } else {
        window.addEventListener('load', performanceMonitor);
    }
    
    console.log('Mobile optimizations initialized');
}

// Optimized lottery card rendering
function optimizedLotteryCardRender() {
    const cards = document.querySelectorAll('.result-card');
    
    // Use Intersection Observer for lazy rendering
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        cards.forEach(card => observer.observe(card));
    }
}

// Memory management
function cleanupEventListeners() {
    // Remove unused event listeners to prevent memory leaks
    const tooltips = document.querySelectorAll('.chart-tooltip');
    tooltips.forEach(tooltip => tooltip.remove());
}

// Periodic cleanup
setInterval(cleanupEventListeners, 30000); // Every 30 seconds

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileOptimizations);
} else {
    initMobileOptimizations();
}

// Replace the original chart renderer with optimized version
if (typeof renderFrequencyChart !== 'undefined') {
    window.originalRenderFrequencyChart = renderFrequencyChart;
    window.renderFrequencyChart = optimizedRenderFrequencyChart;
}

// Export functions for use in other scripts
window.mobileOptimizations = {
    throttle,
    debounce,
    optimizedRenderFrequencyChart,
    initMobileOptimizations,
    optimizedLotteryCardRender
};