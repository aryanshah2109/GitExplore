from dataclasses import asdict
from pathlib import Path
import json

from backend.app.core.logger import get_logger
from backend.app.core.path_constants import SYMBOLS_DIR
from backend.app.chunking.parsers.language_registry import get_extractor


logger = get_logger()


class ASTTraverser:
    """
    Traverses repository files and extracts semantic symbols.
    """

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path

    def read_manifest_file(self) -> dict:
        """
        Reads repository manifest file.
        """

        try:

            with open(self.manifest_path, "r", encoding="utf-8") as file:
                manifest_file = json.load(file)

            return manifest_file

        except Exception:
            logger.exception("Error while reading manifest file")
            return {}

    def symbol_extraction(self):
        """
        Extracts symbols from all repository files.
        """

        try:

            logger.debug("Reading manifest file")

            manifest_file = self.read_manifest_file()

            if not manifest_file:
                logger.error("Manifest file is empty")
                return []

            repo_root = manifest_file["repo_root"]
            repo_id = manifest_file["repo_id"]

            repo_symbols_paths = []

            for file in manifest_file["files"]:

                extension = file["extension"]
                file_name = file["file_name"]

                logger.info(f"Chunking: {file_name}")

                file_path = Path(repo_root) / file_name

                extractor_class = get_extractor(extension)

                extractor = extractor_class()

                logger.debug(
                    f"Creating symbols for file: {file_name}"
                )

                symbols = extractor.extract_symbols(file_path, repo_root)

                relative_parent = Path(file_name).parent

                symbol_dir = (
                    SYMBOLS_DIR
                    / repo_id
                    / relative_parent
                )

                symbol_dir.mkdir(
                    parents=True,
                    exist_ok=True
                )

                symbol_file_name = (
                    f"{Path(file_name).stem}_symbols.json"
                )

                symbol_path = (
                    symbol_dir
                    / symbol_file_name
                )

                logger.debug(
                    f"Saving symbols at {symbol_path}"
                )

                with symbol_path.open(
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        [asdict(symbol) for symbol in symbols],
                        f,
                        indent=4
                    )

                repo_symbols_paths.append(symbol_path)

            logger.info("Symbol extraction completed")

            return repo_symbols_paths

        except Exception:
            logger.exception(
                "Error while extracting symbols"
            )
            return []