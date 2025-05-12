"""
Popup Remover Injection Script

This script accepts a raw HTML file as input and injects CSS and JavaScript
to automatically remove popup messages, especially "Oops! Something went wrong!" errors.
"""

import os
import sys

def inject_popup_remover(html_path, output_path=None):
    """
    Injects CSS and JavaScript to remove popups from an HTML file
    
    Args:
        html_path (str): Path to the input HTML file
        output_path (str, optional): Path to save the modified HTML file.
                                    If None, overwrites the input file.
    
    Returns:
        bool: Success status
    """
    if output_path is None:
        output_path = html_path
    
    try:
        # Read the original HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # CSS to hide popups and error messages
        popup_remover_css = """
<style>
/* Hide any popups, error messages, or overlays */
.popup, .overlay, .modal, .cookie-banner, .consent-banner, 
div[class*="popup"], div[class*="modal"], div[class*="overlay"], 
div[class*="cookie"], div[class*="consent"],
div[role="dialog"], div[aria-modal="true"], .fade {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Target specific Oops message elements */
div[class*="error"], div[id*="error"],
[class*="error"], [id*="error"],
[class*="modal"], [id*="modal"] {
    display: none !important;
    visibility: hidden !important;
}

/* Remove modal backdrops */
body.modal-open {
    overflow: auto !important;
}

/* Remove fixed position elements that could be popups */
body > div[style*="position: fixed"],
body > div[style*="position:fixed"] {
    display: none !important;
}

/* Specifically target the "Oops!" popup */
div.modal, div.popup, div.overlay,
[class*="modal"], [class*="popup"], [class*="overlay"],
[aria-modal="true"], [role="dialog"] {
    display: none !important;
}

/* For the specific popup structure shown in the example */
div[aria-modal="true"],
div.modal-dialog,
div.modal-content,
div.modal-header,
div.modal-body,
.modal-backdrop {
    display: none !important;
}
</style>
"""
        
        # JavaScript to remove popups
        popup_remover_js = """
<script>
// Execute when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Remove popups immediately
    removePopups();
    
    // Then periodically check for new popups (sometimes they're added dynamically)
    setInterval(removePopups, 500);
});

// Function to remove all types of popups and error messages
function removePopups() {
    // Common popup selectors
    const elementsToRemove = [
        '.popup', '.modal', '.overlay', '.cookie-banner',
        '[class*="popup"]', '[class*="modal"]', '[class*="overlay"]',
        '[class*="cookie"]', '[class*="consent"]', '[class*="error"]',
        'div[role="dialog"]', 'div[aria-modal="true"]',
        '.fade', '.modal-backdrop'
    ];
    
    // Remove elements matching selectors
    elementsToRemove.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
            if(el) el.remove();
        });
    });
    
    // Remove elements containing "Oops" text
    document.querySelectorAll('div, h1, h2, h3, p, span').forEach(el => {
        if(el && el.innerText && 
           (el.innerText.includes('Oops') || 
            el.innerText.includes('Something went wrong') || 
            el.innerText.includes('network connectivity'))) {
            
            // Try to find parent modal/popup container
            let parent = el.parentElement;
            for(let i=0; i<5 && parent; i++) {
                if(parent.tagName === 'BODY') break;
                parent = parent.parentElement;
            }
            
            // Hide the parent container if found, otherwise hide the element itself
            if(parent && parent.tagName !== 'BODY') {
                parent.style.display = 'none';
            } else {
                el.style.display = 'none';
            }
        }
    });
    
    // Remove fixed position elements (often overlays/modals)
    document.querySelectorAll('body > div').forEach(el => {
        const style = window.getComputedStyle(el);
        if(style.position === 'fixed' && 
           (style.zIndex === 'auto' || parseInt(style.zIndex) > 100)) {
            el.style.display = 'none';
        }
    });
    
    // Re-enable scrolling if it was disabled by a modal
    document.body.style.overflow = 'auto';
    document.documentElement.style.overflow = 'auto';
}
</script>
"""
        
        # Inject CSS into <head>
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', '<head>\n' + popup_remover_css)
        else:
            # If no head tag, add it before the body or at the beginning
            if '<body>' in html_content:
                html_content = html_content.replace('<body>', popup_remover_css + '\n<body>')
            else:
                html_content = popup_remover_css + html_content
        
        # Inject JavaScript right before </body> closure
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', popup_remover_js + '\n</body>')
        else:
            # If no body end tag, add it at the end
            html_content = html_content + '\n' + popup_remover_js
        
        # Write the modified content to the output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return True
    
    except Exception as e:
        print(f"Error injecting popup remover: {str(e)}")
        return False

if __name__ == "__main__":
    # Simple command-line interface
    if len(sys.argv) < 2:
        print("Usage: python inject_popup_remover.py <html_file_path> [output_path]")
        sys.exit(1)
    
    html_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(html_path):
        print(f"Error: File {html_path} not found")
        sys.exit(1)
    
    success = inject_popup_remover(html_path, output_path)
    if success:
        print(f"Successfully injected popup remover into {output_path or html_path}")
    else:
        print(f"Failed to inject popup remover")
        sys.exit(1)