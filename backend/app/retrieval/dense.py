"""Run dense retrieval against the Qdrant collection."""

from typing import List, Dict, Optional

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue
)

from backend.app.core.config_loader import config
from backend.app.core.qdrant_setup import client
from backend.app.core.logger import get_logger
from backend.app.embeddings.embedder import embedding_generator
from backend.app.retrieval.models.retrieval import Retrieval
from backend.app.retrieval.query_expander import QueryExpander

logger = get_logger()


class DenseRetriever:
    """Embed the query and fetch the closest stored chunks."""

    def __init__(self):
        self.collection_name = config.vector_db.collection_name
        self.top_k = config.vector_db.top_k
        self.query_expander = QueryExpander()

    def normalize_text(self, value) -> str:
        """Turn nested values into plain searchable text."""
        if value is None:
            return ""

        if isinstance(value, (list, tuple, set)):
            return " ".join(
                self.normalize_text(item)
                for item in value
                if item is not None
            ).strip().lower()

        if isinstance(value, dict):
            parts = []
            for key, val in value.items():
                parts.append(f"{self.normalize_text(key)} {self.normalize_text(val)}")
            return " ".join(parts).strip().lower()

        return str(value).strip().lower()

    def build_searchable_text(self, payload: Dict) -> str:
        """Assemble the fields that should influence exact-match boosts."""
        searchable_fields = [
            payload.get("symbol"),
            payload.get("qualified_name"),
            payload.get("module_path"),
            payload.get("parent_class"),
            payload.get("file_path"),
            payload.get("chunk_type"),
            payload.get("language"),
            payload.get("imports"),
            payload.get("function_calls"),
            payload.get("children"),
            payload.get("docstring"),
            payload.get("relationships"),
            payload.get("code"),
        ]

        return " ".join(
            self.normalize_text(field)
            for field in searchable_fields
            if field
        )

    def embed_query(self, query: str, query_type: Optional[str] = None) -> List[float]:
        """Return the embedding vector for the expanded query."""
        try:
            expanded = self.query_expander.expand(query, query_type=query_type)
            embeddings = embedding_generator.generate_embeddings(
                [expanded.expanded_query_text]
            )
            if not embeddings:
                return []
            return embeddings[0]

        except Exception:
            logger.exception("Error generating query embedding")
            return []

    def apply_exact_match_boost(self, query: str, results: List[Retrieval], query_type: Optional[str] = None) -> List[Retrieval]:
        """Raise scores when the query clearly matches a symbol or file."""
        try:
            expanded = self.query_expander.expand(query, query_type=query_type)
            original_query_text = self.normalize_text(query)
            expanded_query_text = self.normalize_text(expanded.expanded_query_text)
            query_terms = set(expanded_query_text.split())

            boosted_results = []

            for result in results:
                payload = result.metadata or {}
                symbol_name = self.normalize_text(payload.get("name") or result.chunk_id)
                qualified_name = self.normalize_text(payload.get("qualified_name"))
                module_path = self.normalize_text(payload.get("module_path"))
                parent_class = self.normalize_text(payload.get("parent_class"))
                file_path = self.normalize_text(payload.get("file_path"))

                searchable_text = self.build_searchable_text(
                    {
                        "symbol": payload.get("name") or result.chunk_id,
                        "qualified_name": payload.get("qualified_name"),
                        "module_path": payload.get("module_path"),
                        "parent_class": payload.get("parent_class"),
                        "file_path": payload.get("file_path"),
                        "code": result.code,
                        "chunk_type": payload.get("chunk_type"),
                        "language": payload.get("language"),
                        "imports": payload.get("imports"),
                        "function_calls": payload.get("function_calls"),
                        "children": payload.get("children"),
                        "docstring": payload.get("docstring"),
                        "relationships": payload.get("relationships"),
                    }
                )

                boost = 0.0

                if original_query_text == symbol_name:
                    boost += 100.0
                if qualified_name and original_query_text == qualified_name:
                    boost += 90.0
                if symbol_name and symbol_name in original_query_text:
                    boost += 70.0
                if qualified_name and qualified_name in original_query_text:
                    boost += 60.0

                for term in query_terms:
                    if not term:
                        continue
                    if term == module_path:
                        boost += 24.0
                    elif term in module_path:
                        boost += 12.0

                    if term == parent_class:
                        boost += 20.0
                    elif term in parent_class:
                        boost += 8.0

                    if term in file_path:
                        boost += 3.0

                    if term in searchable_text:
                        boost += 0.5

                if file_path:
                    file_name = file_path.rsplit("/", 1)[-1]
                    if file_name and file_name in original_query_text:
                        boost += 6.0

                result.score += boost
                boosted_results.append(result)

            boosted_results.sort(key=lambda x: x.score, reverse=True)
            return boosted_results

        except Exception:
            logger.exception("Error applying exact match boost")
            return results

    def format_result(self, point) -> Retrieval:
        """Convert a Qdrant point into the shared retrieval object."""
        payload = point.payload or {}

        return Retrieval(
            chunk_id=payload.get("symbol_id"),
            score=point.score,
            retriever_type="dense",
            metadata={
                "chunk_type": payload.get("chunk_type"),
                "language": payload.get("language"),
                "parent_class": payload.get("parent_class"),
                "file_path": payload.get("file_path"),
                "module_path": payload.get("module_path"),
                "name": payload.get("symbol"),
                "qualified_name": payload.get("qualified_name"),
                "imports": payload.get("imports", []),
                "function_calls": payload.get("function_calls", []),
                "children": payload.get("children", []),
                "docstring": payload.get("docstring", ""),
                "relationships": payload.get("relationships", {}),
                "code_lines": f"{payload.get('start_line')} - {payload.get('end_line')}",
            },
            code=payload.get("code")
        )

    def search(
        self,
        query: str,
        repo_id: Optional[str] = None,
        top_k: Optional[int] = None,
        query_type: Optional[str] = None,
    ) -> List[Dict]:
        """Fetch the best dense matches for a query."""
        try:
            if top_k is None:
                top_k = self.top_k

            logger.info(f"Dense retrieval query: {query}")

            query_embedding = self.embed_query(query, query_type=query_type)

            if not query_embedding:
                logger.warning("No query embedding generated")
                return []

            query_filter = None

            if repo_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="repo_id",
                            match=MatchValue(value=repo_id)
                        )
                    ]
                )

            search_results = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True
            )

            formatted_results = [
                self.format_result(point)
                for point in search_results
            ]

            boosted_results = self.apply_exact_match_boost(query=query, results=formatted_results, query_type=query_type)

            logger.info(f"Dense retrieved {len(boosted_results)} results")
            return boosted_results

        except Exception:
            logger.exception("Dense retrieval failed")
            return []

    def get_context(
        self,
        query: str,
        repo_id: Optional[str] = None,
        top_k: Optional[int] = None,
        query_type: Optional[str] = None
    ) -> List[Dict]:
        """Compatibility wrapper around `search`."""
        return self.search(
            query=query,
            repo_id=repo_id,
            top_k=top_k,
            query_type=query_type
        )
