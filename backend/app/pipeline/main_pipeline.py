from backend.app.pipeline.ingestion_pipeline import IngestionPipeline
from backend.app.chunking.ast_traverser import ASTTraverser
from backend.app.embeddings.storage import StorageToQdrant

import json

repo_url = "https://github.com/aryanshah2109/FraudDetect"
branch = "main"

# repo_url = "https://github.com/aryanshah2109/DSA-Codes"
# branch = "master"

ingestion_pipeline = IngestionPipeline(
    repo_url=repo_url,
    branch_name=branch
)

manifest_path = ingestion_pipeline.run()

traverser = ASTTraverser(manifest_path)

all_symbol_paths = traverser.symbol_extraction()

all_chunks = []

for path in all_symbol_paths:

    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    all_chunks.extend(chunks)

qdrant_storage_object = StorageToQdrant()

qdrant_storage_object.store_chunks(all_chunks=all_chunks)