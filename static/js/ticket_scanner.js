/**
 * Snap Lotto Ticket Scanner Module
 * Handles ticket image upload, processing and result display 
 */

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Camera elements
    const cameraBtn = document.getElementById('camera-btn');
    const cameraInterface = document.getElementById('camera-interface');
    const cameraPreview = document.getElementById('camera-preview');
    const captureBtn = document.getElementById('capture-btn');
    const switchCameraBtn = document.getElementById('switch-camera-btn');
    const cancelCameraBtn = document.getElementById('cancel-camera-btn');
    const captureCanvas = document.getElementById('capture-canvas');
    
    // Regular file upload elements
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('ticket-image');
    const fileSelectBtn = document.getElementById('file-select-btn');
    const previewContainer = document.getElementById('preview-container');
    const ticketPreview = document.getElementById('ticket-preview');
    const removeImageBtn = document.getElementById('remove-image');
    const scanButton = document.getElementById('scan-button');
    
    // Results elements
    const resultsContainer = document.getElementById('results-container');
    const successContent = document.getElementById('success-content');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    // Form and overlays
    const ticketForm = document.getElementById('ticket-form');
    const loadingOverlay = document.getElementById('ad-overlay-loading');
    const resultsOverlay = document.getElementById('ad-overlay-results');
    const viewResultsBtn = document.getElementById('view-results-btn');
    
    // Camera variables
    let stream = null;
    let facingMode = 'environment'; // Start with back camera
    
    // Initialize camera button events
    if (cameraBtn) {
        cameraBtn.addEventListener('click', startCamera);
    }
    
    if (switchCameraBtn) {
        switchCameraBtn.addEventListener('click', toggleCamera);
    }
    
    if (captureBtn) {
        captureBtn.addEventListener('click', capturePhoto);
    }
    
    if (cancelCameraBtn) {
        cancelCameraBtn.addEventListener('click', stopCamera);
    }
    
    // Initialize drag and drop for ticket image
    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        dropArea.addEventListener('drop', handleDrop, false);
    }
    
    // File select button
    if (fileSelectBtn) {
        fileSelectBtn.addEventListener('click', () => {
            fileInput.click();
        });
    }
    
    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files[0]) {
                handleFiles(fileInput.files);
            }
        });
    }
    
    // Remove image button
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', removeImage);
    }
    
    // View results button
    if (viewResultsBtn) {
        viewResultsBtn.addEventListener('click', function() {
            console.log('View Results button clicked!');
            if (window.AdManager) {
                AdManager.hideInterstitialAd();
            } else {
                console.error('AdManager not found - using fallback hide');
                if (resultsOverlay) {
                    resultsOverlay.style.display = 'none';
                }
                document.body.style.overflow = 'auto';
                document.body.style.position = 'static';
            }
            
            if (window.ticketData) {
                displayResults(window.ticketData);
            } else {
                console.error('No ticket data available');
                showError('Error: No ticket data available. Please try scanning again.');
            }
        });
    }
    
    // Form submission
    if (ticketForm) {
        ticketForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const loadingIndicator = document.getElementById('scanner-loading');
            loadingIndicator.style.display = 'block';
            scanButton.disabled = true;
            
            // Check if we have an image
            if (!fileInput.files || !fileInput.files[0]) {
                showError('Please upload an image of your lottery ticket.');
                loadingIndicator.style.display = 'none';
                scanButton.disabled = false;
                return;
            }
            
            // Start processing animations
            if (window.AdManager) {
                AdManager.showLoadingAd();
                console.log('Loading ad shown');
                
                startProcessingAnimation();
            }
            
            const formData = new FormData(ticketForm);
            
            // Send the form data to the server
            fetch('/scan-ticket', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
                
                // Save ticket data globally
                window.ticketData = data;
                
                // Hide ad loading overlay
                if (window.AdManager) {
                    AdManager.hideLoadingAd();
                }
                
                // Show results with data
                showResultsOverlay(data);
            })
            .catch(error => {
                console.error('Error:', error);
                // Hide ad loading overlay
                if (window.AdManager) {
                    AdManager.hideLoadingAd();
                }
                showError('An error occurred while scanning your ticket. Please try again.');
                
                // Hide loading indicator and re-enable scan button
                loadingIndicator.style.display = 'none';
                scanButton.disabled = false;
                console.log("Scan completed - button enabled");
            });
        });
    }
    
    // Helper functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            
            if (!file.type.match('image.*')) {
                showError('Please upload an image file (JPG, PNG, etc.).');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (e) => {
                ticketPreview.src = e.target.result;
                dropArea.classList.add('d-none');
                previewContainer.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        }
    }
    
    function removeImage() {
        fileInput.value = '';
        ticketPreview.src = '';
        previewContainer.classList.add('d-none');
        dropArea.classList.remove('d-none');
    }
    
    function startCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showError('Camera access is not supported in your browser.');
            return;
        }
        
        // Hide the drop area and show camera interface
        dropArea.classList.add('d-none');
        cameraInterface.classList.remove('d-none');
        
        // Get camera stream
        const constraints = {
            video: {
                facingMode: facingMode,
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        };
        
        navigator.mediaDevices.getUserMedia(constraints)
            .then((mediaStream) => {
                stream = mediaStream;
                cameraPreview.srcObject = mediaStream;
                cameraPreview.play();
            })
            .catch((err) => {
                console.error('Error accessing camera:', err);
                showError('Error accessing camera. Please ensure you have granted camera permissions.');
                stopCamera();
            });
    }
    
    function stopCamera() {
        if (stream) {
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop());
            stream = null;
        }
        
        // Hide camera interface and show drop area
        cameraInterface.classList.add('d-none');
        dropArea.classList.remove('d-none');
        
        // Clear preview if it exists
        if (cameraPreview.srcObject) {
            cameraPreview.srcObject = null;
        }
    }
    
    function toggleCamera() {
        if (stream) {
            // Stop current stream
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop());
            
            // Toggle facing mode
            facingMode = facingMode === 'environment' ? 'user' : 'environment';
            
            // Restart camera with new facing mode
            const constraints = {
                video: {
                    facingMode: facingMode,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };
            
            navigator.mediaDevices.getUserMedia(constraints)
                .then((mediaStream) => {
                    stream = mediaStream;
                    cameraPreview.srcObject = mediaStream;
                    cameraPreview.play();
                })
                .catch((err) => {
                    console.error('Error toggling camera:', err);
                    showError('Error switching camera. Your device may not support this feature.');
                    stopCamera();
                });
        }
    }
    
    function capturePhoto() {
        if (!stream) return;
        
        // Set canvas dimensions to match video
        const width = cameraPreview.videoWidth;
        const height = cameraPreview.videoHeight;
        captureCanvas.width = width;
        captureCanvas.height = height;
        
        // Draw the current video frame to the canvas
        const ctx = captureCanvas.getContext('2d');
        ctx.drawImage(cameraPreview, 0, 0, width, height);
        
        // Convert to file
        captureCanvas.toBlob(function(blob) {
            const file = new File([blob], "ticket_photo.jpg", { type: "image/jpeg" });
            
            // Create a FileList-like object
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // Update preview
            ticketPreview.src = URL.createObjectURL(blob);
            previewContainer.classList.remove('d-none');
            
            // Hide camera interface
            stopCamera();
        }, 'image/jpeg', 0.95);
    }
    
    function showResultsOverlay(data) {
        // Store ticket data globally
        window.ticketData = data;
        
        // Start processing animations
        startProcessingSteps();
        
        // Show interstitial ad after steps are complete
        function startProcessingSteps() {
            const steps = document.querySelectorAll('.step');
            const progressBar = document.getElementById('scan-progress-bar');
            const stepText = document.getElementById('scan-step-text');
            
            let currentStep = 0;
            const stepTexts = [
                'Uploading and analyzing your ticket image...',
                'Identifying game type and draw details...',
                'Extracting your selected numbers...',
                'Comparing with winning numbers...',
                'Checking for matches...',
                'Calculating potential prize...',
                'Results ready!'
            ];
            
            // Reset steps
            steps.forEach(step => step.classList.remove('active'));
            steps[0].classList.add('active');
            progressBar.style.width = '25%';
            stepText.textContent = stepTexts[0];
            
            // Update steps at intervals
            const stepInterval = setInterval(() => {
                currentStep++;
                
                if (currentStep < steps.length) {
                    // Update active step
                    steps.forEach(step => step.classList.remove('active'));
                    steps[currentStep].classList.add('active');
                    
                    // Update progress bar
                    progressBar.style.width = `${25 + (currentStep * 25)}%`;
                }
                
                // Update step text
                if (currentStep < stepTexts.length) {
                    stepText.textContent = stepTexts[currentStep];
                }
                
                // If we're at the end of the steps, show the results
                if (currentStep >= steps.length + 1) {
                    clearInterval(stepInterval);
                    
                    // Show the results interstitial ad
                    console.log('Showing processing ad for 5+ seconds');
                    
                    // Show results overlay after a short delay
                    setTimeout(() => {
                        // If AdManager is available, show interstitial ad
                        if (window.AdManager) {
                            AdManager.showInterstitialAd();
                            
                            console.log('Showing results interstitial ad');
                        } else {
                            // Fallback if AdManager isn't loaded
                            if (resultsOverlay) {
                                resultsOverlay.style.display = 'flex';
                            }
                            console.warn('AdManager not found - using fallback display');
                        }
                        
                        // Hide loading indicator and re-enable scan button
                        const loadingIndicator = document.getElementById('scanner-loading');
                        loadingIndicator.style.display = 'none';
                        scanButton.disabled = false;
                        console.log("Scan completed - button enabled");
                    }, 1000);
                }
            }, 2000); // Change steps every 2 seconds for a total of 14 seconds (7 steps)
        }
    }
    
    function displayResults(data) {
        console.log('Displaying results:', data);
        
        // Force enable scrolling on document body and html
        document.body.style.overflow = 'auto';
        document.body.style.position = 'static';
        document.body.style.width = '';
        document.body.style.height = '';
        document.documentElement.style.overflow = 'auto';
        document.documentElement.style.position = 'static';
        
        // Populate result fields
        document.getElementById('result-lottery-type').textContent = data.lottery_type || 'Unknown';
        document.getElementById('result-draw-number').textContent = data.draw_number || 'Unknown';
        document.getElementById('result-draw-date').textContent = data.draw_date || 'Unknown';
        
        // Populate detected info
        if (data.ticket_info) {
            document.getElementById('detected-game-type').textContent = data.ticket_info.detected_game_type || 'Unknown';
            document.getElementById('detected-draw-number').textContent = data.ticket_info.detected_draw_number || 'Unknown';
            document.getElementById('detected-draw-date').textContent = data.ticket_info.detected_draw_date || 'Unknown';
        }
        
        // Show winning numbers
        const winningNumbersContainer = document.getElementById('winning-numbers-container');
        if (winningNumbersContainer) {
            winningNumbersContainer.innerHTML = '';
            
            if (data.winning_numbers && data.winning_numbers.length > 0) {
                data.winning_numbers.forEach(number => {
                    const ball = document.createElement('div');
                    ball.className = 'lottery-ball';
                    ball.textContent = number;
                    winningNumbersContainer.appendChild(ball);
                });
                
                // Add bonus numbers if available
                if (data.bonus_numbers && data.bonus_numbers.length > 0) {
                    // Add separator
                    const separator = document.createElement('div');
                    separator.className = 'ball-separator';
                    separator.textContent = '+';
                    winningNumbersContainer.appendChild(separator);
                    
                    // Add bonus balls
                    data.bonus_numbers.forEach(number => {
                        const ball = document.createElement('div');
                        ball.className = 'lottery-ball bonus';
                        ball.textContent = number;
                        winningNumbersContainer.appendChild(ball);
                    });
                }
            } else {
                winningNumbersContainer.innerHTML = '<p class="text-muted">No winning numbers available</p>';
            }
        }
        
        // Show ticket numbers with matches highlighted
        const ticketNumbersContainer = document.getElementById('ticket-numbers-container');
        if (ticketNumbersContainer && data.rows_with_matches) {
            ticketNumbersContainer.innerHTML = '';
            
            data.rows_with_matches.forEach(row => {
                const rowDiv = document.createElement('div');
                rowDiv.className = 'ticket-row mb-2';
                
                // Add row label
                const rowLabel = document.createElement('div');
                rowLabel.className = 'row-label me-2';
                rowLabel.textContent = row.row || '';
                rowDiv.appendChild(rowLabel);
                
                // Add number balls
                const ballsContainer = document.createElement('div');
                ballsContainer.className = 'd-flex flex-wrap';
                
                if (row.numbers && row.numbers.length > 0) {
                    row.numbers.forEach((number, index) => {
                        const ball = document.createElement('div');
                        
                        // Check if this number matches a winning number
                        const isMatch = row.matched_numbers && row.matched_numbers.includes(number);
                        const isBonus = row.matched_bonus && row.matched_bonus.includes(number);
                        
                        ball.className = 'lottery-ball small ' + 
                                      (isMatch ? 'matched' : '') + 
                                      (isBonus ? 'matched-bonus' : '');
                        
                        ball.textContent = number;
                        
                        // Add checkmark icon inside matched balls
                        if (isMatch || isBonus) {
                            const checkmark = document.createElement('i');
                            checkmark.className = 'fas fa-check match-check';
                            ball.appendChild(checkmark);
                        }
                        
                        ballsContainer.appendChild(ball);
                        
                        // Add + separator before the last ball in Powerball games
                        if (index === row.numbers.length - 2 && 
                            (data.lottery_type === 'Powerball' || data.lottery_type === 'Powerball Plus')) {
                            const separator = document.createElement('div');
                            separator.className = 'ball-separator small';
                            separator.textContent = '+';
                            ballsContainer.appendChild(separator);
                        }
                    });
                }
                
                rowDiv.appendChild(ballsContainer);
                ticketNumbersContainer.appendChild(rowDiv);
            });
        }
        
        // Show prize info
        const prizeInfoContainer = document.getElementById('prize-info-container');
        if (prizeInfoContainer) {
            if (data.has_prize) {
                prizeInfoContainer.innerHTML = `
                    <div class="alert alert-success">
                        <h5 class="mb-0"><i class="fas fa-trophy me-2"></i> Congratulations! You've won a prize!</h5>
                    </div>
                `;
                
                // Add prize details if available
                if (data.prize_info && Object.keys(data.prize_info).length > 0) {
                    const prizeDetails = document.createElement('div');
                    prizeDetails.className = 'prize-details mt-3';
                    
                    for (const [division, info] of Object.entries(data.prize_info)) {
                        prizeDetails.innerHTML += `
                            <div class="prize-row">
                                <strong>${division}:</strong> ${info.prize || 'Unknown'} 
                                <span class="text-muted small">(${info.match || 'Unknown match'})</span>
                            </div>
                        `;
                    }
                    
                    prizeInfoContainer.appendChild(prizeDetails);
                }
            } else {
                // Check if we had any matches
                if (data.matched_numbers && data.matched_numbers.length > 0) {
                    prizeInfoContainer.innerHTML = `
                        <div class="alert alert-warning">
                            <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i> You matched ${data.matched_numbers.length} number(s), but didn't win a prize this time.</h5>
                        </div>
                    `;
                } else {
                    prizeInfoContainer.innerHTML = `
                        <div class="alert alert-secondary">
                            <h5 class="mb-0"><i class="fas fa-times-circle me-2"></i> Sorry, your ticket didn't win this time.</h5>
                        </div>
                    `;
                }
            }
        }
        
        // Show the results container
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
        }
        
        // Show success content
        if (successContent) {
            successContent.classList.remove('d-none');
        }
        
        // Hide error message if visible
        if (errorMessage) {
            errorMessage.classList.add('d-none');
        }
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    function showError(message) {
        console.error('Error:', message);
        
        // Hide success content
        if (successContent) {
            successContent.classList.add('d-none');
        }
        
        // Show error message
        if (errorMessage && errorText) {
            let formattedMessage;
            
            if (message.includes('Please upload') || message.includes('Camera access')) {
                formattedMessage = `<div class="mb-3">
                    <i class="fas fa-exclamation-triangle me-2 text-warning"></i> 
                    ${message}
                </div>`;
            } else {
                formattedMessage = `<div class="mb-3">
                    <i class="fas fa-exclamation-triangle me-2 text-warning"></i> 
                    ${message}
                </div>`;
            }
            
            // Use innerHTML to support formatted messages with HTML
            errorText.innerHTML = formattedMessage;
            errorMessage.classList.remove('d-none');
            successContent.classList.add('d-none');
            
            // Scroll to the error message
            errorMessage.scrollIntoView({ behavior: 'smooth' });
        }
    }
});