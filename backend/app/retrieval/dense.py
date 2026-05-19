import ollama

from typing import List, Dict, Optional

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue
)

from backend.app.core.config_loader import config
from backend.app.core.qdrant_setup import client
from backend.app.core.logger import (
    get_logger
)
from backend.app.retrieval.models.retrieval import Retrieval

logger = get_logger()


class DenseRetriever:

    def __init__(self):

        self.collection_name = (
            config.vector_db.collection_name
        )

        self.embedding_model = (
            config.embedding.model_name
        )

        self.top_k = (
            config.vector_db.top_k
        )

    def normalize_text(
        self,
        value
    ) -> str:

        if value is None:
            return ""

        return str(value).strip().lower()

    def build_searchable_text(
        self,
        payload: Dict
    ) -> str:

        searchable_fields = [
            payload.get("symbol"),
            payload.get("module_path"),
            payload.get("parent_class"),
            payload.get("file_path"),
            payload.get("code"),
            payload.get("chunk_type"),
            payload.get("language"),
        ]

        return " ".join(
            self.normalize_text(field)
            for field in searchable_fields
            if field
        )

    def embed_query(
        self,
        query: str
    ) -> List[float]:

        try:

            response = ollama.embed(
                model=self.embedding_model,
                input=query
            )

            return response["embeddings"][0]

        except Exception:

            logger.exception(
                "Error generating query embedding"
            )

            return []

    def apply_exact_match_boost(
        self,
        query: str,
        results: List[Retrieval]
    ) -> List[Retrieval]:

        try:

            query_terms = set(
                self.normalize_text(query).split()
            )

            boosted_results = []

            for result in results:

                payload = result.metadata or {}

                searchable_text = (
                    self.build_searchable_text(
                        {
                            "symbol": result.chunk_id,
                            "module_path": payload.get("module_path"),
                            "parent_class": payload.get("parent_class"),
                            "file_path": payload.get("file_path"),
                            "code": result.code,
                            "chunk_type": payload.get("chunk_type"),
                            "language": payload.get("language"),
                        }
                    )
                )

                boost = 0.0

                for term in query_terms:

                    if term in searchable_text:
                        boost += 0.10

                symbol_name = self.normalize_text(
                    result.chunk_id
                )

                if symbol_name in query_terms:
                    boost += 0.50

                module_path = self.normalize_text(
                    payload.get("module_path")
                )

                for term in query_terms:

                    if term in module_path:
                        boost += 0.20

                parent_class = self.normalize_text(
                    payload.get("parent_class")
                )

                for term in query_terms:

                    if term in parent_class:
                        boost += 0.20

                file_path = self.normalize_text(
                    payload.get("file_path")
                )

                for term in query_terms:

                    if term in file_path:
                        boost += 0.10

                result.score += boost

                boosted_results.append(result)

            boosted_results.sort(
                key=lambda x: x.score,
                reverse=True
            )

            return boosted_results

        except Exception:

            logger.exception(
                "Error applying exact match boost"
            )

            return results

    def format_result(
        self,
        point
    ) -> Retrieval:

        payload = point.payload or {}

        return Retrieval(
            chunk_id = payload.get("symbol_id"),
            score = point.score,
            retriever_type = "dense",
            metadata = {
                    "chunk_type": payload.get("chunk_type"),
                    "language":payload.get("language"),
                    "parent_class":payload.get("parent_class"),
                    "file_path":payload.get("file_path"),
                    "module_path":payload.get("module_path"),
                    "name":payload.get("symbol"),
                    "code_lines": f"{payload.get("start_line")} - {payload.get("end_line")}",
            },
            code = payload.get("code")
        )

        

    def search(
        self,
        query: str,
        repo_id: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:

        try:

            if top_k is None:
                top_k = self.top_k

            logger.info(
                f"Dense retrieval query: {query}"
            )

            query_embedding = (
                self.embed_query(query)
            )

            if not query_embedding:

                logger.warning(
                    "No query embedding generated"
                )

                return []

            query_filter = None

            if repo_id:

                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="repo_id",
                            match=MatchValue(
                                value=repo_id
                            )
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

            boosted_results = (
                self.apply_exact_match_boost(
                    query=query,
                    results=formatted_results
                )
            )

            logger.info(
                f"Retrieved {len(boosted_results)} dense results"
            )

            return boosted_results

        except Exception:

            logger.exception(
                "Dense retrieval failed"
            )

            return []

    def get_context(
        self,
        query: str,
        repo_id: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:

        return self.search(
            query=query,
            repo_id=repo_id,
            top_k=top_k
        )
