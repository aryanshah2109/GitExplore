"""
    Creates manifest for cloned repository files and saves it in directory
"""

from uuid import uuid4
import json
from pathlib import Path
from collections import Counter

from backend.app.ingestion.repo_cloner import RepoCloner
from backend.app.ingestion.file_filter import FileFilter
from backend.app.ingestion.language_detector import LanguageDetector
from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.core.path_constants import MANIFESTS_DIR

# Get logger object
logger = get_logger()

class ManifestBuilder:
    """
        Class to build manifest for cloned repository

        Input: repo_root: Path, repo_url: str, branch_name: str
        Output: manifests_dir: Path
    """

    def __init__(self, repo_root: Path, repo_url: str, branch_name: str):
        MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

        self.repo_root = repo_root.resolve()
        self.repo_id = self.repo_root.name
        self.repo_url = repo_url
        self.branch_name = branch_name
        self.manifest = {}
        self.valid_files_count = 0
        self.saved_manifest_path = MANIFESTS_DIR / f"{self.repo_id}.json"
        self.file_filter_object = FileFilter()
        self.language_detector_object = LanguageDetector()
        

    def get_relative_path(self, file_path: Path, repo_root: Path) -> str:
        """
            Returns relative path of a file path with respect to a root path
            Input: file_path (pathlib.Path), repo_root (pathlib.Path)
            Output: relative_path (str)
        """

        try:
            return str(file_path.relative_to(repo_root))
        except ValueError:
            return str(file_path)

    def build_manifest(self) -> Path:
        """
            Builds manifest of a repository and returns path
        
        """

        try:

            self.manifest.update({
                "repo_id": self.repo_id,
                "repo_root": self.repo_root.as_posix(),
                "repo_url": self.repo_url,
                "repo_name": self.repo_url.split("/")[-1],
                "branch_name": self.branch_name,
                "files": [],
                "valid_files_count": 0,
                "languages_detected": Counter()
            })

            logger.info("Buidling manifest")

            for file_path in self.repo_root.rglob("*"):

                if not file_path.is_file():
                    continue

                relative_file_path = self.get_relative_path(file_path, self.repo_root)
                relative_file_path = Path(relative_file_path).as_posix()

                # filter
                if not self.file_filter_object.should_include_filter(file_path, self.repo_root):
                    continue

                # Detect language
                detected_language = self.language_detector_object.detect_language(file_path, self.repo_root)

                self.manifest["languages_detected"][detected_language] += 1

                self.manifest["valid_files_count"] += 1

                self.manifest["files"].append({
                    "file_id": str(uuid4()),
                    "file_path": relative_file_path,
                    "language": detected_language,
                    "extension": file_path.suffix.lower(),
                    "file_size": file_path.stat().st_size
                })

            # Saving manifest
            logger.info(f"Saving repository manifest. Path: {self.saved_manifest_path}")
            with self.saved_manifest_path.open("w", encoding="utf-8") as f:
                json.dump(self.manifest, f, indent=4)

            return self.saved_manifest_path


        except Exception as e:
            logger.error(f"Error while building manifest: {e}")
            return


            

