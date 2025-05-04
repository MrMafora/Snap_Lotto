/**
 * Ticket Scanner Upload Test Script
 * This script will help diagnose issues with the file upload functionality
 */

console.log('File upload test script loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - starting file upload diagnostics');
    
    // Get references to critical elements
    const fileInput = document.getElementById('ticket-image');
    const fileSelectBtn = document.getElementById('file-select-btn');
    const ticketForm = document.getElementById('ticket-form');
    const scanButton = document.getElementById('scan-button');
    
    // Check if critical elements exist
    console.log('File input exists:', !!fileInput);
    console.log('File select button exists:', !!fileSelectBtn);
    console.log('Ticket form exists:', !!ticketForm);
    console.log('Scan button exists:', !!scanButton);
    
    // Check form attributes
    if (ticketForm) {
        console.log('Form action:', ticketForm.action);
        console.log('Form method:', ticketForm.method);
        console.log('Form enctype:', ticketForm.enctype);
    }
    
    // Check file input attributes
    if (fileInput) {
        console.log('File input name:', fileInput.name);
        console.log('File input accept:', fileInput.accept);
    }
    
    // Add direct event listeners for testing
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            console.log('File input change event triggered');
            console.log('Selected files:', e.target.files);
            if (e.target.files.length > 0) {
                console.log('File name:', e.target.files[0].name);
                console.log('File type:', e.target.files[0].type);
                console.log('File size:', e.target.files[0].size, 'bytes');
            }
        });
    }
    
    if (fileSelectBtn) {
        fileSelectBtn.addEventListener('click', function(e) {
            console.log('File select button click detected');
        });
    }
    
    if (ticketForm) {
        ticketForm.addEventListener('submit', function(e) {
            console.log('Form submission detected');
            console.log('Form data being submitted:');
            
            // Log all form data for debugging
            const formData = new FormData(ticketForm);
            for (const pair of formData.entries()) {
                console.log(`- ${pair[0]}: ${pair[1] instanceof File ? pair[1].name : pair[1]}`);
            }
        });
    }
    
    // Test AJAX submission
    window.testFileUpload = function(file) {
        console.log('Manual file upload test started');
        if (!file && fileInput && fileInput.files.length > 0) {
            file = fileInput.files[0];
        }
        
        if (!file) {
            console.error('No file selected for upload test');
            return;
        }
        
        console.log('Testing upload with file:', file.name);
        
        // Create FormData for test
        const testFormData = new FormData();
        testFormData.append('ticket_image', file);
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
        if (csrfToken) {
            testFormData.append('csrf_token', csrfToken);
        }
        
        // Create and send test request
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/scan-ticket', true);
        
        xhr.onload = function() {
            console.log('Upload test response received');
            console.log('Status:', xhr.status);
            console.log('Response:', xhr.responseText);
        };
        
        xhr.onerror = function() {
            console.error('Upload test failed');
            console.error('Error:', xhr.statusText);
        };
        
        console.log('Sending test upload request');
        xhr.send(testFormData);
    };
    
    console.log('File upload diagnostic initialization complete');
});