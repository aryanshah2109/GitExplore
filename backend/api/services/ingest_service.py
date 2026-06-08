"""Repository ingestion service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from backend.api.schemas.ingest import IngestResponse


SESSION_STORE: dict[str, dict] = {}


def run_ingestion(repo_url: str, branch: str) -> IngestResponse:
    """Run the existing ingestion pipeline and store the resulting session data."""
    from backend.app.chunking.ast_traverser import ASTTraverser
    from backend.app.embeddings.storage import StorageToQdrant
    from backend.app.ingestion.repo_summary import RepositorySummaryBuilder
    from backend.app.pipeline.ingestion_pipeline import IngestionPipeline
    from backend.app.utils.chunk_splitter import ChunkSplitter

    ingestion_pipeline = IngestionPipeline(repo_url=repo_url, branch_name=branch)
    manifest_path = ingestion_pipeline.run()
    if not manifest_path:
        raise RuntimeError("Ingestion pipeline did not return a manifest path.")

    manifest_path = Path(manifest_path)
    traverser = ASTTraverser(manifest_path)
    symbol_paths = traverser.symbol_extraction()

    chunks: List[Dict] = []
    for path in symbol_paths:
        with Path(path).open("r", encoding="utf-8") as file:
            chunks.extend(json.load(file))

    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    summary_chunk = RepositorySummaryBuilder(manifest=manifest, chunks=chunks).build_summary_chunk()
    chunks.append(summary_chunk)

    split_chunks = ChunkSplitter().split_all_chunks(chunks)
    StorageToQdrant().store_chunks(split_chunks)

    repo_id = manifest.get("repo_id") or manifest_path.stem
    SESSION_STORE[repo_id] = {
        "chunks": split_chunks,
    }

    return IngestResponse(
        repo_id=repo_id,
        file_count=int(manifest.get("valid_files_count", len(manifest.get("files", [])))),
        chunk_count=len(split_chunks),
        status="ready",
    )
