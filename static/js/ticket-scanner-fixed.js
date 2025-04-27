// Ticket scanner main JavaScript functionality with improved reliability
// This version fixes the issues with image uploads and scanning

// Add first countdown timer function similar to ticket-submission-handler.js
function initFirstCountdown(seconds) {
    // Create container and add to the first ad overlay
    const adContainer = document.querySelector('#ad-overlay-loading .ad-container-wrapper');
    if (!adContainer) return;
    
    // Create timer element if it doesn't exist
    if (!document.getElementById('first-countdown-container')) {
        const countdownContainer = document.createElement('div');
        countdownContainer.id = 'first-countdown-container';
        countdownContainer.className = 'countdown-container text-center mt-3';
        countdownContainer.style.cssText = 'font-weight: bold; color: #495057; background-color: #f8f9fa; padding: 8px; border-radius: 5px; max-width: 350px; margin: 10px auto;';
        countdownContainer.innerHTML = `
            <div class="countdown-timer">
                <span class="timer-value">${seconds}</span>
                <span class="timer-text">seconds</span>
            </div>
        `;
        
        // Add after the ad container
        adContainer.parentNode.insertBefore(countdownContainer, adContainer.nextSibling);
    }
    
    // Get timer elements
    const countdownContainer = document.getElementById('first-countdown-container');
    const timerElement = countdownContainer.querySelector('.timer-value');
    const timerTextElement = countdownContainer.querySelector('.timer-text');
    
    // Set initial value
    let currentSeconds = seconds;
    timerElement.textContent = currentSeconds;
    timerTextElement.textContent = currentSeconds === 1 ? 'second' : 'seconds';
    
    // Start countdown
    const intervalId = setInterval(() => {
        currentSeconds--;
        
        // Update display
        timerElement.textContent = currentSeconds;
        timerTextElement.textContent = currentSeconds === 1 ? 'second' : 'seconds';
        
        // Apply pulse effect in last 3 seconds
        if (currentSeconds <= 3) {
            timerElement.classList.add('text-danger', 'fw-bold');
            countdownContainer.classList.add('pulse-animation');
        }
        
        // Stop when time is up
        if (currentSeconds <= 0) {
            clearInterval(intervalId);
        }
    }, 1000);
    
    return intervalId;
}

// Initialize necessary elements once the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get all required DOM elements
    const fileInput = document.getElementById('ticket-image');
    const previewContainer = document.getElementById('preview-container');
    const ticketPreview = document.getElementById('ticket-preview');
    const scanButton = document.getElementById('scan-button');
    const loadingIndicator = document.getElementById('scanner-loading');
    const resultsContainer = document.getElementById('results-container');
    const lotteryTypeSelect = document.getElementById('lottery-type');
    const dropArea = document.getElementById('drop-area');
    const fileSelectBtn = document.getElementById('file-select-btn');
    const removeImageBtn = document.getElementById('remove-image');
    const scanAnotherButton = document.getElementById('scan-another-ticket');
    
    // Hide loading indicator initially
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
    
    // Set up drag and drop functionality
    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            dropArea.classList.add('highlight');
        }
        
        function unhighlight() {
            dropArea.classList.remove('highlight');
        }
        
        dropArea.addEventListener('drop', handleDrop, false);
    }
    
    // Function to handle dropped files
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelection();
        }
    }
    
    // File selection handler - called when a file is selected
    window.handleFileSelection = function() {
        console.log("File selection handler called");
        
        // Get the selected file
        const file = fileInput.files[0];
        
        if (file) {
            console.log("File selected:", file.name, "Type:", file.type, "Size:", file.size, "bytes");
            
            // Validate file type
            if (!file.type.match('image.*')) {
                alert('Please select an image file (JPG, PNG, etc.).');
                fileInput.value = '';
                scanButton.disabled = true;
                return;
            }
            
            try {
                // Create a direct object URL instead of using FileReader for better compatibility
                const objectUrl = URL.createObjectURL(file);
                console.log("Created object URL for preview");
                
                // Set the image source directly - with improved error handling
                // Show the preview container immediately
                previewContainer.style.display = 'block';
                previewContainer.classList.remove('d-none');
                
                // Enable the scan button - do this both ways for cross-browser compatibility
                scanButton.disabled = false;
                scanButton.removeAttribute('disabled');
                
                ticketPreview.onload = function() {
                    console.log("Preview image loaded successfully");
                    console.log("Preview displayed and scan button enabled");
                };
                
                ticketPreview.onerror = function(e) {
                    console.error("Error loading preview image", e);
                    
                    // Instead of showing an error alert, try an alternative method
                    // Use FileReader as fallback for better browser compatibility
                    try {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            ticketPreview.src = e.target.result;
                            console.log("Preview image loaded using FileReader fallback");
                            
                            // Make sure the image is visible and properly sized
                            ticketPreview.style.maxWidth = '100%';
                            ticketPreview.style.height = 'auto';
                            ticketPreview.style.display = 'block';
                            
                            // Keep the scan button enabled
                            scanButton.disabled = false;
                            scanButton.removeAttribute('disabled');
                        };
                        reader.readAsDataURL(file);
                    } catch (e2) {
                        console.error("All image preview methods failed:", e2);
                        alert('Error displaying the image. Please try another file.');
                        fileInput.value = '';
                        scanButton.disabled = true;
                    }
                };
                
                // Set the source to trigger the onload event
                try {
                    // Try to load the image using both approaches for maximum compatibility
                    ticketPreview.src = objectUrl;
                    console.log("Set ticket preview source to:", objectUrl);
                    
                    // Also save a backup using FileReader for some browsers
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        // Only use this if the other method failed
                        if (!ticketPreview.complete || ticketPreview.naturalWidth === 0) {
                            console.log("Using FileReader result as fallback");
                            ticketPreview.src = e.target.result;
                        }
                    };
                    reader.readAsDataURL(file);
                } catch (e) {
                    console.error("Error setting image source:", e);
                    // Try an alternative method with FileReader
                    try {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            ticketPreview.src = e.target.result;
                            console.log("Set preview using FileReader after object URL failed");
                        };
                        reader.readAsDataURL(file);
                    } catch (e2) {
                        console.error("All preview methods failed:", e2);
                        alert('Error processing the image file. Please try a different image.');
                        fileInput.value = '';
                        scanButton.disabled = true;
                    }
                }
                
            } catch (e) {
                console.error("Error creating preview:", e);
                alert('Error processing the image file. Please try a different image.');
                fileInput.value = '';
                scanButton.disabled = true;
            }
        } else {
            console.log("No file selected");
            previewContainer.style.display = 'none';
            scanButton.disabled = true;
        }
    };
    
    // Set up remove button handler
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            console.log("Remove button clicked");
            
            // Clear the file input
            fileInput.value = '';
            
            // Clear the image source and revoke the object URL to free memory
            if (ticketPreview.src && ticketPreview.src.startsWith('blob:')) {
                URL.revokeObjectURL(ticketPreview.src);
            }
            ticketPreview.src = '';
            
            // Hide the preview container
            previewContainer.style.display = 'none';
            
            // Disable the scan button
            scanButton.disabled = true;
            
            console.log("Image removed and preview hidden");
        });
    }
    
    // Function to clear previous results
    window.clearPreviousResults = function() {
        console.log("Clearing previous results");
        
        // Hide results container
        if (resultsContainer) {
            resultsContainer.classList.add('d-none');
        }
        
        // Clear previous prize display
        const prizeContainer = document.getElementById('prize-container');
        if (prizeContainer) {
            prizeContainer.classList.add('d-none');
        }
        
        const noPrizeContainer = document.getElementById('no-prize-container');
        if (noPrizeContainer) {
            noPrizeContainer.classList.add('d-none');
        }
        
        // Reset all ball indicators
        document.querySelectorAll('.lottery-ball').forEach(ball => {
            ball.classList.remove('matched');
            const checkmark = ball.querySelector('.checkmark');
            if (checkmark) {
                checkmark.remove();
            }
        });
        
        console.log("Previous results cleared");
    };
    
    // Main ticket processing function with ad display
    window.processTicketWithAds = function() {
        console.log("Processing ticket with ads:", new Date().toISOString());
        
        // Verify we have a file
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            console.error("No file selected!");
            alert("Please select an image first");
            return false;
        }
        
        console.log("File is selected:", fileInput.files[0].name);
        
        // Debug information about form elements
        console.log("CSRF token input:", document.querySelector('input[name="csrf_token"]') ? "Found" : "Not found");
        console.log("Form elements count:", document.querySelectorAll('form input, form select').length);
        
        // Clear any previous results
        clearPreviousResults();
        
        // Disable the scan button
        const scanButton = document.getElementById('scan-button');
        if (scanButton) {
            scanButton.disabled = true;
        }
        
        // Hide the normal loading indicator 
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        
        // IMMEDIATELY show the first ad overlay with yellow badge
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading) {
            // Add active class to make it visible
            adOverlayLoading.classList.add('active');
            console.log('FIRST ad overlay (yellow badge) is now visible');
            
            // Start the first countdown timer - 5 seconds
            if (typeof initFirstCountdown === 'function') {
                initFirstCountdown(5);
            } else {
                console.log("initFirstCountdown function not found, using fallback timer");
                // Simple fallback countdown
                let countdownContainer = document.createElement('div');
                countdownContainer.id = 'first-countdown-container';
                countdownContainer.className = 'countdown-container text-center mt-3';
                countdownContainer.style.cssText = 'font-weight: bold; color: #495057; background-color: #f8f9fa; padding: 8px; border-radius: 5px; max-width: 350px; margin: 10px auto;';
                countdownContainer.innerHTML = '<div class="countdown-timer"><span class="timer-value">5</span> <span class="timer-text">seconds</span></div>';
                
                // Add after the ad container
                const adContainer = document.querySelector('#ad-overlay-loading .ad-container-wrapper');
                if (adContainer) {
                    adContainer.parentNode.insertBefore(countdownContainer, adContainer.nextSibling);
                    
                    // Simple countdown
                    let seconds = 5;
                    const timerInterval = setInterval(() => {
                        seconds--;
                        const timerValue = countdownContainer.querySelector('.timer-value');
                        const timerText = countdownContainer.querySelector('.timer-text');
                        if (timerValue) timerValue.textContent = seconds;
                        if (timerText) timerText.textContent = seconds === 1 ? 'second' : 'seconds';
                        
                        if (seconds <= 0) {
                            clearInterval(timerInterval);
                        }
                    }, 1000);
                }
            }
        }
        
        // Get lottery type
        const lotteryType = lotteryTypeSelect ? lotteryTypeSelect.value : '';
        
        // Create form data
        const formData = new FormData();
        formData.append('ticket_image', fileInput.files[0]);
        formData.append('lottery_type', lotteryType);
        
        // Add CSRF token from the hidden input field
        const csrfTokenInput = document.querySelector('input[name="csrf_token"]');
        if (csrfTokenInput) {
            formData.append('csrf_token', csrfTokenInput.value);
        }
        
        // Submit the form data
        console.log("Submitting form data to /scan-ticket");
        
        // Log what's being submitted
        console.log("FormData contents:");
        for (let pair of formData.entries()) {
            console.log(pair[0] + ': ' + (pair[0] === 'ticket_image' ? 'Image file' : pair[1]));
        }
        
        fetch('/scan-ticket', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            console.log("Received response:", response.status);
            if (!response.ok) {
                throw new Error(`Network response error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Received scan result:", data);
            
            // Store the results for later display
            window.ticketResults = data;
            
            // First ad was displayed when form was submitted
            // After 5 seconds, transition to second ad
            setTimeout(function() {
                console.log('First ad (yellow badge) completed - 5 seconds elapsed');
                
                // Hide the first ad overlay
                if (adOverlayLoading) {
                    adOverlayLoading.classList.remove('active');
                    console.log('First ad overlay hidden');
                }
                
                // Show the second ad overlay (blue badge)
                const adOverlayResults = document.getElementById('ad-overlay-results');
                if (adOverlayResults) {
                    // Add active class to make it visible
                    adOverlayResults.classList.add('active');
                    console.log('SECOND ad overlay (blue badge) is now visible');
                    
                    // Initially hide the View Results button and the helper text until countdown completes
                    const viewResultsBtn = document.getElementById('view-results-btn');
                    const viewResultsHelper = document.querySelector('#ad-overlay-results .text-center.mt-4.mb-1');
                    
                    if (viewResultsBtn) {
                        viewResultsBtn.disabled = true;
                        viewResultsBtn.style.display = 'none';
                    }
                    
                    if (viewResultsHelper) {
                        viewResultsHelper.style.display = 'none';
                    }
                    
                    // Show countdown timer in the second ad screen
                    const countdownContainer = document.getElementById('countdown-container');
                    if (countdownContainer) {
                        // Initialize a 15-second countdown
                        let seconds = 15;
                        countdownContainer.innerHTML = `
                            <div class="countdown-timer">
                                <span class="timer-value">${seconds}</span>
                                <span class="timer-text">seconds</span>
                            </div>
                        `;
                        
                        const timerElement = countdownContainer.querySelector('.timer-value');
                        const timerTextElement = countdownContainer.querySelector('.timer-text');
                        
                        // Make countdown visible
                        countdownContainer.style.display = 'block';
                        
                        // Start timer countdown
                        const timerInterval = setInterval(() => {
                            seconds--;
                            
                            // Update display
                            if (timerElement && timerTextElement) {
                                timerElement.textContent = seconds;
                                timerTextElement.textContent = seconds === 1 ? 'second' : 'seconds';
                                
                                // Apply pulse effect in last 3 seconds
                                if (seconds <= 3) {
                                    timerElement.classList.add('text-danger', 'fw-bold');
                                    countdownContainer.classList.add('pulse-animation');
                                }
                            }
                            
                            // When countdown completes
                            if (seconds <= 0) {
                                clearInterval(timerInterval);
                                
                                // Show completion message
                                countdownContainer.innerHTML = '<span class="text-success"><i class="fas fa-check-circle me-1"></i> Ready to view results!</span>';
                                
                                // Show the View Results button and helper text
                                if (viewResultsBtn) {
                                    viewResultsBtn.disabled = false;
                                    viewResultsBtn.style.display = 'block'; 
                                    viewResultsBtn.classList.add('btn-pulse');
                                    
                                    // Also display the helper text with arrow pointing to the button
                                    if (viewResultsHelper) {
                                        viewResultsHelper.style.display = 'block';
                                    }
                                    
                                    // Make sure the event listener is only added once
                                    if (!viewResultsBtn._clickHandlerAdded) {
                                        viewResultsBtn._clickHandlerAdded = true;
                                        
                                        viewResultsBtn.addEventListener('click', function(e) {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            
                                            console.log('View Results button clicked');
                                            
                                            // Hide the overlay immediately when button is clicked using class
                                            adOverlayResults.classList.remove('active');
                                            
                                            // Show the actual results
                                            displayResults(window.ticketResults);
                                        });
                                    }
                                }
                            }
                        }, 1000);
                    } else {
                        console.error('Countdown container not found!');
                        // Fallback: Just show button after 15 seconds
                        setTimeout(() => {
                            if (viewResultsBtn) {
                                viewResultsBtn.disabled = false;
                                viewResultsBtn.style.display = 'block';
                                viewResultsBtn.classList.add('btn-pulse');
                                
                                // Also display the helper text in fallback case
                                if (viewResultsHelper) {
                                    viewResultsHelper.style.display = 'block';
                                }
                                
                                // Add click handler
                                viewResultsBtn.addEventListener('click', function() {
                                    adOverlayResults.classList.remove('active');
                                    displayResults(window.ticketResults);
                                });
                            } else {
                                // Ultimate fallback if even button isn't found
                                adOverlayResults.classList.remove('active');
                                displayResults(window.ticketResults);
                            }
                        }, 15000);
                    }
                } else {
                    console.error('Second ad overlay not found!');
                    // Fallback display results directly
                    displayResults(window.ticketResults);
                }
            }, 5000); // 5 seconds for first ad
        })
        .catch(error => {
            console.error("Error processing ticket:", error);
            
            // Hide the ad overlays using classes
            if (adOverlayLoading) adOverlayLoading.classList.remove('active');
            const adOverlayResults = document.getElementById('ad-overlay-results');
            if (adOverlayResults) adOverlayResults.classList.remove('active');
            
            // Show error message
            const errorMessage = document.getElementById('error-message');
            const errorText = document.getElementById('error-text');
            if (errorMessage && errorText) {
                errorText.textContent = 'Error processing your ticket: ' + error.message;
                errorMessage.classList.remove('d-none');
            } else {
                alert('Error processing your ticket: ' + error.message);
            }
            
            // Re-enable the scan button
            if (scanButton) {
                scanButton.disabled = false;
            }
        });
    };
    
    // Function to display results
    window.displayResults = function(data) {
        console.log("Displaying results:", data);
        
        // Show results container
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
            
            // Scroll to results
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        // Display ticket info
        if (data.ticket_info) {
            // Set lottery type
            const resultLotteryType = document.getElementById('result-lottery-type');
            if (resultLotteryType) {
                resultLotteryType.textContent = data.ticket_info.game_type || lotteryTypeSelect.value || 'Unknown';
            }
            
            // Set draw number
            const resultDrawNumber = document.getElementById('result-draw-number');
            if (resultDrawNumber) {
                resultDrawNumber.textContent = data.ticket_info.draw_number || 'Unknown';
            }
            
            // Set draw date
            const resultDrawDate = document.getElementById('result-draw-date');
            if (resultDrawDate) {
                resultDrawDate.textContent = data.ticket_info.draw_date || 'Unknown';
            }
            
            // Show OCR detected info
            const detectedGameType = document.getElementById('detected-game-type');
            if (detectedGameType) {
                detectedGameType.textContent = data.ticket_info.game_type || 'Unknown';
            }
            
            const detectedDrawNumber = document.getElementById('detected-draw-number');
            if (detectedDrawNumber) {
                detectedDrawNumber.textContent = data.ticket_info.draw_number || 'Unknown';
            }
            
            const detectedDrawDate = document.getElementById('detected-draw-date');
            if (detectedDrawDate) {
                detectedDrawDate.textContent = data.ticket_info.draw_date || 'Unknown';
            }
            
            // Display ticket numbers
            const ticketNumbersContainer = document.getElementById('ticket-numbers');
            if (ticketNumbersContainer) {
                ticketNumbersContainer.innerHTML = ''; // Clear previous
                
                // Get the selected numbers from ticket info
                let selectedNumbers = [];
                if (data.ticket_info.selected_numbers) {
                    if (Array.isArray(data.ticket_info.selected_numbers)) {
                        // If it's a direct array format
                        selectedNumbers = data.ticket_info.selected_numbers.flat();
                    } else {
                        // If it's an object with row keys like A01, B01, etc.
                        for (const rowKey in data.ticket_info.selected_numbers) {
                            selectedNumbers = selectedNumbers.concat(data.ticket_info.selected_numbers[rowKey]);
                        }
                    }
                }
                
                // Filter out any non-numeric values and sort
                selectedNumbers = selectedNumbers
                    .filter(num => !isNaN(num) && num !== null)
                    .map(num => parseInt(num, 10))
                    .sort((a, b) => a - b);
                
                // Create balls for ticket numbers
                selectedNumbers.forEach(number => {
                    const ball = document.createElement('div');
                    ball.className = 'lottery-ball';
                    ball.textContent = number;
                    ticketNumbersContainer.appendChild(ball);
                });
            }
        }
        
        // Display winning numbers if available
        if (data.winning_numbers) {
            const winningNumbersContainer = document.getElementById('winning-numbers');
            if (winningNumbersContainer) {
                winningNumbersContainer.innerHTML = ''; // Clear previous
                
                // Extract and display main numbers
                const mainNumbers = data.winning_numbers.main_numbers || [];
                mainNumbers.forEach(number => {
                    const ball = document.createElement('div');
                    ball.className = 'lottery-ball';
                    ball.textContent = number;
                    winningNumbersContainer.appendChild(ball);
                });
                
                // Handle bonus numbers if present
                const bonusNumbers = data.winning_numbers.bonus_numbers || [];
                if (bonusNumbers.length > 0) {
                    // For PowerBall, add the bonus number with a special class
                    bonusNumbers.forEach(number => {
                        const ball = document.createElement('div');
                        ball.className = 'lottery-ball bonus-ball';
                        ball.textContent = number;
                        winningNumbersContainer.appendChild(ball);
                    });
                }
            }
        }
        
        // Handle matched numbers
        if (data.matches) {
            const matchedCount = document.getElementById('matched-count');
            if (matchedCount) {
                matchedCount.textContent = data.matches.matched_count || '0';
            }
            
            // Highlight matched balls
            if (data.matches.matched_numbers) {
                const ticketBalls = document.querySelectorAll('#ticket-numbers .lottery-ball');
                ticketBalls.forEach(ball => {
                    const number = parseInt(ball.textContent, 10);
                    if (data.matches.matched_numbers.includes(number)) {
                        ball.classList.add('matched');
                        
                        // Add a checkmark to matched balls
                        const checkmark = document.createElement('span');
                        checkmark.className = 'checkmark';
                        checkmark.innerHTML = '✓';
                        ball.appendChild(checkmark);
                    }
                });
            }
        }
        
        // Enable the scan button again
        if (scanButton) {
            scanButton.disabled = false;
        }
    };
    
    // Set up scan another ticket button
    if (scanAnotherButton) {
        scanAnotherButton.addEventListener('click', function() {
            console.log("Scan another ticket button clicked");
            
            // Reset the file input
            fileInput.value = '';
            
            // Clear the image preview
            if (ticketPreview.src && ticketPreview.src.startsWith('blob:')) {
                URL.revokeObjectURL(ticketPreview.src);
            }
            ticketPreview.src = '';
            
            // Hide the preview container
            if (previewContainer) {
                previewContainer.classList.add('d-none');
            }
            
            // Hide results container
            if (resultsContainer) {
                resultsContainer.classList.add('d-none');
            }
            
            // Disable the scan button
            if (scanButton) {
                scanButton.disabled = true;
            }
            
            // Scroll to the upload form
            const ticketForm = document.getElementById('ticket-form');
            if (ticketForm) {
                ticketForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }
});