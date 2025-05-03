# Screenshots Directory

This directory contains screenshot images of lottery results pages. These screenshots are used by the application for:

1. OCR data extraction from lottery websites
2. Historical data archiving
3. Visual verification of lottery results

## Organization

The screenshots follow the naming pattern:
`YYYYMMDD_HHMMSS_lottery-type.png`

For example:
`20250502_032622_daily-lotto.png`

## Maintenance

The application automatically:
- Takes new screenshots daily at 2 AM SAST
- Archives old screenshots in the database
- Processes screenshots for data extraction

*Last updated: May 3, 2025*
