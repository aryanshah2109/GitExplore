"""Generate embeddings with the configured Ollama model."""

import ollama
from typing import List

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger

logger = get_logger()

class EmbeddingGenerator:
    """Small wrapper around the embedding model client."""

    def __init__(self):
        self.embedding_model = config.embedding.model_name
        self.batch_size = config.embedding.batch_size
        
    def generate_embeddings(self, texts: List[str]):
        """Return one embedding vector per input text."""

        try:

            response = ollama.embed(
                model = self.embedding_model,
                input = texts,
                truncate = True
            )            

            return response["embeddings"]
        
        except Exception as e:

            logger.error(
                f"Embedding generation failed: {e}"
            )

            raise
    
embedding_generator = EmbeddingGenerator()
