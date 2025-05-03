#!/bin/bash
# Simple bash script to capture all screenshots sequentially

echo "Capturing screenshots for all lottery types..."

# Run cleanup first
echo "Running initial cleanup..."
python capture_all_screenshots.py --cleanup

# Capture each lottery type
echo "Capturing Lotto..."
python capture_all_screenshots.py --index 0

echo "Capturing Powerball..."
python capture_all_screenshots.py --index 3

echo "Capturing Powerball Plus..."
python capture_all_screenshots.py --index 4 

echo "Capturing Daily Lotto..."
python capture_all_screenshots.py --index 5

# Run final cleanup
echo "Running final cleanup..."
python capture_all_screenshots.py --cleanup

echo "Done!"