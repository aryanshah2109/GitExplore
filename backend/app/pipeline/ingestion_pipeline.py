"""
    Main ingestion orchestration pipeline

    Flow:
    1. Clone repository
    2. Build repository manifest
    3. Return saved manifest path

"""

# Imports
from pathlib import Path

from backend.app.ingestion.repo_cloner import RepoCloner
from backend.app.ingestion.manifest_builder import ManifestBuilder

from backend.app.core.logger import configure_logger, get_logger

# Configure logging
configure_logger()

# Get logger
logger = get_logger()


class IngestionPipeline:
    """
        Main ingestion orchestration class
    """

    def __init__(
        self,
        repo_url: str,
        branch_name: str = "main"
    ):

        self.repo_url = repo_url
        self.branch_name = branch_name

        self.repo_cloner_object = RepoCloner(
            repository_url=self.repo_url,
            branch=self.branch_name
        )

    def run(self) -> Path:
        """
            Executes complete ingestion pipeline

            Returns:
                Path -> saved manifest path
        """

        try:

            logger.info("Starting ingestion pipeline")

             
            # STEP 1: Clone Repository             

            logger.info("Cloning repository")

            cloned_repo_info = self.repo_cloner_object.save_repo()

            repo_root = Path(cloned_repo_info["repo_path"])

            logger.info(
                f"Repository cloned successfully. Repo ID: {cloned_repo_info['repo_id']}"
            )

             
            # STEP 2: Build Manifest             

            logger.info("Building repository manifest")

            manifest_builder_object = ManifestBuilder(
                repo_root=repo_root,
                repo_url=self.repo_url,
                branch_name=self.branch_name
            )

            saved_manifest_path = manifest_builder_object.build_manifest()

            logger.info(
                f"Manifest built successfully. Path: {saved_manifest_path}"
            )


            logger.info("Ingestion pipeline completed successfully")

            return saved_manifest_path

        except Exception as e:

            logger.error(f"Error during ingestion pipeline: {e}")

            raise


if __name__ == "__main__":

    repo_url = "https://github.com/aryanshah2109/FraudDetect"
    branch = "main"

    ingestion_pipeline = IngestionPipeline(
        repo_url=repo_url,
        branch_name=branch
    )

    manifest_path = ingestion_pipeline.run()

    print(f"\nManifest Saved At:\n{manifest_path}")