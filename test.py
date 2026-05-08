from backend.app.ingestion.repo_cloner import RepoCloner
from backend.app.ingestion.manifest_builder import ManifestBuilder

from pathlib import Path
from pprint import pprint
from uuid import uuid4
import json

from backend.app.core.logger import configure_logger

configure_logger()

repo_url = "https://github.com/aryanshah2109/FraudDetect"
branch = "main"

repo_cloner_object = RepoCloner(
    repository_url= repo_url,
    branch = branch
)


def ingestion_pipeline():

    saved_dict = repo_cloner_object.save_repo()
    
    repo_root = Path(saved_dict["repo_path"])

    manifest_builder_obj = ManifestBuilder(repo_root, repo_url, branch)

    manifest_builder_obj.build_manifest()

ingestion_pipeline()

        
