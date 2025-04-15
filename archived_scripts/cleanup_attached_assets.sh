#!/bin/bash
# Script to clean up unnecessary files in attached_assets folder
# while preserving lottery images and essential documentation

echo "=== Cleaning up attached_assets folder ==="

# Create backup directory (just in case)
mkdir -p backup_assets
echo "Created backup directory: backup_assets"

# Categories to keep/organize
mkdir -p attached_assets/lottery_images # Ensure exists
mkdir -p attached_assets/essential_docs # For important documentation

# Move essential lottery documentation to essential_docs
if [ -f "attached_assets/documentation/lottery_data_template_20250413_222531.xlsx" ]; then
  echo "Preserving lottery data template..."
  mv "attached_assets/documentation/lottery_data_template_20250413_222531.xlsx" "attached_assets/essential_docs/"
fi

if [ -f "attached_assets/README.md" ]; then
  echo "Preserving README file..."
  cp "attached_assets/README.md" "attached_assets/essential_docs/"
fi

# Count files to be processed
total_files=$(find attached_assets -type f | grep -v "lottery_images\|essential_docs" | wc -l)
echo "Found $total_files files to process"

# Copy all files to backup (except lottery_images which we keep)
echo "Backing up files before deletion..."
find attached_assets -type f -not -path "*/lottery_images/*" -not -path "*/essential_docs/*" -exec cp {} backup_assets/ \;

# Remove unnecessary folders and their contents
echo "Removing unnecessary folders..."
rm -rf attached_assets/documentation
rm -rf attached_assets/other
rm -rf attached_assets/screenshots

# Remove all image files in root attached_assets directory
echo "Removing unnecessary image files..."
find attached_assets -maxdepth 1 -type f -name "image_*.png" -delete
find attached_assets -maxdepth 1 -type f -name "Screenshot*.png" -delete

# Remove all pasted text files
echo "Removing unnecessary text files..."
find attached_assets -maxdepth 1 -type f -name "Pasted-*.txt" -delete

# Count files kept
files_kept=$(find attached_assets -type f | wc -l)
files_removed=$((total_files - files_kept))

echo ""
echo "=== Cleanup Summary ==="
echo "Total files processed: $total_files"
echo "Files removed: $files_removed"
echo "Backup created: backup_assets/ (contains all removed files)"
echo "Preserved: attached_assets/lottery_images/ (lottery result images)"
echo "Preserved: attached_assets/essential_docs/ (essential documentation)"
echo ""
echo "Cleanup complete!"