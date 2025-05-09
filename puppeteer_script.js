// Puppeteer script for capturing screenshots with anti-detection measures
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Get arguments from command line
const args = process.argv.slice(2);
const url = args[0];
const screenshotPath = args[1];
const htmlPath = args[2];

async function captureScreenshot() {
    console.log(`Capturing screenshot for URL: ${url}`);
    
    // Random user agents to avoid detection
    const userAgents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
    ];
    
    const selectedAgent = userAgents[Math.floor(Math.random() * userAgents.length)];
    
    // Enhanced anti-detection browser settings
    const browserArgs = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-web-security',
        `--window-size=${1280 + Math.floor(Math.random() * 100)},${1024 + Math.floor(Math.random() * 100)}`,
        '--ignore-certificate-errors',
        '--ignore-certificate-errors-spki-list',
        '--enable-features=NetworkService'
    ];
    
    let browser;
    try {
        browser = await puppeteer.launch({
            headless: 'new',
            args: browserArgs
        });
        
        const page = await browser.newPage();
        await page.setUserAgent(selectedAgent);
        
        // Set custom viewport
        await page.setViewport({
            width: 1280 + Math.floor(Math.random() * 100),
            height: 1024 + Math.floor(Math.random() * 100),
            deviceScaleFactor: 1 + (Math.random() * 0.3)
        });
        
        // Add JavaScript to avoid detection
        await page.evaluateOnNewDocument(() => {
            // Overwrite navigator properties to avoid detection
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // Add fake plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ]
            });
            
            // Add language for more realistic browser
            Object.defineProperty(navigator, 'language', {
                get: () => 'en-US'
            });
            
            // Add fake platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // Hide webdriver-related properties
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
            
            // Add webGL renderer
            Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
                value: function(type) {
                    const result = HTMLCanvasElement.prototype.getContext.apply(this, arguments);
                    if (type === 'webgl') {
                        result.getExtension = function(name) {
                            return {
                                UNMASKED_VENDOR_WEBGL: 37445,
                                UNMASKED_RENDERER_WEBGL: 37446
                            };
                        };
                        result.getParameter = function(parameter) {
                            if (parameter === 37445) {
                                return 'Google Inc.';
                            }
                            if (parameter === 37446) {
                                return 'Intel Iris OpenGL Engine';
                            }
                        };
                    }
                    return result;
                }
            });
        });
        
        // Navigate to URL with retries for the "Oops" error
        let success = false;
        const maxRetries = 3;
        
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            console.log(`Navigating to URL (attempt ${attempt+1}/${maxRetries})`);
            
            await page.goto(url, {waitUntil: 'networkidle0', timeout: 90000});
            await new Promise(r => setTimeout(r, 2000 + Math.random() * 3000)); // Wait for content
            
            // Check if the "Oops" error message is present
            const hasError = await page.evaluate(() => {
                const errorTexts = ['Oops', 'Something went wrong', 'network connectivity'];
                for (const text of errorTexts) {
                    const elements = document.querySelectorAll('div, h1, h2, h3, p, span');
                    for (const el of elements) {
                        if (el.innerText && el.innerText.includes(text)) {
                            return true;
                        }
                    }
                }
                return false;
            });
            
            if (hasError) {
                console.log(`Detected 'Oops' error message, retrying (attempt ${attempt+1}/${maxRetries})`);
                
                // Try to dismiss the error
                await page.evaluate(() => {
                    document.querySelectorAll('button').forEach(btn => {
                        if (btn.innerText.includes('Dismiss') || btn.innerText.includes('Close') || btn.innerText.includes('OK')) {
                            btn.click();
                        }
                    });
                });
                
                // Wait and try a different approach
                await new Promise(r => setTimeout(r, 5000 + Math.random() * 5000));
                
                // Try a browser refresh
                await page.reload({waitUntil: 'networkidle0', timeout: 60000});
                await new Promise(r => setTimeout(r, 2000 + Math.random() * 2000));
                
                // Use a different user agent
                const newAgent = userAgents.find(ua => ua !== selectedAgent) || userAgents[0];
                await page.setUserAgent(newAgent);
                
                // Add some human-like scrolling
                let scrollPos = 0;
                for (let i = 0; i < Math.floor(Math.random() * 5) + 3; i++) {
                    const scrollAmount = Math.floor(Math.random() * 400) + 300;
                    scrollPos += scrollAmount;
                    await page.evaluate((pos) => window.scrollTo(0, pos), scrollPos);
                    await new Promise(r => setTimeout(r, Math.random() * 500 + 500));
                }
                
                // Scroll back to top
                await page.evaluate(() => window.scrollTo(0, 0));
                await new Promise(r => setTimeout(r, Math.random() * 1000 + 1000));
                
                // Try navigating again
                await page.goto(url, {waitUntil: 'networkidle0', timeout: 90000});
                await new Promise(r => setTimeout(r, Math.random() * 2000 + 2000));
                
                // Check if error is still present
                const stillHasError = await page.evaluate(() => {
                    const errorTexts = ['Oops', 'Something went wrong', 'network connectivity'];
                    for (const text of errorTexts) {
                        const elements = document.querySelectorAll('div, h1, h2, h3, p, span');
                        for (const el of elements) {
                            if (el.innerText && el.innerText.includes(text)) {
                                return true;
                            }
                        }
                    }
                    return false;
                });
                
                if (!stillHasError) {
                    success = true;
                    break;
                }
            } else {
                success = true;
                break;
            }
        }
        
        // Remove any overlay or popup
        await page.evaluate(() => {
            // Remove modals and overlays
            const elementsToRemove = [
                '.popup', '.modal', '.overlay', '.cookie-banner',
                '[class*="popup"]', '[class*="modal"]', '[class*="overlay"]',
                '[class*="cookie"]', '[class*="consent"]',
                'div[role="dialog"]', 'div[aria-modal="true"]',
                '.fade', '.modal-backdrop'
            ];
            
            elementsToRemove.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    if(el) el.remove();
                });
            });
            
            // Re-enable scrolling
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        });
        
        await new Promise(r => setTimeout(r, 1000));
        
        // Save screenshot
        console.log("Taking screenshot");
        await page.screenshot({path: screenshotPath, fullPage: true, quality: 100});
        
        // Save HTML content
        console.log("Saving HTML content");
        const htmlContent = await page.content();
        fs.writeFileSync(htmlPath, htmlContent);
        
        await browser.close();
        return success;
    } catch (error) {
        console.error(`Error: ${error.message}`);
        if (browser) {
            await browser.close();
        }
        return false;
    }
}

// Execute the function
captureScreenshot()
    .then(success => {
        console.log(success ? "Screenshot captured successfully" : "Failed to capture screenshot");
        process.exit(success ? 0 : 1);
    })
    .catch(error => {
        console.error(`Unexpected error: ${error.message}`);
        process.exit(1);
    });