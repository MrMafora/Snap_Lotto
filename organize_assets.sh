#!/bin/bash
# Script to organize the attached_assets directory by file type

# Create backup of the current state
echo "Creating backup of attached_assets directory..."
mkdir -p backup_assets
cp -r attached_assets/* backup_assets/ 2>/dev/null

# Create subdirectories for each file type
echo "Creating subdirectories for different file types..."
mkdir -p attached_assets/screenshots
mkdir -p attached_assets/documentation
mkdir -p attached_assets/lottery_images
mkdir -p attached_assets/other

# Move files to appropriate directories
echo "Organizing files by type..."

# Move all screenshots and PNG files to screenshots directory first
echo "Moving screenshots..."
find attached_assets -maxdepth 1 -name "Screenshot*.png" -exec mv {} attached_assets/screenshots/ \;
find attached_assets -maxdepth 1 -name "image_*.png" -exec mv {} attached_assets/screenshots/ \;

# Move lottery-related images to their own directory
echo "Moving lottery images..."
find attached_assets -maxdepth 1 -name "Lotto*.png" -exec mv {} attached_assets/lottery_images/ \;
find attached_assets -maxdepth 1 -name "*Lotto*.png" -exec mv {} attached_assets/lottery_images/ \;

# Move text and documentation files
echo "Moving documentation files..."
find attached_assets -maxdepth 1 -name "*.txt" -exec mv {} attached_assets/documentation/ \;
find attached_assets -maxdepth 1 -name "*.xlsx" -exec mv {} attached_assets/documentation/ \;

# Move remaining image files to other
echo "Moving remaining files..."
find attached_assets -maxdepth 1 -name "*.png" -exec mv {} attached_assets/other/ \;
find attached_assets -maxdepth 1 -name "*.jpeg" -exec mv {} attached_assets/other/ \;

echo "Asset organization complete!"
echo "Files are now organized in the following directories:"
echo "- attached_assets/screenshots/ - All screenshot PNG files"
echo "- attached_assets/lottery_images/ - Lottery-specific images"
echo "- attached_assets/documentation/ - Text and Excel files"
echo "- attached_assets/other/ - All other images"
echo ""
echo "Original files backed up to backup_assets/"