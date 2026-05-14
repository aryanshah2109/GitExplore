import ollama
from typing import List

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger

logger = get_logger()

class EmbeddingGenerator:
    def __init__(self):
        self.embedding_model = config.embedding.model_name
        self.batch_size = config.embedding.batch_size
        
    def generate_embeddings(self, chunks: List[str]):

        embeddings_corpus = []

        for i in range(0, len(chunks), self.batch_size):

            batch = chunks[i:i+self.batch_size]

            batch_embeddings = ollama.embed(
                model = self.embedding_model,
                input = batch
            )            

            embeddings_corpus.extend(batch_embeddings["embeddings"])

            logger.debug(f"Processed batch {i // self.batch_size + 1}")

        return embeddings_corpus
    
embedding_generator = EmbeddingGenerator()