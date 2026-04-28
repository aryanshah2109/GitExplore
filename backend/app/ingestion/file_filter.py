"""
    Utility file for ingestion with filters to apply on cloned repository
"""

# Imports
from pathlib import Path

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger

# Get logger object
logger = get_logger()

class FileFilter:

    """
        Class that selects correct cloned repository from local storage and decides which files and folders to
        skip based on file extensions, folder types, size of files, etc.        
    """

    def __init__(self):
        self.supported_extensions = config.ingestion.supported_extensions
        self.skip_dirs = config.ingestion.skip_dirs
        self.skip_files = config.ingestion.skip_files
        self.max_size_file = config.ingestion.max_size_file
    
    def should_include_filter(self, saved_file_path: str) -> bool:

        """
            Filters files and folders and Returns True if the file should be processed further in the ingestion pipeline 
            and False if it should not be included. This will later be used to create manifests useful for chunking.

            Input: saved_file_path (str)
            Output: include (bool)
        """
        
        logger.info(f"Filtering {saved_file_path} to decide whether it will be useful or not")

        try:

            file_path = Path(saved_file_path)

            if not file_path.is_file():
                logger.debug(f"{file_path} is not a valid item path")
                return False
            

            if file_path.name.startswith("."):
                logger.debug(f"{file_path} is a hidden item.")
                return False

            if file_path.suffix.lower() not in self.supported_extensions:
                logger.debug(f"{file_path} is not a valid code path based on allowed extensions.")
                return False

            if any(part in self.skip_dirs for part in file_path.parts):
                logger.debug(f"{file_path} is not an allowed directory.")
                return False
            
            if file_path.name in self.skip_files:
                logger.debug(f"{file_path} is not an allowed file.")
                return False
            
            file_stat = file_path.stat()

            if file_stat.st_size == 0:
                logger.debug(f"{file_path} is of 0 bytes size")
                return False
            
            if file_stat.st_size >= self.max_size_file:
                logger.debug(f"{file_path} is of very large size")
                return False
            
            logger.info(f"{file_path} has passed all filters and is valid")
            return True

        except Exception as e:
            logger.error(f"Error while filtering item {file_path}: {e}")
            return False