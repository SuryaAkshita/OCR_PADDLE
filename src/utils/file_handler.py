"""
File handling utilities
"""
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Handle file I/O operations"""
    
    @staticmethod
    def save_text(content: str, output_path: str) -> None:
        """
        Save text content to file
        
        Args:
            content: Text content
            output_path: Output file path
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved text to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving text file: {e}")
            raise
    
    @staticmethod
    def save_json(data: Dict, output_path: str, pretty: bool = True) -> None:
        """
        Save data as JSON
        
        Args:
            data: Dictionary to save
            output_path: Output file path
            pretty: Pretty print JSON (default: True)
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            logger.info(f"Saved JSON to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")
            raise
    
    @staticmethod
    def load_json(file_path: str) -> Dict:
        """
        Load JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dictionary from JSON
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded JSON from {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            raise
    
    @staticmethod
    def create_output_structure(base_name: str, output_dir: Path) -> Dict[str, Path]:
        """
        Create organized output directory structure
        
        Args:
            base_name: Base name for output files
            output_dir: Base output directory
            
        Returns:
            Dictionary of output paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{base_name}_{timestamp}"
        
        paths = {
            'json': output_dir / 'json' / f"{output_name}.json",
            'text': output_dir / 'txt' / f"{output_name}.txt",
            'detailed': output_dir / 'json' / f"{output_name}_detailed.json",
        }
        
        # Create directories
        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        
        return paths
    
    @staticmethod
    def cleanup_temp_files(temp_dir: Path) -> None:
        """
        Clean up temporary files
        
        Args:
            temp_dir: Temporary directory to clean
        """
        try:
            if temp_dir.exists():
                for item in temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
                
        except Exception as e:
            logger.warning(f"Error cleaning temp files: {e}")
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        Get file information
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file info
        """
        try:
            path = Path(file_path)
            stat = path.stat()
            
            return {
                'name': path.name,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': path.suffix,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}