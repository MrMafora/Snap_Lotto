"""
Screenshot Archival System
Manages historical storage of lottery screenshots that yielded successful results
"""

import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ScreenshotArchivalSystem:
    """
    Manages archival of successful lottery screenshots with metadata
    """
    
    def __init__(self, archive_base_path: str = "screenshots_archive"):
        self.archive_base_path = archive_base_path
        self._ensure_archive_structure()
    
    def _ensure_archive_structure(self):
        """Ensure the archive folder structure exists"""
        if not os.path.exists(self.archive_base_path):
            os.makedirs(self.archive_base_path)
            logger.info(f"Created archive base path: {self.archive_base_path}")
    
    def archive_successful_screenshot(
        self, 
        screenshot_path: str, 
        lottery_type: str, 
        draw_number: int,
        draw_date: str,
        confidence: float,
        database_id: int
    ) -> Dict[str, any]:
        """
        Archive a screenshot that successfully yielded lottery results
        
        Args:
            screenshot_path: Path to the screenshot file
            lottery_type: Type of lottery (e.g., 'LOTTO', 'POWERBALL')
            draw_number: Draw number extracted
            draw_date: Draw date (YYYY-MM-DD format)
            confidence: AI extraction confidence score
            database_id: ID of the created database record
            
        Returns:
            Dict with archival status and details
        """
        try:
            if not os.path.exists(screenshot_path):
                return {
                    'success': False,
                    'error': f'Screenshot file not found: {screenshot_path}'
                }
            
            # Parse date to organize by year/month
            date_obj = datetime.strptime(draw_date, '%Y-%m-%d')
            year = date_obj.strftime('%Y')
            month = date_obj.strftime('%m')
            
            # Create year/month folder structure
            archive_folder = os.path.join(self.archive_base_path, year, month)
            os.makedirs(archive_folder, exist_ok=True)
            
            # Create descriptive filename with metadata
            original_filename = os.path.basename(screenshot_path)
            lottery_safe_name = lottery_type.replace(' ', '_').lower()
            archived_filename = f"{draw_date}_{lottery_safe_name}_draw{draw_number}_{original_filename}"
            archived_path = os.path.join(archive_folder, archived_filename)
            
            # Copy screenshot to archive
            shutil.copy2(screenshot_path, archived_path)
            
            # Create metadata file
            metadata = {
                'lottery_type': lottery_type,
                'draw_number': draw_number,
                'draw_date': draw_date,
                'ai_confidence': confidence,
                'database_id': database_id,
                'original_filename': original_filename,
                'archived_at': datetime.now().isoformat(),
                'screenshot_size_bytes': os.path.getsize(screenshot_path)
            }
            
            metadata_filename = archived_filename.replace('.png', '_metadata.json')
            metadata_path = os.path.join(archive_folder, metadata_filename)
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Archived screenshot: {archived_filename}")
            
            return {
                'success': True,
                'archived_path': archived_path,
                'metadata_path': metadata_path,
                'archive_folder': archive_folder
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to archive screenshot {screenshot_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_archived_screenshots(
        self, 
        lottery_type: Optional[str] = None,
        year: Optional[str] = None,
        month: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve list of archived screenshots with optional filters
        
        Args:
            lottery_type: Filter by lottery type
            year: Filter by year (YYYY)
            month: Filter by month (MM)
            
        Returns:
            List of dictionaries with screenshot metadata
        """
        archived_items = []
        
        try:
            # Determine search path
            if year and month:
                search_path = os.path.join(self.archive_base_path, year, month)
            elif year:
                search_path = os.path.join(self.archive_base_path, year)
            else:
                search_path = self.archive_base_path
            
            if not os.path.exists(search_path):
                return archived_items
            
            # Walk through archive folder
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.endswith('_metadata.json'):
                        metadata_path = os.path.join(root, file)
                        
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            
                            # Apply lottery type filter if specified
                            if lottery_type and metadata.get('lottery_type') != lottery_type:
                                continue
                            
                            # Add file paths
                            screenshot_filename = file.replace('_metadata.json', '')
                            metadata['screenshot_path'] = os.path.join(root, screenshot_filename)
                            metadata['metadata_path'] = metadata_path
                            
                            archived_items.append(metadata)
                            
                        except Exception as e:
                            logger.warning(f"Failed to read metadata {metadata_path}: {e}")
            
            # Sort by date descending
            archived_items.sort(key=lambda x: x.get('draw_date', ''), reverse=True)
            
            return archived_items
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve archived screenshots: {e}")
            return []
    
    def get_archive_statistics(self) -> Dict:
        """
        Get statistics about archived screenshots
        
        Returns:
            Dict with archive statistics
        """
        try:
            all_archives = self.get_archived_screenshots()
            
            if not all_archives:
                return {
                    'total_screenshots': 0,
                    'lottery_types': {},
                    'oldest_date': None,
                    'newest_date': None,
                    'total_size_mb': 0
                }
            
            lottery_counts = {}
            total_size = 0
            dates = []
            
            for archive in all_archives:
                # Count by lottery type
                lottery_type = archive.get('lottery_type', 'Unknown')
                lottery_counts[lottery_type] = lottery_counts.get(lottery_type, 0) + 1
                
                # Track dates
                if archive.get('draw_date'):
                    dates.append(archive['draw_date'])
                
                # Sum file sizes
                if os.path.exists(archive.get('screenshot_path', '')):
                    total_size += os.path.getsize(archive['screenshot_path'])
            
            return {
                'total_screenshots': len(all_archives),
                'lottery_types': lottery_counts,
                'oldest_date': min(dates) if dates else None,
                'newest_date': max(dates) if dates else None,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get archive statistics: {e}")
            return {'error': str(e)}
    
    def cleanup_old_archives(self, days_to_keep: int = 365) -> Dict:
        """
        Clean up archived screenshots older than specified days
        
        Args:
            days_to_keep: Number of days to retain archives
            
        Returns:
            Dict with cleanup results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            all_archives = self.get_archived_screenshots()
            removed_count = 0
            
            for archive in all_archives:
                if archive.get('draw_date', '9999-99-99') < cutoff_str:
                    # Remove screenshot and metadata
                    try:
                        if os.path.exists(archive.get('screenshot_path', '')):
                            os.remove(archive['screenshot_path'])
                        if os.path.exists(archive.get('metadata_path', '')):
                            os.remove(archive['metadata_path'])
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove old archive: {e}")
            
            logger.info(f"🗑️ Cleaned up {removed_count} old archived screenshots")
            
            return {
                'success': True,
                'removed_count': removed_count,
                'cutoff_date': cutoff_str
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old archives: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def archive_screenshot(screenshot_path: str, lottery_data: Dict) -> bool:
    """
    Convenience function to archive a single screenshot
    
    Args:
        screenshot_path: Path to screenshot file
        lottery_data: Dictionary with lottery result data
        
    Returns:
        Boolean indicating success
    """
    archival_system = ScreenshotArchivalSystem()
    
    result = archival_system.archive_successful_screenshot(
        screenshot_path=screenshot_path,
        lottery_type=lottery_data.get('lottery_type', 'UNKNOWN'),
        draw_number=lottery_data.get('draw_id', 0),
        draw_date=lottery_data.get('draw_date', datetime.now().strftime('%Y-%m-%d')),
        confidence=lottery_data.get('extraction_confidence', 0),
        database_id=lottery_data.get('database_id', 0)
    )
    
    return result.get('success', False)


if __name__ == "__main__":
    # Test the archival system
    logging.basicConfig(level=logging.INFO)
    
    archival = ScreenshotArchivalSystem()
    
    # Get statistics
    stats = archival.get_archive_statistics()
    print(f"Archive Statistics: {json.dumps(stats, indent=2)}")
