"""
    Utility file for ingestion with to detect language type of a given file path
"""

# Imports
from pathlib import Path

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger

# Get logger object
logger = get_logger()

class LanguageDetector:
    """
        Class that inputs a file path to detect programming language type of the file.
    """

    def __init__(self):
        self.extension_map = {
            k.lower(): v.lower()
            for k, v in config.ingestion.language_detection.items()
        }

    def detect_language(self, file_path: Path, repo_root: Path) -> str:
        try:

            relative_path = file_path.relative_to(repo_root)

            if file_path.is_file():
                # Extension based detection
                extension = file_path.suffix.lower()

                if not extension:
                    logger.info(f"Extension not found in {relative_path}")
                    return "unknown"

                language = self.extension_map.get(extension)
                if language:                    
                    logger.debug(f"{relative_path} = {language}")
                    return language
            
                logger.info(f"Could not find appropriate language from extension map")
                return "unknown"

            else:
                return "unknown"

        except Exception as e:
            logger.error(f"Error while detecting language of {relative_path}: {e}")
            return "unknown"
