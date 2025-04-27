// Ticket scanner main JavaScript functionality with improved reliability
// This version fixes the issues with image uploads and scanning

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
                    // Show alert for image error
                    alert('Error displaying the image. Please try another file.');
                    fileInput.value = '';
                    scanButton.disabled = true;
                };
                
                // Set the source to trigger the onload event
                try {
                    ticketPreview.src = objectUrl;
                } catch (e) {
                    console.error("Error setting image source:", e);
                    alert('Error processing the image file. Please try a different image.');
                    fileInput.value = '';
                    scanButton.disabled = true;
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
    
    // Main ticket processing function
    window.processTicketWithAds = function() {
        console.log("Processing ticket with ads:", new Date().toISOString());
        
        // Verify we have a file
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            console.error("No file selected!");
            alert("Please select an image first");
            return;
        }
        
        console.log("File is selected:", fileInput.files[0].name);
        
        // Clear any previous results
        clearPreviousResults();
        
        // Make scanner loading visible
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
        
        // Get lottery type
        const lotteryType = lotteryTypeSelect ? lotteryTypeSelect.value : '';
        
        // Create form data
        const formData = new FormData();
        formData.append('ticket_image', fileInput.files[0]);
        formData.append('lottery_type', lotteryType);
        
        // Add CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            formData.append('csrf_token', csrfToken.getAttribute('content'));
        }
        
        // Submit the form data
        console.log("Submitting form data to /scan-ticket");
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
            
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            // Display the results
            displayResults(data);
        })
        .catch(error => {
            console.error("Error processing ticket:", error);
            
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            // Show error message
            alert("Error processing ticket: " + error.message);
            
            // Re-enable scan button
            scanButton.disabled = false;
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