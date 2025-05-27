/**
 * Enhanced File Input Handler for Ticket Scanner
 * 
 * This script improves the file selection and submission functionality for the ticket scanner,
 * with enhanced error handling and user feedback.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Core elements
    const fileInput = document.getElementById('ticket-image');
    const fileSelectBtn = document.getElementById('file-select-btn');
    const previewContainer = document.getElementById('preview-container');
    const ticketPreview = document.getElementById('ticket-preview');
    const removeImageBtn = document.getElementById('remove-image');
    const scanButton = document.getElementById('scan-button');
    const ticketForm = document.getElementById('ticket-form');
    const resultsContainer = document.getElementById('results-container');
    const loadingIndicator = document.getElementById('scanner-loading');
    
    // Make sure the button triggers the file input
    if (fileSelectBtn && fileInput) {
        fileSelectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fileInput.click();
            console.log('File input activated');
        });
    }
    
    // Handle file selection
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files && fileInput.files[0]) {
                const file = fileInput.files[0];
                console.log('File selected:', file.name);
                
                // Show preview if elements exist
                if (previewContainer && ticketPreview) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        ticketPreview.src = e.target.result;
                        previewContainer.classList.remove('d-none');
                        console.log('Preview shown');
                        
                        // Enable scan button once file is selected and previewed
                        if (scanButton) {
                            scanButton.disabled = false;
                        }
                    };
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    }
    
    // Handle image removal
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            if (fileInput) {
                fileInput.value = '';
            }
            
            if (previewContainer) {
                previewContainer.classList.add('d-none');
            }
            
            if (ticketPreview) {
                ticketPreview.src = '';
            }
            
            // Disable scan button when image is removed
            if (scanButton) {
                scanButton.disabled = true;
            }
            
            console.log('Image removed');
        });
    }
    
    // Handle form submission
    if (ticketForm) {
        ticketForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!fileInput.files || !fileInput.files[0]) {
                showError('Please select an image first.');
                return;
            }
            
            // Disable scan button while processing
            if (scanButton) {
                scanButton.disabled = true;
            }
            
            // Show loading indicator
            if (loadingIndicator) {
                loadingIndicator.style.display = 'block';
            }
            
            // Hide results container while processing
            if (resultsContainer) {
                resultsContainer.classList.add('d-none');
            }
            
            // Clear any previous error messages
            const errorMessage = document.getElementById('error-message');
            if (errorMessage) {
                errorMessage.classList.add('d-none');
            }
            
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            // Create form data
            const formData = new FormData(ticketForm);
            
            // Submit form data
            fetch('/process-ticket', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                console.log('Response received:', response.status);
                if (!response.ok) {
                    return response.text().then(text => {
                        console.error('Error response:', text);
                        throw new Error('Server error: ' + response.status + ' - ' + text);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Success processing ticket:', data);
                
                // Enable the scan button again
                if (scanButton) {
                    scanButton.disabled = false;
                }
                
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                if (!data.success) {
                    // Show the specific error from the API
                    showError(data.error || 'Failed to process ticket. Please try again.');
                    return;
                }
                
                // Display results immediately
                displayResults(data);
            })
            .catch(error => {
                console.error('Error processing ticket:', error);
                
                // Enable the scan button again
                if (scanButton) {
                    scanButton.disabled = false;
                }
                
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                // Show detailed error message
                showError('Error processing ticket: ' + error.message);
            });
        });
    }
    
    // Initialize
    console.log('Enhanced file input handler loaded and active');
});

// Helper function to show error messages
function showError(message) {
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const resultsContainer = document.getElementById('results-container');
    
    if (errorMessage && errorText) {
        errorText.innerHTML = message;
        errorMessage.classList.remove('d-none');
    }
    
    if (resultsContainer) {
        resultsContainer.classList.remove('d-none');
        
        // Hide success content if it exists
        const successContent = document.getElementById('success-content');
        if (successContent) {
            successContent.classList.add('d-none');
        }
    }
    
    // Scroll to results container
    if (resultsContainer) {
        resultsContainer.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Function to display results
function displayResults(data) {
    console.log('Displaying ticket scanning results:', data);
    
    const resultsContainer = document.getElementById('results-container');
    
    if (!resultsContainer) {
        console.error('Results container not found');
        return;
    }
    
    // Show results container
    resultsContainer.classList.remove('d-none');
    
    // Hide error message by default
    const errorMessage = document.getElementById('error-message');
    if (errorMessage) {
        errorMessage.classList.add('d-none');
    }
    
    if (data.error) {
        showError(data.error);
        return;
    }
    
    // Show success content
    const successContent = document.getElementById('success-content');
    if (successContent) {
        successContent.classList.remove('d-none');
    } else {
        console.error('Success content container not found');
        return;
    }
    
    // Populate ticket info
    const resultLotteryType = document.getElementById('result-lottery-type');
    if (resultLotteryType) resultLotteryType.textContent = data.lottery_type || 'Unknown';
    
    const resultDrawNumber = document.getElementById('result-draw-number');
    if (resultDrawNumber) resultDrawNumber.textContent = data.draw_number || 'Unknown';
    
    const resultDrawDate = document.getElementById('result-draw-date');
    if (resultDrawDate) resultDrawDate.textContent = data.draw_date || 'Unknown';
    
    // Populate detected information from OCR if available
    if (data.ticket_info) {
        const detectedGameType = document.getElementById('detected-game-type');
        if (detectedGameType) {
            detectedGameType.textContent = data.ticket_info.detected_game_type || 'Unknown';
        }
        
        const detectedDrawNumber = document.getElementById('detected-draw-number');
        if (detectedDrawNumber) {
            detectedDrawNumber.textContent = data.ticket_info.detected_draw_number || 'Unknown';
        }
        
        const detectedDrawDate = document.getElementById('detected-draw-date');
        if (detectedDrawDate) {
            detectedDrawDate.textContent = data.ticket_info.detected_draw_date || 'Unknown';
        }
    } else {
        const detectedInfo = document.getElementById('detected-info');
        if (detectedInfo) {
            detectedInfo.classList.add('d-none');
        }
    }
    
    // Display ticket numbers
    const ticketNumbersContainer = document.getElementById('ticket-numbers');
    if (ticketNumbersContainer) {
        ticketNumbersContainer.innerHTML = '';
        
        // Handle both all_lines (new) and ticket_numbers (old) formats
        let linesToDisplay = [];
        
        if (data.all_lines && Array.isArray(data.all_lines)) {
            linesToDisplay = data.all_lines;
        } else if (data.ticket_numbers && Array.isArray(data.ticket_numbers)) {
            linesToDisplay = [data.ticket_numbers];
        }
        
        if (linesToDisplay.length > 0) {
            // Display each line of numbers from your ticket
            linesToDisplay.forEach((numbers, lineIndex) => {
                if (Array.isArray(numbers)) {
                    // Create row label
                    const rowLabel = document.createElement('div');
                    rowLabel.classList.add('mt-2', 'mb-1');
                    rowLabel.innerHTML = `<strong>Line ${lineIndex + 1} - Main Numbers:</strong>`;
                    ticketNumbersContainer.appendChild(rowLabel);
                    
                    // Create row container
                    const rowContainer = document.createElement('div');
                    rowContainer.classList.add('mb-3', 'd-flex', 'flex-wrap');
                    
                    // Add balls for main numbers
                    numbers.forEach(number => {
                        const ballElement = document.createElement('div');
                        ballElement.classList.add('lottery-ball', 'me-2', 'mb-2');
                    
                    // Check if this number matches a winning number
                    const isMatch = data.winning_numbers && data.winning_numbers.includes(number);
                    const isBonusMatch = data.bonus_numbers && data.bonus_numbers.includes(number);
                    
                    if (isMatch) {
                        ballElement.classList.add('matched');
                    } else if (isBonusMatch) {
                        ballElement.classList.add('bonus-matched');
                    }
                    
                    ballElement.textContent = number;
                    rowContainer.appendChild(ballElement);
                });
                
                ticketNumbersContainer.appendChild(rowContainer);
            });
        } else if (data.ticket_info && data.ticket_info.selected_numbers) {
            // Fallback to the simple array of numbers
            const rowContainer = document.createElement('div');
            rowContainer.classList.add('mb-3', 'd-flex', 'flex-wrap');
            
            data.ticket_info.selected_numbers.forEach(number => {
                const ballElement = document.createElement('div');
                ballElement.classList.add('lottery-ball', 'me-2', 'mb-2');
                
                // Check if this number matches a winning number
                const isMatch = data.winning_numbers && data.winning_numbers.includes(number);
                const isBonusMatch = data.bonus_numbers && data.bonus_numbers.includes(number);
                
                if (isMatch) {
                    ballElement.classList.add('matched');
                } else if (isBonusMatch) {
                    ballElement.classList.add('bonus-matched');
                }
                
                ballElement.textContent = number;
                rowContainer.appendChild(ballElement);
            });
            
            ticketNumbersContainer.appendChild(rowContainer);
        } else if (data.ticket_numbers && Array.isArray(data.ticket_numbers)) {
            // Handle your authentic PowerBall ticket data format
            const rowLabel = document.createElement('div');
            rowLabel.classList.add('mt-2', 'mb-1');
            rowLabel.innerHTML = `<strong>Your Numbers:</strong>`;
            ticketNumbersContainer.appendChild(rowLabel);
            
            const rowContainer = document.createElement('div');
            rowContainer.classList.add('mb-3', 'd-flex', 'flex-wrap');
            
            data.ticket_numbers.forEach(number => {
                const ballElement = document.createElement('div');
                ballElement.classList.add('lottery-ball', 'me-2', 'mb-2');
                ballElement.textContent = number;
                rowContainer.appendChild(ballElement);
            });
            
            ticketNumbersContainer.appendChild(rowContainer);
            
            // Add PowerBall if available
            if (data.powerball_number) {
                const powerballLabel = document.createElement('div');
                powerballLabel.classList.add('mt-3', 'mb-1');
                powerballLabel.innerHTML = `<strong>PowerBall:</strong>`;
                ticketNumbersContainer.appendChild(powerballLabel);
                
                const powerballContainer = document.createElement('div');
                powerballContainer.classList.add('mb-3', 'd-flex', 'flex-wrap');
                
                const ballElement = document.createElement('div');
                ballElement.classList.add('lottery-ball', 'powerball', 'me-2', 'mb-2');
                ballElement.textContent = data.powerball_number;
                powerballContainer.appendChild(ballElement);
                
                ticketNumbersContainer.appendChild(powerballContainer);
            }
        }
    }
    
    // Display winning numbers
    const winningNumbersContainer = document.getElementById('winning-numbers');
    if (winningNumbersContainer && data.winning_numbers) {
        winningNumbersContainer.innerHTML = '';
        
        data.winning_numbers.forEach(number => {
            const ballElement = document.createElement('div');
            ballElement.classList.add('lottery-ball', 'me-2', 'mb-2');
            ballElement.textContent = number;
            winningNumbersContainer.appendChild(ballElement);
        });
    }
    
    // Display bonus numbers
    const bonusNumbersContainer = document.getElementById('bonus-numbers-container');
    if (bonusNumbersContainer && data.bonus_numbers && data.bonus_numbers.length > 0) {
        bonusNumbersContainer.classList.remove('d-none');
        
        const bonusNumbersElement = document.getElementById('bonus-numbers');
        if (bonusNumbersElement) {
            bonusNumbersElement.innerHTML = '';
            
            data.bonus_numbers.forEach(number => {
                const ballElement = document.createElement('div');
                ballElement.classList.add('lottery-ball', 'bonus-ball', 'me-2', 'mb-2');
                ballElement.textContent = number;
                bonusNumbersElement.appendChild(ballElement);
            });
        }
    } else if (bonusNumbersContainer) {
        bonusNumbersContainer.classList.add('d-none');
    }
    
    // Display winning status message
    const winningStatusElement = document.getElementById('winning-status');
    if (winningStatusElement) {
        // Check if there are any matches
        const hasMatches = data.has_matches || false;
        
        if (hasMatches) {
            winningStatusElement.innerHTML = '<span class="text-success"><i class="fas fa-check-circle me-2"></i>This ticket has matching numbers!</span>';
            
            // Add winning details if available
            if (data.matched_count) {
                const winningDetailsElement = document.getElementById('winning-details');
                if (winningDetailsElement) {
                    winningDetailsElement.innerHTML = `<p>You matched ${data.matched_count} number${data.matched_count !== 1 ? 's' : ''}${data.matched_bonus_count > 0 ? ` plus ${data.matched_bonus_count} bonus number${data.matched_bonus_count !== 1 ? 's' : ''}` : ''}.</p>`;
                    winningDetailsElement.classList.remove('d-none');
                }
            }
        } else {
            winningStatusElement.innerHTML = '<span class="text-danger"><i class="fas fa-times-circle me-2"></i>No matching numbers found</span>';
            
            // Hide winning details
            const winningDetailsElement = document.getElementById('winning-details');
            if (winningDetailsElement) {
                winningDetailsElement.classList.add('d-none');
            }
        }
    }
    
    // Scroll to results container
    resultsContainer.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
    
    console.log('Results displayed successfully');
}