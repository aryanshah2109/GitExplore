"""Custom exceptions used by the backend service."""

class QdrantSetupException(Exception):
    """Raised when Qdrant cannot be prepared for use."""

    def __init__(self, message):
        super().__init__(message)

class EmbeddingGenerationException(Exception):
    """Raised when embedding or storage work fails."""

    def __init__(self, message):
        super().__init__(message)
