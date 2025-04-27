#!/bin/bash
# Import data from Excel file
# Usage: ./import_data.sh <excel_file_path> [sheet_name]

# Check if the file exists
if [ ! -f "$1" ]; then
  echo "Error: File $1 not found!"
  exit 1
fi

# Run the import script
echo "Importing data from $1..."
if [ -z "$2" ]; then
  python import_excel_data.py "$1"
else
  python import_excel_data.py "$1" --sheet "$2"
fi

# Check the result
if [ $? -eq 0 ]; then
  echo "Import completed successfully!"
else
  echo "Import completed with errors. See log for details."
fi