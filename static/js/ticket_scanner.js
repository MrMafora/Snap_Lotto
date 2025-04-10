/**
 * Ticket scanner functionality for Snap Lotto
 * Handles the scanning of lottery tickets using the camera or file upload
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Ticket scanner script loaded");
    initTicketScannerFunctionality();
});

function initTicketScannerFunctionality() {
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
    const ticketForm = document.getElementById('ticket-form');
    const lotteryTypeSelect = document.getElementById('lottery_type');
    const loadingIndicator = document.getElementById('scanner-loading');
    const resultsContainer = document.getElementById('results-container');
    const scanNewTicketBtn = document.getElementById('scan-new-ticket');
    
    // Camera stream variables
    let stream = null;
    let currentFacingMode = 'environment'; // Start with back camera
    
    // Exit early if essential elements are missing (wrong page)
    if (!scanButton || !ticketForm) {
        console.log("Not on ticket scanner page, skipping initialization");
        return;
    }
    
    // Add form submission handler
    ticketForm.addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent standard form submission
        
        // Check if an image has been selected
        if (fileInput && fileInput.files.length) {
            // Process the ticket with ads
            processTicketWithAds();
        } else {
            alert('Please select an image first.');
        }
        
        return false; // Prevent form from submitting normally
    });
    
    // Camera handling functions
    function startCamera() {
        // Hide the drop area and show camera interface
        dropArea.classList.add('d-none');
        cameraInterface.classList.remove('d-none');
        
        // Get camera access
        const constraints = {
            video: {
                facingMode: currentFacingMode,
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        };
        
        // Stop any existing stream
        if (stream) {
            stopCameraStream();
        }
        
        // Request camera access
        navigator.mediaDevices.getUserMedia(constraints)
            .then(function(mediaStream) {
                stream = mediaStream;
                cameraPreview.srcObject = stream;
                cameraPreview.play();
                console.log('Camera started successfully:', currentFacingMode);
            })
            .catch(function(err) {
                console.error('Error accessing camera:', err);
                alert('Could not access the camera. Please ensure you have granted camera permissions and try again. Error: ' + err.message);
                stopCamera();
            });
    }
    
    function stopCameraStream() {
        if (stream) {
            stream.getTracks().forEach(track => {
                track.stop();
            });
            stream = null;
            cameraPreview.srcObject = null;
        }
    }
    
    function stopCamera() {
        stopCameraStream();
        cameraInterface.classList.add('d-none');
        dropArea.classList.remove('d-none');
    }
    
    function switchCamera() {
        currentFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
        console.log('Switching camera to:', currentFacingMode);
        startCamera(); // This will restart the camera with the new facing mode
    }
    
    function captureImage() {
        if (!stream) {
            console.error('No camera stream available');
            return;
        }
        
        // Set canvas dimensions to match video
        const width = cameraPreview.videoWidth;
        const height = cameraPreview.videoHeight;
        captureCanvas.width = width;
        captureCanvas.height = height;
        
        // Draw video frame to canvas
        const context = captureCanvas.getContext('2d');
        context.drawImage(cameraPreview, 0, 0, width, height);
        
        // Convert to data URL
        const imageDataUrl = captureCanvas.toDataURL('image/jpeg');
        
        // Show the preview with captured image
        ticketPreview.src = imageDataUrl;
        previewContainer.classList.remove('d-none');
        
        // Create a file object from the data URL for form submission
        fetch(imageDataUrl)
            .then(res => res.blob())
            .then(blob => {
                const file = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });
                
                // Create a FileList-like object
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
                
                // Stop camera and show preview
                stopCamera();
                updateScanButton();
            })
            .catch(err => {
                console.error('Error creating file from canvas:', err);
                alert('Error capturing image. Please try again.');
            });
    }
    
    // Camera button event listeners
    if (cameraBtn) cameraBtn.addEventListener('click', startCamera);
    if (captureBtn) captureBtn.addEventListener('click', captureImage);
    if (switchCameraBtn) switchCameraBtn.addEventListener('click', switchCamera);
    if (cancelCameraBtn) cancelCameraBtn.addEventListener('click', stopCamera);
    
    // Initialize scan button state
    setTimeout(() => {
        updateScanButton();
    }, 500);
    
    // File selection via button
    if (fileSelectBtn) {
        fileSelectBtn.addEventListener('click', () => {
            fileInput.click();
        });
    }
    
    // File selection change
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Drag and drop events
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
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect();
        }
    }
    
    function handleFileSelect() {
        const file = fileInput.files[0];
        
        if (file) {
            // Check if file is an image
            if (!file.type.match('image.*')) {
                alert('Please select an image file');
                fileInput.value = ''; // Clear the file input
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = function(e) {
                ticketPreview.src = e.target.result;
                previewContainer.classList.remove('d-none');
                // Update scan button state
                updateScanButton();
            }
            
            reader.onerror = function() {
                alert('Error reading the image file. Please try a different image.');
                fileInput.value = ''; // Clear the file input on error
                updateScanButton();
            }
            
            reader.readAsDataURL(file);
        } else {
            previewContainer.classList.add('d-none');
            updateScanButton();
        }
    }
    
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            ticketPreview.src = '';
            fileInput.value = '';
            previewContainer.classList.add('d-none');
            updateScanButton();
        });
    }
    
    if (lotteryTypeSelect) {
        lotteryTypeSelect.addEventListener('change', updateScanButton);
    }
    
    // Add a direct click handler for the scan button
    if (scanButton) {
        scanButton.addEventListener('click', function(e) {
            if (fileInput && fileInput.files.length) {
                e.preventDefault();
                processTicketWithAds();
            }
        });
    }
    
    // Scan new ticket button (success case)
    if (scanNewTicketBtn) {
        scanNewTicketBtn.addEventListener('click', function() {
            resetScannerForm();
        });
    }
    
    // Scan another button (error case)
    const scanAnotherBtn = document.getElementById('scan-another-btn');
    if (scanAnotherBtn) {
        scanAnotherBtn.addEventListener('click', function() {
            resetScannerForm();
        });
    }
    
    // Common function to reset the scanner form
    function resetScannerForm() {
        // Hide results and reset the form
        if (resultsContainer) resultsContainer.classList.add('d-none');
        if (ticketForm) ticketForm.reset();
        if (previewContainer) previewContainer.classList.add('d-none');
        
        // Stop camera if active
        if (stream) {
            stopCamera();
        }
        
        // Make sure camera interface is hidden and drop area is visible
        if (cameraInterface) cameraInterface.classList.add('d-none');
        if (dropArea) dropArea.classList.remove('d-none');
        
        updateScanButton();
        
        // Scroll back to top of scanner
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
    
    function updateScanButton() {
        // Enable button if image is selected
        if (scanButton && fileInput) {
            scanButton.disabled = !fileInput.files.length;
        }
    }
    
    // Function to handle showing ads and processing the ticket
    function processTicketWithAds() {
        // Immediately force-display loading indicator
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
        
        // Disable the scan button while processing
        if (scanButton) {
            scanButton.disabled = true;
        }
        
        // Show ad overlay (force override any previous styling issues)
        const adOverlayLoading = document.getElementById('ad-overlay-loading');
        if (adOverlayLoading) {
            // Ensure the overlay is fully reset
            adOverlayLoading.style.display = 'flex';
            adOverlayLoading.style.opacity = '1';
            adOverlayLoading.style.visibility = 'visible';
            adOverlayLoading.style.zIndex = '9999';
            
            // Prevent background scrolling
            document.body.style.overflow = 'hidden';
            document.body.style.position = 'fixed';
            document.body.style.width = '100%';
            document.body.style.top = '0';
            document.body.style.left = '0';
            
            // Create a basic ad placeholder in the container
            const adContainer = document.getElementById('ad-container-loader');
            if (adContainer) {
                adContainer.innerHTML = `
                    <div class="text-center">
                        <div class="ad-placeholder py-4">
                            <p><i class="fas fa-ad mb-2 fa-2x"></i></p>
                            <p class="mb-0">Advertisement</p>
                            <p class="small text-muted mt-1">Advertisements help keep this service free</p>
                        </div>
                    </div>
                `;
            }
            
            // Don't use callbacks here, directly process the ticket
            processTicket();
        } else {
            // Fallback if overlay element is missing
            console.error("Ad overlay element missing! Using direct processing.");
            processTicket();
        }
    }
    
    // Main ticket processing function
    function processTicket() {
        // Create form data from the ticket form
        const formData = new FormData(ticketForm);
        
        // Simulate the processing steps with progress updates
        simulateProcessingSteps(formData);
    }
    
    // Simulate processing steps to make ad viewing time more engaging
    function simulateProcessingSteps(formData) {
        const progressBar = document.getElementById('scan-progress-bar');
        const stepText = document.getElementById('scan-step-text');
        
        // Create more steps to extend the processing time to 14 seconds
        const steps = [
            { 
                text: "Initializing ticket scanning process...", 
                progress: 10,
                activeStep: 1
            },
            { 
                text: "Uploading and analyzing your ticket image...", 
                progress: 25,
                activeStep: 1
            },
            { 
                text: "Using AI to identify game type...", 
                progress: 40,
                activeStep: 2
            },
            { 
                text: "Extracting draw information and date...", 
                progress: 60,
                activeStep: 2
            },
            { 
                text: "Detecting your selected lottery numbers...", 
                progress: 75,
                activeStep: 3
            },
            { 
                text: "Matching your numbers against winning combinations...", 
                progress: 90,
                activeStep: 4
            },
            { 
                text: "Results ready! Finishing up...", 
                progress: 100,
                activeStep: 4
            }
        ];
        
        let currentStep = 0;
        let ticketData = null;
        let ticketProcessed = false;
        
        // Start processing the ticket in the background while showing ads
        // This way, results will be ready when the ad finishes
        console.log('Sending ticket data to server...');
        
        // Add debugging for form data
        for (let pair of formData.entries()) {
            console.log(pair[0] + ': ' + (pair[0] === 'ticket_image' ? '[File data]' : pair[1])); 
        }
        
        // No need to manually add CSRF token as it's included in the formData
        // from the hidden_tag() in the form
        fetch('/scan-ticket', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // Check if response is ok before trying to parse JSON
            if (!response.ok) {
                throw new Error('Server returned status: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            ticketData = data;
            ticketProcessed = true;
        })
        .catch(error => {
            console.error('Error during scan ticket processing:', error);
            ticketProcessed = true;
            ticketData = { 
                error: "An error occurred while scanning your ticket. Please try again.",
                details: error.toString()
            };
        });
        
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                
                // Update step text and progress bar
                if (stepText) stepText.textContent = step.text;
                if (progressBar) progressBar.style.width = step.progress + '%';
                
                // Update step indicators
                const allSteps = document.querySelectorAll('.step');
                allSteps.forEach((stepEl, index) => {
                    // Reset all steps
                    stepEl.classList.remove('active', 'completed');
                    
                    // Mark completed steps
                    if (index + 1 < step.activeStep) {
                        stepEl.classList.add('completed');
                    }
                    // Mark active step
                    else if (index + 1 === step.activeStep) {
                        stepEl.classList.add('active');
                    }
                });
                
                currentStep++;
                
                // After last step is shown, wait a bit more for ad view time
                if (currentStep >= steps.length) {
                    setTimeout(() => {
                        completeProcess();
                    }, 1000);
                }
            }
        }, 2000); // Step every 2 seconds
        
        // Function to complete the process and show results
        function completeProcess() {
            console.log('Completing ticket processing...');
            
            // Add timeout to force completion in case the ticket 
            // is never marked as processed
            let processingTimeout = setTimeout(() => {
                console.log('Processing timeout reached - forcing completion');
                if (!ticketProcessed) {
                    ticketProcessed = true;
                    ticketData = { 
                        error: "Ticket scanning timed out. Please try again.",
                        details: "Server did not respond within the expected timeframe."
                    };
                }
            }, 5000); // 5 second timeout
            
            // Clear the interval to stop processing animation
            clearInterval(interval);
            
            // Hide the loading overlay and ad
            try {
                if (window.AdManager) {
                    window.AdManager.hideLoadingAd();
                } else {
                    // Manual hide if AdManager not available
                    const adOverlayLoading = document.getElementById('ad-overlay-loading');
                    if (adOverlayLoading) {
                        adOverlayLoading.style.display = 'none';
                    }
                    // Reset body styles
                    document.body.style.overflow = 'auto';
                    document.body.style.position = 'static';
                    document.body.style.width = 'auto';
                    document.body.style.height = 'auto';
                    document.body.style.top = 'auto';
                    document.body.style.left = 'auto';
                    document.documentElement.style.overflow = 'auto';
                    document.documentElement.style.position = 'static';
                    document.body.style.touchAction = 'auto';
                }
            } catch (e) {
                console.error('Error hiding overlay:', e);
            }
            
            // Wait for ticket to be processed before showing results
            function checkTicketProcessed() {
                if (ticketProcessed) {
                    clearTimeout(processingTimeout);
                    console.log('Ticket processing completed, displaying results...');
                    
                    // Add small delay to ensure UI is ready
                    setTimeout(() => {
                        try {
                            displayResults(ticketData);
                            console.log('Results displayed successfully');
                        } catch (err) {
                            console.error('Error in displayResults:', err);
                            // Force close overlay if there's an error displaying results
                            if (document.getElementById('ad-overlay-loading')) {
                                document.getElementById('ad-overlay-loading').style.display = 'none';
                            }
                            // Display error in results area
                            const resultsContent = document.getElementById('results-content');
                            if (resultsContent) {
                                resultsContent.innerHTML = `
                                    <div class="alert alert-danger">
                                        <strong>Error displaying results:</strong> ${err.message || 'Unknown error'}
                                    </div>
                                    <button id="force-reset-btn" class="btn btn-primary">Try Again</button>
                                `;
                                document.getElementById('force-reset-btn')?.addEventListener('click', resetScannerForm);
                            }
                        }
                    }, 100);
                } else {
                    console.log('Waiting for ticket processing to complete...');
                    setTimeout(checkTicketProcessed, 500);
                }
            }
            
            // Start checking if ticket is processed
            checkTicketProcessed();
        }
    }
    
    // Function to display results on the page
    function displayResults(data) {
        console.log('Displaying results:', data);
        
        // Hide loading indicator
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        
        try {
            // Construct and display the results
            if (data && !data.error) {
                showSuccessResults(data);
            } else {
                showErrorResults(data || "An unknown error occurred");
            }
        } catch (err) {
            console.error('Error displaying results:', err);
            showErrorResults({
                error: "Error displaying results",
                details: err.toString()
            });
        } finally {
            // Always ensure the scan button is re-enabled
            if (scanButton) {
                scanButton.disabled = false;
                console.log("Scan completed - button enabled");
            }
            
            // Ensure all overlay elements are hidden and body style reset
            const adOverlayLoading = document.getElementById('ad-overlay-loading');
            if (adOverlayLoading) {
                adOverlayLoading.style.display = 'none';
            }
            
            // Reset body styles as a final failsafe
            document.body.style.overflow = 'auto';
            document.body.style.position = 'static';
            document.body.style.width = 'auto';
            document.body.style.height = 'auto';
            document.body.style.top = 'auto';
            document.body.style.left = 'auto';
        }
    }
    
    // Show successful ticket scan results
    function showSuccessResults(data) {
        const container = document.getElementById('results-content');
        if (!container) return;
        
        if (resultsContainer) resultsContainer.classList.remove('d-none');
        
        // Populate results content
        let resultsHTML = `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">${data.lottery_type} - Draw #${data.draw_number}</h5>
                    <div class="small">${data.draw_date}</div>
                </div>
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="mb-3">Winning Numbers</h6>
                            <div class="d-flex flex-wrap gap-2 mb-3">
        `;
        
        // Add winning numbers
        data.winning_numbers.forEach(num => {
            resultsHTML += `<div class="lottery-ball">${num}</div>`;
        });
        
        // Add bonus numbers if present
        if (data.bonus_numbers && data.bonus_numbers.length > 0) {
            resultsHTML += `<div class="lottery-ball bonus">${data.bonus_numbers[0]}</div>`;
        }
        
        resultsHTML += `
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="mb-3">Your Ticket Summary</h6>
                            <p>You matched <strong>${data.total_matched}</strong> number(s) in total.</p>
                            
                            ${data.has_prize ? 
                                `<div class="alert alert-success">
                                    <i class="fas fa-trophy me-2"></i> Congratulations! Your ticket has won a prize.
                                </div>` : 
                                `<div class="alert alert-secondary">
                                    <i class="fas fa-info-circle me-2"></i> Your ticket did not win a prize in this draw.
                                </div>`
                            }
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-12">
                            <h6 class="mb-3">Your Ticket Details</h6>
                            <div class="table-responsive">
                                <table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>Board</th>
                                            <th>Your Numbers</th>
                                            <th>Matched</th>
                                        </tr>
                                    </thead>
                                    <tbody>
        `;
        
        // Add rows with ticket details
        data.rows_with_matches.forEach(row => {
            resultsHTML += `
                <tr>
                    <td>${row.row}</td>
                    <td>
                        <div class="d-flex flex-wrap gap-1">
            `;
            
            // For each number in this row, check if it's a match
            row.numbers.forEach(num => {
                const isMatch = row.matched_numbers.includes(num);
                const isBonus = row.matched_bonus && row.matched_bonus.includes(num);
                
                if (isMatch) {
                    resultsHTML += `<div class="lottery-ball-sm match">${num}</div>`;
                } else if (isBonus) {
                    resultsHTML += `<div class="lottery-ball-sm bonus-match">${num}</div>`;
                } else {
                    resultsHTML += `<div class="lottery-ball-sm">${num}</div>`;
                }
            });
            
            resultsHTML += `
                        </div>
                    </td>
                    <td>${row.total_matched} number(s)</td>
                </tr>
            `;
        });
        
        resultsHTML += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card-footer text-center">
                    <button type="button" id="scan-new-ticket" class="btn btn-primary">
                        <i class="fas fa-redo me-2"></i> Scan Another Ticket
                    </button>
                </div>
            </div>
        `;
        
        container.innerHTML = resultsHTML;
        
        // Add click event to the new scan button
        const newScanBtn = document.getElementById('scan-new-ticket');
        if (newScanBtn) {
            newScanBtn.addEventListener('click', resetScannerForm);
        }
    }
    
    // Show error when ticket scanning fails
    function showErrorResults(errorInfo) {
        console.log('Showing error results:', errorInfo);
        const container = document.getElementById('results-content');
        if (!container) {
            console.error('Results container not found');
            return;
        }
        
        if (resultsContainer) {
            resultsContainer.classList.remove('d-none');
        }
        
        // Handle different error formats
        let errorMessage = "";
        let errorDetails = "";
        
        if (typeof errorInfo === 'string') {
            errorMessage = errorInfo;
        } else if (errorInfo && typeof errorInfo === 'object') {
            errorMessage = errorInfo.error || "Unknown error";
            errorDetails = errorInfo.details || "";
        } else {
            errorMessage = "We couldn't process your ticket. Please try again.";
        }
        
        let errorHTML = `
            <div class="card mb-4">
                <div class="card-header bg-danger text-white">
                    <h5 class="mb-0">Error Scanning Ticket</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i> ${errorMessage}
                    </div>
                    ${errorDetails ? `<div class="small text-muted mb-3">Technical details: ${errorDetails}</div>` : ''}
                    
                    <p class="mb-0">Scanning tips:</p>
                    <ul>
                        <li>Make sure the ticket is well-lit and not blurry</li>
                        <li>Ensure the entire ticket is visible in the image</li>
                        <li>Try using the camera button for a direct capture</li>
                    </ul>
                </div>
                <div class="card-footer text-center">
                    <button type="button" id="scan-another-btn" class="btn btn-primary">
                        <i class="fas fa-redo me-2"></i> Try Again
                    </button>
                </div>
            </div>
        `;
        
        container.innerHTML = errorHTML;
        
        // Add click event to the try again button
        const scanAnotherBtn = document.getElementById('scan-another-btn');
        if (scanAnotherBtn) {
            scanAnotherBtn.addEventListener('click', resetScannerForm);
        }
    }
}