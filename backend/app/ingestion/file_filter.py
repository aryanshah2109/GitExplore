"""
    Utility file for ingestion with filters to apply on a given file path
"""

# Imports
from pathlib import Path

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger

# Get logger object
logger = get_logger()

class FileFilter:

    """
        Class that takes a file path and decides whether the file is valid or not based on file extensions, folder types, 
        size of files, etc.        
    """

    def __init__(self):
        self.supported_extensions = config.ingestion.supported_extensions
        self.skip_dirs = config.ingestion.skip_dirs
        self.skip_files = config.ingestion.skip_files
        self.max_size_file = config.ingestion.max_size_file
    
    def should_include_filter(self, file_path: Path, repo_root: Path) -> bool:

        """
            Filters files and folders and Returns True if the file should be processed further in the ingestion pipeline 
            and False if it should not be included. This will later be used to create manifests useful for chunking.

            Input: saved_file_path (str)
            Output: include (bool)
        """
        relative_path = file_path.relative_to(repo_root)

        try:

            if not file_path.is_file():
                return False
            

            if file_path.name.startswith("."):
                logger.debug(f"{relative_path} is a hidden item.")
                return False

            if file_path.suffix.lower() not in self.supported_extensions:
                logger.debug(f"{relative_path} is not a valid code path based on allowed extensions.")
                return False

            if any(part in self.skip_dirs for part in file_path.parts):
                logger.debug(f"{relative_path} is not an allowed directory.")
                return False
            
            if file_path.name in self.skip_files:
                logger.debug(f"{relative_path} is not an allowed file.")
                return False
            
            file_stat = file_path.stat()

            if file_stat.st_size == 0:
                logger.debug(f"{relative_path} is of 0 bytes size")
                return False
            
            if file_stat.st_size >= self.max_size_file:
                logger.debug(f"{relative_path} is of very large size")
                return False
            
            return True

        except Exception as e:
            logger.error(f"Error while filtering item {relative_path}: {e}")
            return False