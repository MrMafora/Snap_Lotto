#!/usr/bin/env python3
"""
Cleanup Archive Duplicates
Removes duplicate archived screenshots, keeping only the first (earliest) archive for each draw
"""

import os
import json
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArchiveDuplicateCleanup:
    """
    Manages cleanup of duplicate archived screenshots
    """
    
    def __init__(self, archive_base_path: str = "screenshots_archive"):
        self.archive_base_path = archive_base_path
    
    def find_all_archived_screenshots(self) -> List[Dict]:
        """
        Find all archived screenshots with their metadata
        
        Returns:
            List of dicts with screenshot info
        """
        archived_items = []
        
        try:
            for root, dirs, files in os.walk(self.archive_base_path):
                for file in files:
                    if file.endswith('_metadata.json'):
                        metadata_path = os.path.join(root, file)
                        
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            
                            # Get screenshot filename
                            screenshot_filename = file.replace('_metadata.json', '')
                            screenshot_path = os.path.join(root, screenshot_filename)
                            
                            # Add paths
                            metadata['screenshot_path'] = screenshot_path
                            metadata['metadata_path'] = metadata_path
                            metadata['archived_at_obj'] = datetime.fromisoformat(metadata.get('archived_at', ''))
                            
                            archived_items.append(metadata)
                            
                        except Exception as e:
                            logger.warning(f"Failed to read metadata {metadata_path}: {e}")
            
            return archived_items
            
        except Exception as e:
            logger.error(f"Failed to find archived screenshots: {e}")
            return []
    
    def identify_duplicates(self, archived_items: List[Dict]) -> Dict:
        """
        Identify duplicate screenshots for the same draw
        
        Args:
            archived_items: List of archived screenshot metadata
            
        Returns:
            Dict with duplicates organized by draw
        """
        # Group by lottery type and draw number
        draw_groups = defaultdict(list)
        
        for item in archived_items:
            key = (item.get('lottery_type'), item.get('draw_number'))
            draw_groups[key].append(item)
        
        # Find duplicates (groups with more than 1 screenshot)
        duplicates = {}
        
        for key, items in draw_groups.items():
            if len(items) > 1:
                # Sort by archived_at timestamp (keep earliest)
                items_sorted = sorted(items, key=lambda x: x.get('archived_at_obj'))
                
                duplicates[key] = {
                    'keep': items_sorted[0],
                    'remove': items_sorted[1:],
                    'total_count': len(items)
                }
        
        return duplicates
    
    def cleanup_duplicates(self, dry_run: bool = True) -> Dict:
        """
        Remove duplicate archived screenshots
        
        Args:
            dry_run: If True, only report what would be deleted without deleting
            
        Returns:
            Dict with cleanup results
        """
        logger.info("🔍 Scanning for duplicate archived screenshots...")
        
        # Find all archives
        all_archives = self.find_all_archived_screenshots()
        logger.info(f"📂 Found {len(all_archives)} total archived screenshots")
        
        # Identify duplicates
        duplicates = self.identify_duplicates(all_archives)
        
        if not duplicates:
            logger.info("✅ No duplicates found!")
            return {
                'success': True,
                'duplicates_found': 0,
                'files_removed': 0
            }
        
        logger.info(f"⚠️  Found {len(duplicates)} draws with duplicate archives")
        
        # Calculate total files to remove
        total_to_remove = sum(len(dup['remove']) for dup in duplicates.values())
        total_files_to_delete = total_to_remove * 2  # Screenshot + metadata
        
        logger.info(f"🗑️  Will remove {total_to_remove} duplicate screenshots ({total_files_to_delete} files)")
        
        removed_count = 0
        
        for (lottery_type, draw_number), dup_info in duplicates.items():
            logger.info(f"\n📋 {lottery_type} Draw {draw_number}:")
            logger.info(f"   ✅ Keeping: {os.path.basename(dup_info['keep']['screenshot_path'])}")
            logger.info(f"   🗑️  Removing {len(dup_info['remove'])} duplicate(s)")
            
            for item in dup_info['remove']:
                screenshot_path = item['screenshot_path']
                metadata_path = item['metadata_path']
                
                logger.info(f"      - {os.path.basename(screenshot_path)}")
                
                if not dry_run:
                    try:
                        # Remove screenshot
                        if os.path.exists(screenshot_path):
                            os.remove(screenshot_path)
                        
                        # Remove metadata
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                        
                        removed_count += 1
                        
                    except Exception as e:
                        logger.error(f"      ❌ Failed to remove: {e}")
        
        if dry_run:
            logger.info(f"\n🔍 DRY RUN - No files were actually deleted")
            logger.info(f"Run with dry_run=False to perform actual cleanup")
        else:
            logger.info(f"\n✅ Cleanup complete! Removed {removed_count} duplicate screenshots")
        
        return {
            'success': True,
            'duplicates_found': len(duplicates),
            'files_removed': removed_count if not dry_run else 0,
            'dry_run': dry_run
        }
    
    def get_cleanup_summary(self) -> Dict:
        """
        Get summary of what would be cleaned up without actually cleaning
        
        Returns:
            Dict with cleanup summary
        """
        all_archives = self.find_all_archived_screenshots()
        duplicates = self.identify_duplicates(all_archives)
        
        summary = {
            'total_archives': len(all_archives),
            'unique_draws': len(set((item.get('lottery_type'), item.get('draw_number')) for item in all_archives)),
            'duplicated_draws': len(duplicates),
            'duplicate_files': sum(len(dup['remove']) for dup in duplicates.values()),
            'space_wasted_mb': 0
        }
        
        # Calculate wasted space
        for dup_info in duplicates.values():
            for item in dup_info['remove']:
                if os.path.exists(item['screenshot_path']):
                    summary['space_wasted_mb'] += os.path.getsize(item['screenshot_path'])
        
        summary['space_wasted_mb'] = round(summary['space_wasted_mb'] / (1024 * 1024), 2)
        
        return summary


if __name__ == "__main__":
    cleanup = ArchiveDuplicateCleanup()
    
    # First, get summary
    summary = cleanup.get_cleanup_summary()
    print("\n" + "="*60)
    print("📊 ARCHIVE DUPLICATE SUMMARY")
    print("="*60)
    print(f"Total archived screenshots: {summary['total_archives']}")
    print(f"Unique draws archived: {summary['unique_draws']}")
    print(f"Draws with duplicates: {summary['duplicated_draws']}")
    print(f"Duplicate files to remove: {summary['duplicate_files']}")
    print(f"Space wasted: {summary['space_wasted_mb']} MB")
    print("="*60 + "\n")
    
    # Dry run first
    print("Running DRY RUN (preview only)...\n")
    result = cleanup.cleanup_duplicates(dry_run=True)
    
    print("\n" + "="*60)
    print("To actually remove duplicates, run:")
    print("  python cleanup_archive_duplicates.py --execute")
    print("="*60)
