# Snap Lotto - South African Lottery Data Intelligence Platform

A Python-powered lottery data intelligence platform that automates sophisticated data capture, AI-driven extraction, and comprehensive result aggregation using advanced web scraping and OCR technologies.

## Optimized File Structure

This application has been optimized to reduce its size while maintaining full functionality:

- **Lightweight Core**: The main application uses lightweight dependencies for basic functionality
- **Optional Playwright**: Full browser automation with Playwright is available but optional
- **Modular Design**: Critical components like screenshot capture are isolated for easier maintenance

## Components

- **Python Flask Backend**: Core application server
- **Claude AI for OCR**: Advanced OCR processing of lottery tickets and results
- **Responsive Web Interface**: Mobile-friendly Bootstrap design
- **Admin Authentication**: Secure access for administrative functions
- **Scheduled Data Collection**: Automated data gathering via API or web screenshots

## Size Optimization

The application has been optimized to reduce its size:

1. **Lightweight Screenshot Capture**: Uses requests library for basic screenshot needs
2. **Optional Playwright Integration**: Full browser automation available only when needed
3. **Modular Architecture**: Components can be enabled/disabled as needed

## Getting Started

### Basic Installation (Small Footprint)

```bash
# Install required dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Full Installation (With Browser Automation)

If you need full browser automation for complex websites, install Playwright:

```bash
# Install Playwright
pip install playwright

# Install required browsers
playwright install chromium
```

## Environment Variables

The following environment variables are required:

- `Lotto_scape_ANTHROPIC_KEY`: API key for Claude AI OCR processing
- `SESSION_SECRET`: Secret key for Flask session security
- `DATABASE_URL`: PostgreSQL database connection string

## Features

- Ticket scanning with OCR technology
- Real-time data aggregation
- Comprehensive lottery result storage
- Admin dashboard for system management
- Scheduled data collection