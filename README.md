# Snap Lotto

A Python-powered lottery data intelligence platform that automates sophisticated data capture, AI-driven extraction, and comprehensive result aggregation using advanced web scraping and OCR technologies.

## Features

- **Ticket Scanner**: Scan South African lottery tickets to check for winnings
- **Results Database**: Comprehensive database of historical lottery results
- **AI-Powered OCR**: Automated extraction of ticket numbers using Claude AI
- **Prize Calculation**: Automatic calculation of winnings based on matched numbers
- **Responsive Design**: Mobile-friendly interface for ease of use

## Technologies Used

- **Backend**: Python with Flask framework
- **OCR Processing**: Claude AI with advanced image recognition
- **Web Scraping**: Custom web scraper with browser emulation
- **Data Storage**: PostgreSQL database
- **Task Scheduling**: APScheduler for automated data collection
- **Frontend**: Bootstrap with responsive design

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Anthropic API key for Claude AI

### Environment Variables

The following environment variables need to be set:

- `DATABASE_URL`: PostgreSQL connection string
- `Lotto_scape_ANTHROPIC_KEY`: Anthropic API key for Claude
- `SESSION_SECRET`: Secret key for session security

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/username/snap-lotto.git
   cd snap-lotto
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Setup the database:
   ```
   # Database tables will be automatically created on first run
   ```

4. Run the application:
   ```
   python main.py
   ```

## License

Proprietary - All rights reserved

## Credits

- Created by the Snap Lotto Team
- Powered by Claude AI for OCR processing