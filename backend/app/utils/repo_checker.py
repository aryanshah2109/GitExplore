"""Look for an already-processed repo before starting a new clone."""

from backend.app.core.path_constants import MANIFESTS_DIR
from backend.app.core.logger import get_logger

import json
from pathlib import Path

logger = get_logger()

def check_repo_exists(repo_url: str, branch_name: str):
    """Return the repo id when the same repo and branch already exist."""
    try:
        for manifest_file_path in MANIFESTS_DIR.rglob("*.json"):

            with open(manifest_file_path) as file:
                manifest_data = json.load(file)

            if repo_url == manifest_data["repo_url"] and branch_name == manifest_data["branch_name"]:
                logger.info(f"Same repository already exists at path {manifest_file_path}")
                return manifest_data["repo_id"]
            
        return None
    
    except Exception as e:
        logger.error(f"Error while looking for same repo existing in storage: {e}")
    
