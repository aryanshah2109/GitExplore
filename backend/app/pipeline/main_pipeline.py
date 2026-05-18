from backend.app.pipeline.ingestion_pipeline import IngestionPipeline
from backend.app.chunking.ast_traverser import ASTTraverser
from backend.app.embeddings.storage import StorageToQdrant
from backend.app.utils.chunk_splitter import ChunkSplitter
from backend.app.retrieval.bm25 import BM25Retriever
from backend.app.retrieval.dense import DenseRetriever
from backend.app.intelligence.classifier import detect_query_type

import json
from pprint import pprint

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

chunk_splitter = ChunkSplitter()

splitted_chunks = chunk_splitter.split_all_chunks(all_chunks)

qdrant_storage_object.store_chunks(all_chunks=splitted_chunks)

bm25 = BM25Retriever(splitted_chunks)
dense = DenseRetriever()

query = "Explain in detail how model training happens in the project?"
repo_id = "265dc296-f7f0-4ec9-906d-d2a30a27189e"

bm25_results = bm25.retrieve(query)
dense_results = dense.get_context(query, repo_id)

print(type(bm25_results))
print(type(dense_results))

print("="*50)

pprint(bm25_results[0])

print("\n\n")

print("="*50)

pprint(dense_results[0])

print("\n\n")