class QdrantSetupException(Exception):
    def __init__(self, message):
        super().__init__(message)

class EmbeddingGenerationException(Exception):
    def __init__(self, message):
        super().__init__(message)