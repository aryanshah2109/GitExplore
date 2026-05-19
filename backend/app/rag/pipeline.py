from typing import List, Dict

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.retrieval.bm25 import BM25Retriever
from backend.app.retrieval.dense import DenseRetriever
from backend.app.retrieval.hybrid import RRFRetriever
from backend.app.rag.context_builder import ContextBuilder
from backend.app.rag.llm_client import LLMClient
from backend.app.intelligence.classifier import detect_query_type

logger = get_logger()

class RAGPipeline:
    def __init__(self, chunks: List[Dict], repo_id: str):
        self.bm25 = BM25Retriever(chunks)
        self.dense = DenseRetriever()
        self.rrf = RRFRetriever()
        self.context_builder = ContextBuilder()
        self.llm = LLMClient()
        self.repo_id = repo_id

    def query(self, user_query: str) -> str:

        try:
            logger.debug("Detecting query type")

            query_type = detect_query_type(user_query)
            exclude = ["document"] + (
                ["module"] if query_type in ("find_function", "debug") else []
            )

            logger.debug("Retriving hybrid results")
            bm25_results = self.bm25.retrieve(user_query, exclude_kinds=exclude)
            dense_results = self.dense.get_context(user_query, self.repo_id)
            hybrid_results = self.rrf.fuse([bm25_results, dense_results])

            logger.debug("Generating context")
            context = self.context_builder.build_context(hybrid_results)

            logger.debug("Generating answer")
            answer = self.llm.generate_answer(query=user_query, context=context)

            return answer

        except Exception as e:
            logger.error(f"Error while running RAG Pipeline: {e}")    

    def clear_session(self):
        """Call when user switches repos."""
        self.llm.clear_history()