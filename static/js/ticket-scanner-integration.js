/**
 * Ticket Scanner Integration
 * Connects our clean file uploader with the existing ticket scanning functionality
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        scannerEndpoint: '/scan-ticket',
        scanButton: 'scan-button',
        resultsContainer: 'results-container',
        loadingElement: 'scanner-loading',
        errorElement: 'error-message',
        errorText: 'error-text',
        debug: true
    };
    
    // Initialize after CleanFileUploader
    document.addEventListener('DOMContentLoaded', function() {
        // Small delay to ensure CleanFileUploader is initialized first
        setTimeout(initScannerIntegration, 200);
    });
    
    // Logging functions
    function log(message, data) {
        if (config.debug) {
            console.log(`[TicketScannerIntegration] ${message}`, data ? data : '');
        }
    }
    
    function error(message, data) {
        console.error(`[TicketScannerIntegration] ${message}`, data ? data : '');
    }
    
    // Main initialization
    function initScannerIntegration() {
        log('Initializing Ticket Scanner Integration');
        
        if (!window.CleanFileUploader) {
            error('CleanFileUploader component not found. Integration aborted.');
            return;
        }
        
        // Hook into the existing UI
        attachEventHandlers();
        initExistingComponents();
        
        log('Ticket Scanner Integration initialized successfully');
    }
    
    function attachEventHandlers() {
        // Get primary elements
        const scanButton = document.getElementById(config.scanButton);
        const loadingElement = document.getElementById(config.loadingElement);
        const resultsContainer = document.getElementById(config.resultsContainer);
        
        if (!scanButton) {
            error('Scan button not found. Integration aborted.');
            return;
        }
        
        // Set loading element to hidden initially
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
        // Override the default ticket form submission
        const ticketForm = document.getElementById('ticket-form');
        if (ticketForm) {
            // Remove any existing event listeners
            const cloned = ticketForm.cloneNode(true);
            ticketForm.parentNode.replaceChild(cloned, ticketForm);
            
            // Add our new event listener
            cloned.addEventListener('submit', function(e) {
                e.preventDefault();
                log('Form submission intercepted');
                
                // Let clean file uploader handle the upload
                if (window.CleanFileUploader) {
                    window.CleanFileUploader.upload();
                }
                
                return false;
            });
        }
        
        // Register our function to handle ticket scan results
        window.handleTicketScanResults = processTicketScanResults;
        
        log('Event handlers attached successfully');
    }
    
    function initExistingComponents() {
        // Hide any lingering overlays
        const resultOverlays = document.querySelectorAll('.results-overlay');
        if (resultOverlays) {
            resultOverlays.forEach(overlay => {
                overlay.style.display = 'none';
            });
        }
        
        // Set up dual ad manager
        if (window.DualAdManager && !window.DualAdManager.initialized) {
            window.DualAdManager.init();
        }
    }
    
    function showLoadingIndicator() {
        const loadingElement = document.getElementById(config.loadingElement);
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
    }
    
    function hideLoadingIndicator() {
        const loadingElement = document.getElementById(config.loadingElement);
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    function showError(message) {
        const errorElement = document.getElementById(config.errorElement);
        const errorText = document.getElementById(config.errorText);
        const resultsContainer = document.getElementById(config.resultsContainer);
        
        if (errorElement && errorText) {
            errorText.textContent = message;
            errorElement.classList.remove('d-none');
        }
        
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
        }
    }
    
    function processTicketScanResults(response) {
        log('Processing scan results', response);
        hideLoadingIndicator();
        
        // Elements
        const resultsContainer = document.getElementById(config.resultsContainer);
        
        // If results container doesn't exist, nothing to do
        if (!resultsContainer) {
            error('Results container not found');
            return;
        }
        
        // Handle errors first
        if (response.error) {
            showError(response.error);
            return;
        }
        
        // Make sure results are visible
        resultsContainer.classList.remove('d-none');
        
        // Hide error message if shown previously
        const errorElement = document.getElementById(config.errorElement);
        if (errorElement) {
            errorElement.classList.add('d-none');
        }
        
        // Get ticket information
        const ticketInfo = response.ticket_info || {};
        
        // Update result information
        updateTicketInfo(ticketInfo);
        
        // Update winning numbers display
        updateWinningNumbers(response);
        
        // Check and display prize information
        updatePrizeInfo(response);
        
        // Scroll to results
        setTimeout(() => {
            resultsContainer.scrollIntoView({behavior: 'smooth', block: 'start'});
        }, 100);
    }
    
    function updateTicketInfo(ticketInfo) {
        // Update ticket information
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element && value) {
                element.textContent = value;
            }
        };
        
        // Update basic ticket info
        updateElement('result-lottery-type', ticketInfo.lottery_type || '');
        updateElement('result-draw-number', ticketInfo.draw_number || '');
        updateElement('result-draw-date', ticketInfo.draw_date || '');
        
        // Update detected info if available
        updateElement('detected-game-type', ticketInfo.game_type || '');
        updateElement('detected-draw-number', ticketInfo.draw_number || '');
        updateElement('detected-draw-date', ticketInfo.draw_date || '');
        
        // Update ticket numbers display
        const ticketNumbersContainer = document.getElementById('ticket-numbers');
        if (ticketNumbersContainer && ticketInfo.ticket_numbers) {
            ticketNumbersContainer.innerHTML = '';
            
            // Check if we have multi-row ticket info
            const rawTicketInfo = ticketInfo.raw_ticket_info;
            if (rawTicketInfo && Object.keys(rawTicketInfo).length > 0) {
                // Multi-row ticket
                let rowsHtml = '';
                for (const [rowName, numbers] of Object.entries(rawTicketInfo)) {
                    rowsHtml += `
                        <div class="ticket-row mb-2">
                            <div class="d-flex align-items-center">
                                <span class="row-label me-2">${rowName}:</span>
                                <div class="d-inline-flex flex-wrap">
                                    ${numbers.map(n => `<span class="lottery-ball">${n}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                    `;
                }
                ticketNumbersContainer.innerHTML = rowsHtml;
            } else {
                // Simple single-row ticket
                ticketNumbersContainer.innerHTML = ticketInfo.ticket_numbers
                    .map(n => `<span class="lottery-ball">${n}</span>`)
                    .join('');
            }
        }
    }
    
    function updateWinningNumbers(response) {
        // Elements
        const winningNumbersContainer = document.getElementById('winning-numbers');
        const primaryGameLabel = document.getElementById('primary-game-label');
        
        // Update winning numbers
        if (winningNumbersContainer && response.winning_numbers) {
            // Clear existing content
            winningNumbersContainer.innerHTML = '';
            
            // Add main numbers
            response.winning_numbers.forEach(number => {
                const ballElement = document.createElement('span');
                ballElement.className = 'lottery-ball';
                ballElement.textContent = number;
                winningNumbersContainer.appendChild(ballElement);
            });
            
            // Handle bonus number if it exists
            if (response.bonus_numbers && response.bonus_numbers.length > 0) {
                // Check if we should call it Powerball or Bonus Ball
                const isPowerball = (response.ticket_info && 
                                   response.ticket_info.lottery_type && 
                                   response.ticket_info.lottery_type.toLowerCase().includes('powerball'));
                
                // Add separator
                const separator = document.createElement('span');
                separator.className = 'mx-2 d-inline-block';
                separator.innerHTML = '+';
                winningNumbersContainer.appendChild(separator);
                
                // Add bonus ball with special styling
                const bonusBall = document.createElement('span');
                bonusBall.className = isPowerball ? 'lottery-ball powerball-ball' : 'lottery-ball bonus-ball';
                bonusBall.textContent = response.bonus_numbers[0];
                winningNumbersContainer.appendChild(bonusBall);
                
                // Update primary game label if needed
                if (primaryGameLabel) {
                    primaryGameLabel.textContent = isPowerball ? 'Powerball Numbers:' : 'Main Numbers:';
                }
            }
        }
        
        // Update matched numbers display
        updateMatchedNumbers(response);
        
        // Update any additional game containers
        updateAdditionalGames(response);
    }
    
    function updateMatchedNumbers(response) {
        // Update match count
        const matchedCountElement = document.getElementById('matched-count');
        if (matchedCountElement && response.matched_count !== undefined) {
            matchedCountElement.textContent = response.matched_count;
            
            // Update styling based on matches
            if (response.matched_count > 0) {
                matchedCountElement.classList.remove('bg-secondary');
                matchedCountElement.classList.add('bg-success');
            } else {
                matchedCountElement.classList.remove('bg-success');
                matchedCountElement.classList.add('bg-secondary');
            }
        }
        
        // Update matched numbers visualization
        const matchedNumbersContainer = document.getElementById('matched-numbers');
        if (matchedNumbersContainer && response.matched_numbers) {
            matchedNumbersContainer.innerHTML = '';
            
            if (response.matched_numbers.length > 0) {
                response.matched_numbers.forEach(number => {
                    const matchedBall = document.createElement('span');
                    matchedBall.className = 'lottery-ball matched-ball';
                    matchedBall.textContent = number;
                    matchedNumbersContainer.appendChild(matchedBall);
                });
            } else {
                matchedNumbersContainer.innerHTML = '<p class="text-muted">No matches found</p>';
            }
        }
    }
    
    function updateAdditionalGames(response) {
        // Check for Powerball Plus
        const powerballPlusContainer = document.getElementById('powerball-plus-numbers-container');
        if (powerballPlusContainer && response.powerball_plus_results) {
            const ppResults = response.powerball_plus_results;
            
            // Show the container
            powerballPlusContainer.classList.remove('d-none');
            
            // Update numbers
            const ppNumbersContainer = document.getElementById('powerball-plus-numbers');
            if (ppNumbersContainer && ppResults.winning_numbers) {
                ppNumbersContainer.innerHTML = '';
                
                // Add main numbers
                ppResults.winning_numbers.forEach(number => {
                    const ballElement = document.createElement('span');
                    ballElement.className = 'lottery-ball';
                    ballElement.textContent = number;
                    ppNumbersContainer.appendChild(ballElement);
                });
                
                // Add bonus if it exists
                if (ppResults.bonus_numbers && ppResults.bonus_numbers.length > 0) {
                    const separator = document.createElement('span');
                    separator.className = 'mx-2 d-inline-block';
                    separator.innerHTML = '+';
                    ppNumbersContainer.appendChild(separator);
                    
                    const bonusBall = document.createElement('span');
                    bonusBall.className = 'lottery-ball powerball-ball';
                    bonusBall.textContent = ppResults.bonus_numbers[0];
                    ppNumbersContainer.appendChild(bonusBall);
                }
            }
            
            // Update match count
            const ppMatchedCountElement = document.getElementById('pp-matched-count');
            if (ppMatchedCountElement && ppResults.matched_count !== undefined) {
                ppMatchedCountElement.textContent = ppResults.matched_count;
                
                if (ppResults.matched_count > 0) {
                    ppMatchedCountElement.classList.remove('bg-secondary');
                    ppMatchedCountElement.classList.add('bg-success');
                } else {
                    ppMatchedCountElement.classList.remove('bg-success');
                    ppMatchedCountElement.classList.add('bg-secondary');
                }
            }
            
            // Update matched numbers
            const ppMatchedNumbersContainer = document.getElementById('pp-matched-numbers');
            if (ppMatchedNumbersContainer && ppResults.matched_numbers) {
                ppMatchedNumbersContainer.innerHTML = '';
                
                if (ppResults.matched_numbers.length > 0) {
                    ppResults.matched_numbers.forEach(number => {
                        const matchedBall = document.createElement('span');
                        matchedBall.className = 'lottery-ball matched-ball';
                        matchedBall.textContent = number;
                        ppMatchedNumbersContainer.appendChild(matchedBall);
                    });
                } else {
                    ppMatchedNumbersContainer.innerHTML = '<p class="text-muted">No matches found</p>';
                }
            }
        } else if (powerballPlusContainer) {
            powerballPlusContainer.classList.add('d-none');
        }
        
        // Similar logic for Lotto Plus 1
        const lottoPlus1Container = document.getElementById('lotto-plus-1-numbers-container');
        if (lottoPlus1Container && response.lottery_plus_1_results) {
            // Show similar updates as above for Powerball Plus
            lottoPlus1Container.classList.remove('d-none');
            // Further implementation similar to above
        } else if (lottoPlus1Container) {
            lottoPlus1Container.classList.add('d-none');
        }
        
        // Similar logic for Lotto Plus 2
        const lottoPlus2Container = document.getElementById('lotto-plus-2-numbers-container');
        if (lottoPlus2Container && response.lottery_plus_2_results) {
            // Show similar updates as above for Powerball Plus
            lottoPlus2Container.classList.remove('d-none');
            // Further implementation similar to above
        } else if (lottoPlus2Container) {
            lottoPlus2Container.classList.add('d-none');
        }
    }
    
    function updatePrizeInfo(response) {
        const prizeContainer = document.getElementById('prize-container');
        const noPrizeContainer = document.getElementById('no-prize-container');
        
        if (!prizeContainer || !noPrizeContainer) {
            error('Prize containers not found');
            return;
        }
        
        // Check if the player has won a prize
        if (response.has_prize && response.prize_info) {
            // Show prize container
            prizeContainer.classList.remove('d-none');
            noPrizeContainer.classList.add('d-none');
            
            // Update prize information
            const prizeInfo = response.prize_info;
            
            document.getElementById('prize-lottery-type').textContent = response.ticket_info?.lottery_type || '';
            document.getElementById('prize-draw-number').textContent = response.ticket_info?.draw_number || '';
            document.getElementById('prize-division').textContent = prizeInfo.division || '';
            document.getElementById('prize-match-type').textContent = prizeInfo.match_description || '';
            document.getElementById('prize-amount').textContent = prizeInfo.prize_amount || '';
            
            // Show prize description if available
            const prizeDescContainer = document.getElementById('prize-description-container');
            if (prizeDescContainer && prizeInfo.description) {
                prizeDescContainer.classList.remove('d-none');
                document.getElementById('prize-description').textContent = prizeInfo.description;
            } else if (prizeDescContainer) {
                prizeDescContainer.classList.add('d-none');
            }
        } else {
            // Show no prize container
            prizeContainer.classList.add('d-none');
            noPrizeContainer.classList.remove('d-none');
            
            // Update basic info in no prize container
            const ticketInfo = response.ticket_info || {};
            const noPrizeLotteryType = document.getElementById('no-prize-lottery-type');
            const noPrizeDrawNumber = document.getElementById('no-prize-draw-number');
            
            if (noPrizeLotteryType) {
                noPrizeLotteryType.textContent = ticketInfo.lottery_type || '';
            }
            
            if (noPrizeDrawNumber) {
                noPrizeDrawNumber.textContent = ticketInfo.draw_number || '';
            }
        }
    }
    
    // DualAdManager for showing ads with results
    window.DualAdManager = {
        initialized: false,
        
        init: function() {
            log('Initializing DualAdManager');
            this.initialized = true;
        },
        
        showResultsWithAd: function(results) {
            log('Showing results with advertisement');
            
            // Show ad overlay
            const adOverlay = document.querySelector('.results-overlay');
            if (adOverlay) {
                adOverlay.style.display = 'flex';
                document.body.style.overflow = 'hidden';
                
                // Set timeout to auto-close overlay after 10 seconds
                setTimeout(() => {
                    this.closeAdOverlay();
                    // Process results
                    processTicketScanResults(results);
                }, 8000);
            } else {
                // If overlay doesn't exist, just process results immediately
                processTicketScanResults(results);
            }
        },
        
        closeAdOverlay: function() {
            const adOverlay = document.querySelector('.results-overlay');
            if (adOverlay) {
                adOverlay.style.display = 'none';
                document.body.style.overflow = '';
            }
        }
    };
})();