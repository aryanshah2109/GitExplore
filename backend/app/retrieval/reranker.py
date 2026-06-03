import cohere
from typing import List
import os

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.retrieval.models.retrieval import Retrieval

logger = get_logger()

class Reranker:
    def __init__(self):
        self.top_k = config.reranker.top_k
        self.model_name = config.reranker.model_name

        self.cohere_setup = cohere.ClientV2(os.getenv("COHERE_API_KEY"))

    def generate_reranking_text(
        self,
        chunk: Retrieval
    ) -> str:
        try:
            metadata = chunk.metadata or {}

            rerank_text = f"""
            File: {metadata.get('file_path', '')}
            Module: {metadata.get('module_path', '')}
            Language: {metadata.get('language', '')}
            Type: {metadata.get('chunk_type', '')}
            Symbol: {metadata.get('name', '')}
            Qualified Name: {metadata.get('qualified_name', '')}
            Parent Class: {metadata.get('parent_class', '')}
            Imports: {" ".join(metadata.get('imports', []))}
            Function Calls: {" ".join(metadata.get('function_calls', []))}
            Docstring: {metadata.get('docstring', '')}

            Code:
            {chunk.code}
            """

            return rerank_text
        
        except Exception as e:
            logger.error(f"Error while creating reranking text: {e}")
            raise

    
    def rerank(self, query: str, chunks: List[Retrieval], top_n: int = None):
        try:
            logger.info(f"Reranking {len(chunks)} chunks")

            documents = [self.generate_reranking_text(chunk) for chunk in chunks]

            try:
                if top_n is None:
                    top_n = self.top_k

                rerank_response = self.cohere_setup.rerank(
                    model=self.model_name,
                    query=query,
                    documents=documents,
                    top_n=top_n
                )
            except Exception:
                return chunks[:top_n]

            final_chunks = [
                chunks[result.index]
                for result in rerank_response.results
            ]

            logger.info(f"Reranker returned {len(final_chunks)} chunks")

            return final_chunks

        except Exception as e:
            logger.error(f"Error while reranking: {e}")
            raise
