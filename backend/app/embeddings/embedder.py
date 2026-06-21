"""Generate embeddings with the configured SentenceTransformers model."""

from typing import List

from sentence_transformers import SentenceTransformer

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger

logger = get_logger()


class EmbeddingGenerator:
    """Small wrapper around the embedding model client."""

    def __init__(self):
        self.embedding_model = config.embedding.model_name
        self.batch_size = config.embedding.batch_size
        self.normalize = config.embedding.normalize
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        """Load the encoder once and reuse it for the process lifetime."""
        if self._model is None:
            self._model = SentenceTransformer(
                self.embedding_model,
                trust_remote_code=True,
            )
        return self._model

    @property
    def embedding_dimension(self) -> int:
        """Expose the output dimension so Qdrant can be configured safely."""
        return self.model.get_sentence_embedding_dimension()

    def generate_embeddings(self, texts: List[str]):
        """Return one embedding vector per input text."""

        try:
            if not texts:
                return []

            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=self.normalize,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            return embeddings.tolist()

        except Exception as e:

            logger.error(
                f"Embedding generation failed: {e}"
            )

            raise


embedding_generator = EmbeddingGenerator()
