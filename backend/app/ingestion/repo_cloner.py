"""
    Clones Github Repository and stores files and folders in local storage
"""

from git import Repo, GitCommandError
from uuid import uuid4
import shutil
import requests

from backend.app.core.path_constants import REPOS_DIR
from backend.app.core.logger import get_logger

logger = get_logger()


class RepoCloner:

    """
        Takes Github Repository URL and required branch as input, loads the Repository and stores all contents in local storage

        Input: repository_url (str), branch (str)
        Output: dict status_message (str), path_to_repo (str)}
    """

    def __init__(self, repository_url: str, branch: str | None):
        self.repository_url = repository_url
        self.branch_name = branch.strip() if branch else None
        self.repo_id = str(uuid4())
        self.path_to_repo = REPOS_DIR / self.repo_id
        self.path_to_repo.mkdir(parents=True, exist_ok=True)

    def _get_default_branch(self) -> str:

        repo_url = self.repository_url.rstrip("/")

        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]

        parts = repo_url.split("/")

        if len(parts) < 2:
            raise ValueError("Invalid GitHub repository URL")

        owner = parts[-2]
        repo = parts[-1]

        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            timeout=15,
        )

        response.raise_for_status()

        return response.json()["default_branch"]

    def _clone(self, branch: str):

        Repo.clone_from(
            url=self.repository_url,
            to_path=self.path_to_repo,
            branch=branch,
            depth=1,
        )

    def save_repo(self) -> dict:

        """
            Clones repository files and folders in local folder
        """

        logger.info(f"[{self.repo_id}] Cloning repo from {self.repository_url}")

        try:

            if not self.repository_url.startswith("https://github.com/"):
                logger.error(f"Invalid Github repository URL: {self.repository_url}")
                raise ValueError("Invalid GitHub repository URL")

            branch_to_use = self.branch_name

            if not branch_to_use:
                branch_to_use = self._get_default_branch()
                logger.info(f"Using default branch: {branch_to_use}")

            try:

                self._clone(branch_to_use)

            except GitCommandError as e:

                error_text = str(e)

                if (
                    "Remote branch" in error_text
                    and "not found" in error_text
                ):

                    logger.warning(
                        f"Branch '{branch_to_use}' not found. Falling back to repository default branch."
                    )

                    if self.path_to_repo.exists():
                        shutil.rmtree(self.path_to_repo, ignore_errors=True)

                    self.path_to_repo.mkdir(parents=True, exist_ok=True)

                    default_branch = self._get_default_branch()

                    logger.info(
                        f"Retrying clone using default branch '{default_branch}'"
                    )

                    self._clone(default_branch)

                else:
                    raise

            logger.info("Repository successfully cloned.")
            logger.info(f"Repository saved at: {self.path_to_repo}")

            return {
                "repo_id": self.repo_id,
                "repo_path": str(self.path_to_repo),
            }

        except Exception as e:

            if self.path_to_repo.exists():
                shutil.rmtree(self.path_to_repo, ignore_errors=True)

            logger.error(f"Error while cloning repository: {e}")

            message = str(e)

            if "Remote branch" in message and "not found" in message:
                raise RuntimeError(
                    f"Branch '{self.branch_name}' does not exist in this repository."
                )

            raise RuntimeError(f"Failed to clone repo: {e}")