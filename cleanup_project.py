#!/usr/bin/env python3
"""
Script to clean up unnecessary files in the Snap Lotto project.
This script will move all non-essential files to an 'archived_scripts' folder.
"""

import os
import shutil
from datetime import datetime

def read_essential_files():
    """Read the list of essential files from essential_files_list.txt"""
    essential_files = []
    with open('essential_files_list.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                essential_files.append(line)
    return essential_files

def is_essential(file_path, essential_files):
    """Check if a file or folder is in the essential list"""
    # Check direct match
    if file_path in essential_files:
        return True
    
    # Check if it's in an essential folder
    for essential in essential_files:
        if essential.endswith('/') and file_path.startswith(essential):
            return True
        
    return False

def cleanup_project():
    """Move non-essential files to the archived_scripts folder"""
    # Create archived_scripts folder if it doesn't exist
    archive_dir = 'archived_scripts'
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    # Timestamp for the archive
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_file = f"{archive_dir}/archive_manifest_{timestamp}.txt"
    
    # Read the list of essential files
    essential_files = read_essential_files()
    
    # Create manifest file
    with open(archive_file, 'w') as manifest:
        manifest.write(f"# Archive created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        manifest.write("# The following files were moved to the archived_scripts folder:\n\n")
        
        # Get all files in the current directory
        for root, dirs, files in os.walk('.', topdown=True):
            # Skip the archived_scripts folder and any hidden directories
            dirs[:] = [d for d in dirs if d != archive_dir and not d.startswith('.')]
            
            for file in files:
                # Skip the essential_files_list.txt, cleanup_project.py, and this script itself
                if file in ['essential_files_list.txt', 'cleanup_project.py', os.path.basename(__file__)]:
                    continue
                
                file_path = os.path.join(root, file)
                # Remove './' prefix for comparison
                compare_path = file_path[2:] if file_path.startswith('./') else file_path
                
                # If not essential, move to archive
                if not is_essential(compare_path, essential_files):
                    # Create destination directory if it doesn't exist
                    dest_dir = os.path.join(archive_dir, os.path.dirname(compare_path))
                    if dest_dir != archive_dir and not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    
                    # Archive path
                    dest_path = os.path.join(archive_dir, compare_path)
                    
                    # Move the file
                    try:
                        shutil.move(file_path, dest_path)
                        manifest.write(f"{compare_path} -> {dest_path}\n")
                        print(f"Archived: {compare_path}")
                    except Exception as e:
                        manifest.write(f"Failed to archive {compare_path}: {str(e)}\n")
                        print(f"Failed to archive: {compare_path} - {str(e)}")
    
    print(f"\nCleanup complete. Manifest saved to {archive_file}")
    print(f"Non-essential files have been moved to the {archive_dir} folder.")
    print("If you need to recover any file, you can find it there.")

if __name__ == "__main__":
    cleanup_project()