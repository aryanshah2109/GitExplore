"""Manual end-to-end script for running ingestion and RAG on one repo."""

from dotenv import load_dotenv

load_dotenv()

from backend.app.core.logger import configure_logger
from backend.app.pipeline.ingestion_pipeline import IngestionPipeline
from backend.app.chunking.ast_traverser import ASTTraverser
from backend.app.embeddings.storage import StorageToQdrant
from backend.app.utils.chunk_splitter import ChunkSplitter
from backend.app.retrieval.bm25 import BM25Retriever
from backend.app.retrieval.dense import DenseRetriever
from backend.app.intelligence.classifier import detect_query_type
from backend.app.ingestion.repo_summary import RepositorySummaryBuilder

from backend.app.rag.pipeline import RAGPipeline

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

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

summary_builder = RepositorySummaryBuilder(manifest=manifest, chunks=all_chunks)
repo_summary_chunk = summary_builder.build_summary_chunk()
all_chunks.append(repo_summary_chunk)

qdrant_storage_object = StorageToQdrant()

chunk_splitter = ChunkSplitter()

splitted_chunks = chunk_splitter.split_all_chunks(all_chunks)

qdrant_storage_object.store_chunks(all_chunks=splitted_chunks)

queries = [
    "Which model is used for fraud detection?",
    "Where is the fraud prediction threshold loaded?",
    "Where is transaction validation implemented?",
    "Which file creates risk factors?",
    "Where is XGBoost initialized?",
    "Where is the trained model loaded?",
    "How does a prediction request flow through the system?",
    "Trace the fraud prediction process step by step.",
    "What happens between API request and model prediction?",
    "How does the frontend communicate with the backend?",
    "Which classes interact with the prediction model?",
    "What would happen if threshold retrieval fails?",
    
]
repo_id = "265dc296-f7f0-4ec9-906d-d2a30a27189e"

rag = RAGPipeline(splitted_chunks, repo_id)

for query in queries:
    print(f"\n\nQuery: {query}")
    llm_generation = rag.query(query)
    if not llm_generation:
        print(f"Answer: unavailable")
        print(f"Error: unknown error")
        continue

    if llm_generation.get("status") == "error":
        print(f"Answer: unavailable")
        print(f"Error: {llm_generation.get('error', 'unknown error')}")
        continue

    print(f"{llm_generation['answer']}")
    print(f"Judgement: \n")
    print(f"Faithfullness: {llm_generation['judgement']['faithfulness']}\n")
    print(f"Retrieval relevance: {llm_generation['judgement']['retrieval_relevance']}\n")
    print(f"Citation accuracy: {llm_generation['judgement']['citation_accuracy']}\n")
    print(f"Reasoning: {llm_generation['judgement']['reasoning']}\n")
    

rag.clear_session()
