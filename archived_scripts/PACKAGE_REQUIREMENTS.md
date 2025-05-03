# Package Requirements Documentation

This document provides a clean, organized list of all the dependencies required for the lottery data project. This serves as documentation only and should not be used to replace the existing configuration files.

## Core Dependencies

### Web Framework
- flask>=3.1.0
- flask-login>=0.6.3
- flask-sqlalchemy>=3.1.1
- flask-wtf>=1.2.2
- werkzeug>=3.1.3
- wtforms>=3.2.1
- gunicorn>=23.0.0

### Database
- sqlalchemy>=2.0.40
- psycopg2-binary>=2.9.10

### Data Processing
- numpy>=2.2.4
- pandas>=2.2.3
- openpyxl>=3.1.5
- beautifulsoup4>=4.13.3
- trafilatura>=2.0.0

### Validation
- email-validator>=2.2.0

### Scheduler
- apscheduler>=3.11.0

### Web Scraping
- playwright>=1.51.0

### AI/OCR Integration
- anthropic>=0.49.0
- mistralai>=1.6.0
- openai>=1.71.0

### Additional Dependencies
- requests>=2.31.0

## Configuration Files

The project uses the following package configuration files:

1. **pyproject.toml** - Modern Python packaging configuration
2. **requirements.txt** - Traditional pip requirements file
3. **.pythonlibs/** - Directory containing installed libraries
4. **.upm/** - Package manager cache

> **Note**: Do not manually edit requirements.txt or attempt to reinstall packages as it may break the environment. The existing configuration works for the current deployment.

## Dependency Installation

If new dependencies need to be added, use the Replit packager tools rather than manually editing configuration files.