#!/usr/bin/env python3
"""
Cleanup Orphaned Screenshots
Removes PNG files that don't have corresponding metadata files
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_orphaned_screenshots(archive_path="screenshots_archive", dry_run=True):
    """Remove PNG files without corresponding metadata"""
    
    orphaned_files = []
    
    for root, dirs, files in os.walk(archive_path):
        for file in files:
            if file.endswith('.png'):
                metadata_file = file.replace('.png', '_metadata.json')
                metadata_path = os.path.join(root, metadata_file)
                
                if not os.path.exists(metadata_path):
                    orphaned_files.append(os.path.join(root, file))
    
    logger.info(f"🔍 Found {len(orphaned_files)} orphaned PNG files without metadata")
    
    if not orphaned_files:
        logger.info("✅ No orphaned files found!")
        return {'orphaned_count': 0, 'removed_count': 0}
    
    if dry_run:
        logger.info("\n📋 Orphaned files that would be removed:")
        for path in orphaned_files:
            logger.info(f"  - {os.path.basename(path)}")
        logger.info(f"\n🔍 DRY RUN - Run with dry_run=False to actually remove {len(orphaned_files)} files")
        return {'orphaned_count': len(orphaned_files), 'removed_count': 0, 'dry_run': True}
    
    # Actually remove files
    removed = 0
    for path in orphaned_files:
        try:
            os.remove(path)
            logger.info(f"🗑️  Removed: {os.path.basename(path)}")
            removed += 1
        except Exception as e:
            logger.error(f"❌ Failed to remove {path}: {e}")
    
    logger.info(f"\n✅ Removed {removed} orphaned screenshot files")
    return {'orphaned_count': len(orphaned_files), 'removed_count': removed, 'dry_run': False}

if __name__ == "__main__":
    # Dry run first
    result = cleanup_orphaned_screenshots(dry_run=True)
    print(f"\nResult: {result}")
