"""
    Clones Github Repository and stores files and folders in local storage
"""

# Imports
from git import Repo
from uuid import uuid4

from backend.app.core.config_loader import config
from backend.app.core.path_constants import REPOS_DIR
from backend.app.core.logger import get_logger

# Get logger object
logger = get_logger()

class RepoCloner:

    """
        Takes Github Repository URL and required branch as input, loads the Repository and stores all contents in local storage

        Input: repository_url (str), branch (str)
        Output: dict status_message (str), path_to_repo (str)}
    """

    def __init__(self, repository_url: str, branch: str):
        self.repository_url = repository_url
        self.branch_name = branch
        self.repo_id = str(uuid4())
        self.path_to_repo = REPOS_DIR / self.repo_id
        self.path_to_repo.mkdir(parents=True, exist_ok=True)
    
    def save_repo(self) -> dict:
        
        """
            Clones repository files and folders in local folder
        """
        
        logger.info(f"[{self.repo_id}] Cloning repo from {self.repository_url}")

        try:

            if not self.repository_url.startswith("https://github.com/"):
                logger.error(f"Invalid Github repository URL: {self.repository_url}")
                raise ValueError("Invalid GitHub repository URL")
            
            if any(self.path_to_repo.iterdir()):
                logger.warning("Repo already exists. Skipping clone.")
                return {
                    "repo_id": self.repo_id,
                    "repo_path": str(self.path_to_repo),
                    "status": "already_exists"
                }
            
            Repo.clone_from(
                url = self.repository_url,
                to_path = self.path_to_repo,
                branch = self.branch_name,
                depth = 1
            )

            logger.info("Repository successfully cloned.")
            logger.info(f"Repository saved at: {self.path_to_repo}")
            
            return {
                "repo_id": self.repo_id,
                "repo_path": str(self.path_to_repo),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error while cloning repository: {e}")
            raise RuntimeError(f"Failed to clone repo: {e}")