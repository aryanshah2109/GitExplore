from rank_bm25 import BM25Okapi
from typing import List, Dict
import re
import numpy as np

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.retrieval.models.retrieval import Retrieval
from backend.app.retrieval.query_expander import QueryExpander

logger = get_logger()


class BM25Retriever:

    def __init__(self, chunks: List[Dict]):

        self.top_k = config.bm25.top_k
        self.chunks = chunks
        self.query_expander = QueryExpander()

        self.original_texts = []
        self.tokenized_texts = []

        self._prepare_documents()

    def tokenize(self, text: str):

        # split camelCase
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # split snake_case
        text = text.replace("_", " ")

        text = text.lower()

        tokens = re.findall(r"\b\w+\b", text)

        return tokens
    
    def _prepare_documents(self):

        logger.info("Preparing BM25 documents")

        for chunk in self.chunks:

            embedding_text = chunk.get("embedding_text", "")
            searchable_text = (
                f"""
                Name: {chunk.get("name", "")}
                Qualified Name: {chunk.get("qualified_name", "")}
                Code:
                {chunk.get("code", "")}
                Module: {chunk.get("module_path", "")}
                Type: {chunk.get("symbol_kind", "")}
                Class: {chunk.get("parent_class", "")}
                Imports: {" ".join(chunk.get("imports", []))}
                Calls: {" ".join(chunk.get("function_calls", []))}
                Children: {" ".join(chunk.get("children", []))}
                Docstring: {chunk.get("docstring", "")}
                Relationships: {chunk.get("relationships", {})}
                """
            )
            
            self.original_texts.append(embedding_text)
            self.tokenized_texts.append(self.tokenize(searchable_text))

        self.bm25 = BM25Okapi(self.tokenized_texts)


    def retrieve(self, query: str, exclude_kinds: list = None, top_k: int = None, query_type: str = None) -> List[Retrieval]:

        if exclude_kinds is None:
            exclude_kinds = ["document"]

        if top_k is None:
            top_k = self.top_k

        logger.info("Retrieving documents via BM25")

        expanded_query = self.query_expander.expand(query, query_type=query_type)
        tokenized_query = self.tokenize(expanded_query.expanded_query_text)
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = np.argsort(scores)[::-1]

        retrieved_chunks = []

        for idx in ranked_indices:

            if len(retrieved_chunks) >= top_k:
                break

            chunk = self.chunks[idx]

            # Skip document-type chunks (markdown, rst, text)
            if chunk.get("symbol_kind") in exclude_kinds:
                continue

            retrieved_chunk_object = Retrieval(
                chunk_id = chunk["symbol_id"],
                score = scores[idx],
                retriever_type = "bm25",
                metadata = {
                    "chunk_type": chunk["symbol_kind"],
                    "language": chunk["language"],
                    "parent_class": chunk["parent_class"],
                    "file_path": chunk["file_path"],
                    "module_path": chunk["module_path"],
                    "name": chunk["name"],
                    "qualified_name": chunk.get("qualified_name"),
                    "imports": chunk.get("imports", []),
                    "function_calls": chunk.get("function_calls", []),
                    "children": chunk.get("children", []),
                    "docstring": chunk.get("docstring", ""),
                    "relationships": chunk.get("relationships", {}),
                    "code_lines": f"{chunk['start_line']} - {chunk['end_line']}",
                },
                code = chunk["code"]
            )

            retrieved_chunks.append(retrieved_chunk_object)

        logger.info(f"BM25 retrieved {len(retrieved_chunks)} documents")
        return retrieved_chunks
