// Results Display Module
// Handles the display of scan results and animations

// Initialize on DOM load to avoid duplication errors
document.addEventListener('DOMContentLoaded', function() {
    console.log("Results display module loaded");
    
    // Track if results are currently visible
    window.resultsVisible = false;
    
    // Get the fixed results wrapper reference only once
    const resultsWrapper = document.getElementById('fixed-results-wrapper');
    const resultsContent = document.getElementById('fixed-results-content');
    
    // Global function to show results - can be called from other scripts
    window.showScanResults = function(jsonData) {
        console.log("showScanResults called with data:", typeof jsonData);
        
        try {
            // Parse the data if it's a string
            const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;
            
            // Ensure we have valid data
            if (!data || typeof data !== 'object') {
                console.error("Invalid results data received");
                showError("Invalid results data received. Please try again.");
                return;
            }
            
            // Update lottery type display
            updateLotteryType(data.lottery_type);
            
            // Create and display ball numbers
            displayWinningNumbers(data);
            displayTicketNumbers(data);
            
            // Show match indicators
            highlightMatches(data);
            
            // Show prize information if available
            displayPrizeInfo(data);
            
            // Handle additional games (Powerball Plus, Lotto Plus 1, etc.)
            handleAdditionalGames(data);
            
            // Make the results visible
            showFixedResults();
            
            console.log("Results display completed successfully");
        } catch (error) {
            console.error("Error displaying results:", error);
            showError("Error displaying results: " + error.message);
        }
    };
    
    // Show the fixed results container with proper animation
    function showFixedResults() {
        if (!resultsWrapper) {
            console.error("Fixed results wrapper not found");
            return;
        }
        
        // Hide loading indicator if visible
        const loadingIndicator = document.getElementById('scanner-loading');
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
        
        // Show success content
        const successContent = document.getElementById('success-content');
        if (successContent) {
            successContent.classList.remove('d-none');
            successContent.style.display = 'block';
        }
        
        // Show the fixed wrapper with animation
        resultsWrapper.classList.remove('d-none');
        resultsWrapper.style.display = 'block';
        
        // Force a reflow for animation to take effect
        resultsWrapper.offsetHeight;
        
        // Add the fixed-content class to body for proper scrolling
        document.body.classList.add('fixed-content');
        
        // Mark results as visible
        window.resultsVisible = true;
        
        console.log("Fixed results now visible");
    }
    
    // Show error message
    window.showError = function(message) {
        console.error("Error:", message);
        
        // Hide loading indicator
        const loadingIndicator = document.getElementById('scanner-loading');
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
        
        // Show error message
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('d-none');
            errorElement.style.display = 'block';
        }
    };
    
    // Update lottery type display
    function updateLotteryType(lotteryType) {
        const typeDisplay = document.getElementById('lottery-type-display');
        if (typeDisplay && lotteryType) {
            typeDisplay.textContent = lotteryType;
        }
    }
    
    // Display winning numbers with animation
    function displayWinningNumbers(data) {
        if (!data.winning_numbers || !data.winning_numbers.length) {
            console.error("No winning numbers found in data");
            return;
        }
        
        const container = document.getElementById('winning-numbers');
        if (!container) {
            console.error("Winning numbers container not found");
            return;
        }
        
        // Clear previous content
        container.innerHTML = '';
        
        // Create and append balls for each number
        data.winning_numbers.forEach((number) => {
            const ball = createBallElement(number, 'winning-ball');
            container.appendChild(ball);
        });
        
        // Add bonus number if present
        if (data.bonus_numbers && data.bonus_numbers.length) {
            const bonusContainer = document.createElement('div');
            bonusContainer.className = 'bonus-container';
            
            const bonusLabel = document.createElement('span');
            bonusLabel.className = 'bonus-label';
            bonusLabel.textContent = 'Bonus:';
            bonusContainer.appendChild(bonusLabel);
            
            data.bonus_numbers.forEach(bonus => {
                const bonusBall = createBallElement(bonus, 'bonus-ball');
                bonusContainer.appendChild(bonusBall);
            });
            
            container.appendChild(bonusContainer);
        }
    }
    
    // Display ticket numbers
    function displayTicketNumbers(data) {
        if (!data.ticket_numbers || !data.ticket_numbers.length) {
            console.error("No ticket numbers found in data");
            return;
        }
        
        const container = document.getElementById('ticket-numbers');
        if (!container) {
            console.error("Ticket numbers container not found");
            return;
        }
        
        // Clear previous content
        container.innerHTML = '';
        
        // Get rows if available
        const rows = data.rows_with_matches || [];
        
        // If we have structured rows, display them
        if (rows.length > 0) {
            rows.forEach(row => {
                const rowContainer = document.createElement('div');
                rowContainer.className = 'ticket-row';
                
                // Row label
                const rowLabel = document.createElement('div');
                rowLabel.className = 'row-label';
                rowLabel.textContent = row.row || '';
                rowContainer.appendChild(rowLabel);
                
                // Row numbers
                const numbersContainer = document.createElement('div');
                numbersContainer.className = 'row-numbers';
                
                row.numbers.forEach((num, index) => {
                    const isBonus = index === row.numbers.length - 1;
                    const isMatched = row.matched_numbers.includes(num) || 
                                      (isBonus && row.matched_bonus.includes(num));
                    
                    const ballClass = isBonus ? 'bonus-ball' : 'ticket-ball';
                    const ball = createBallElement(num, ballClass, isMatched);
                    numbersContainer.appendChild(ball);
                });
                
                rowContainer.appendChild(numbersContainer);
                container.appendChild(rowContainer);
            });
        } else {
            // Simple display of all numbers
            data.ticket_numbers.forEach((number, index) => {
                const isMatch = data.matched_numbers.includes(number);
                const ball = createBallElement(number, 'ticket-ball', isMatch);
                container.appendChild(ball);
            });
        }
    }
    
    // Highlight matches between ticket and winning numbers
    function highlightMatches(data) {
        console.log("Highlighting matches");
        
        // Show match count
        const matchCountElement = document.getElementById('match-count');
        if (matchCountElement) {
            matchCountElement.textContent = data.total_matched || 0;
        }
        
        // Display has prize message
        const prizeContainer = document.getElementById('prize-container');
        const noPrizeContainer = document.getElementById('no-prize-container');
        
        if (data.has_prize) {
            if (prizeContainer) prizeContainer.classList.remove('d-none');
            if (noPrizeContainer) noPrizeContainer.classList.add('d-none');
        } else {
            if (prizeContainer) prizeContainer.classList.add('d-none');
            if (noPrizeContainer) noPrizeContainer.classList.remove('d-none');
        }
    }
    
    // Display prize information if available
    function displayPrizeInfo(data) {
        if (!data.prize_info || Object.keys(data.prize_info).length === 0) {
            console.log("No prize information available");
            return;
        }
        
        const prizeInfoContainer = document.getElementById('prize-details');
        if (!prizeInfoContainer) {
            console.error("Prize info container not found");
            return;
        }
        
        // Clear previous content
        prizeInfoContainer.innerHTML = '';
        
        // Create and add prize information
        for (const [division, info] of Object.entries(data.prize_info)) {
            const divisionElement = document.createElement('div');
            divisionElement.className = 'prize-division';
            divisionElement.innerHTML = `
                <div class="division-name">${division}</div>
                <div class="division-amount">${info.amount || ''}</div>
                <div class="division-winners">${info.winners || 0} winners</div>
            `;
            prizeInfoContainer.appendChild(divisionElement);
        }
    }
    
    // Handle additional games like Powerball Plus, Lotto Plus 1, etc.
    function handleAdditionalGames(data) {
        // Handle Powerball Plus
        if (data.powerball_plus_results) {
            displayAdditionalGame(
                data.powerball_plus_results,
                'powerball-plus-section',
                'powerball-plus-numbers-container'
            );
        }
        
        // Handle Lotto Plus 1
        if (data.lotto_plus_1_results) {
            displayAdditionalGame(
                data.lotto_plus_1_results,
                'lotto-plus-1-section',
                'lotto-plus-1-numbers-container'
            );
        }
        
        // Handle Lotto Plus 2
        if (data.lotto_plus_2_results) {
            displayAdditionalGame(
                data.lotto_plus_2_results,
                'lotto-plus-2-section',
                'lotto-plus-2-numbers-container'
            );
        }
    }
    
    // Display an additional game's results
    function displayAdditionalGame(gameData, sectionId, containerId) {
        const section = document.getElementById(sectionId);
        if (!section) {
            console.error(`Section not found: ${sectionId}`);
            return;
        }
        
        // Show the section
        section.classList.remove('d-none');
        section.style.display = 'block';
        
        // Update content
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container not found: ${containerId}`);
            return;
        }
        
        // Clear previous content
        container.innerHTML = '';
        
        // Display game type
        const typeDisplay = section.querySelector('.additional-game-type');
        if (typeDisplay) {
            typeDisplay.textContent = gameData.lottery_type || '';
        }
        
        // Display winning numbers
        const winningContainer = document.createElement('div');
        winningContainer.className = 'winning-numbers-container';
        
        const winningLabel = document.createElement('div');
        winningLabel.className = 'numbers-label';
        winningLabel.textContent = 'Winning Numbers:';
        winningContainer.appendChild(winningLabel);
        
        const winningBalls = document.createElement('div');
        winningBalls.className = 'balls-container';
        
        // Add winning balls
        gameData.winning_numbers.forEach(number => {
            const ball = createBallElement(number, 'winning-ball');
            winningBalls.appendChild(ball);
        });
        
        // Add bonus if present
        if (gameData.bonus_numbers && gameData.bonus_numbers.length) {
            const bonusContainer = document.createElement('div');
            bonusContainer.className = 'bonus-container';
            
            const bonusLabel = document.createElement('span');
            bonusLabel.className = 'bonus-label';
            bonusLabel.textContent = 'Bonus:';
            bonusContainer.appendChild(bonusLabel);
            
            gameData.bonus_numbers.forEach(bonus => {
                const bonusBall = createBallElement(bonus, 'bonus-ball');
                bonusContainer.appendChild(bonusBall);
            });
            
            winningBalls.appendChild(bonusContainer);
        }
        
        winningContainer.appendChild(winningBalls);
        container.appendChild(winningContainer);
        
        // Show match results
        const matchContainer = document.createElement('div');
        matchContainer.className = 'match-container';
        
        // Match count
        const matchCountElement = document.createElement('div');
        matchCountElement.className = 'match-count-container';
        matchCountElement.innerHTML = `
            <span class="match-label">Matches:</span>
            <span class="match-number">${gameData.total_matched || 0}</span>
        `;
        matchContainer.appendChild(matchCountElement);
        
        // Prize status
        if (gameData.has_prize) {
            const prizeElement = document.createElement('div');
            prizeElement.className = 'prize-status win';
            prizeElement.textContent = 'You won a prize!';
            matchContainer.appendChild(prizeElement);
        } else {
            const noPrizeElement = document.createElement('div');
            noPrizeElement.className = 'prize-status no-win';
            noPrizeElement.textContent = 'No prize for this game';
            matchContainer.appendChild(noPrizeElement);
        }
        
        container.appendChild(matchContainer);
        
        // If there are rows with matches, display them
        if (gameData.rows_with_matches && gameData.rows_with_matches.length) {
            const rowsContainer = document.createElement('div');
            rowsContainer.className = 'ticket-rows-container';
            
            const rowsLabel = document.createElement('div');
            rowsLabel.className = 'numbers-label';
            rowsLabel.textContent = 'Your Numbers:';
            rowsContainer.appendChild(rowsLabel);
            
            gameData.rows_with_matches.forEach(row => {
                const rowElement = document.createElement('div');
                rowElement.className = 'ticket-row';
                
                // Row label
                const rowLabel = document.createElement('div');
                rowLabel.className = 'row-label';
                rowLabel.textContent = row.row || '';
                rowElement.appendChild(rowLabel);
                
                // Numbers
                const numbersContainer = document.createElement('div');
                numbersContainer.className = 'row-numbers';
                
                row.numbers.forEach((num, index) => {
                    const isBonus = index === row.numbers.length - 1;
                    const isMatched = row.matched_numbers.includes(num) || 
                                      (isBonus && row.matched_bonus && row.matched_bonus.includes(num));
                    
                    const ballClass = isBonus ? 'bonus-ball' : 'ticket-ball';
                    const ball = createBallElement(num, ballClass, isMatched);
                    numbersContainer.appendChild(ball);
                });
                
                rowElement.appendChild(numbersContainer);
                rowsContainer.appendChild(rowElement);
            });
            
            container.appendChild(rowsContainer);
        }
    }
    
    // Helper function to create a ball element
    function createBallElement(number, className, isMatched = false) {
        const ball = document.createElement('div');
        ball.className = `ball ${className}`;
        ball.dataset.number = number;
        
        const numberSpan = document.createElement('span');
        numberSpan.className = 'ball-number';
        numberSpan.textContent = number;
        ball.appendChild(numberSpan);
        
        // Add match indicator if matched
        if (isMatched) {
            ball.classList.add('matched');
            const checkmark = document.createElement('div');
            checkmark.className = 'match-indicator';
            ball.appendChild(checkmark);
        }
        
        return ball;
    }
    
    // Add close button event handler
    const closeButton = document.getElementById('close-results');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            hideResults();
        });
    }
    
    // Function to hide results
    function hideResults() {
        if (resultsWrapper) {
            resultsWrapper.classList.add('d-none');
            resultsWrapper.style.display = 'none';
        }
        
        // Remove fixed content class from body
        document.body.classList.remove('fixed-content');
        
        // Mark results as hidden
        window.resultsVisible = false;
        
        console.log("Results hidden");
    }
    
    // Export additional functions to window for external use
    window.hideResults = hideResults;
});