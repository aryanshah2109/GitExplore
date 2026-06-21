"""Create and reuse the Qdrant client used for vector storage."""

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.core.exceptions import QdrantSetupException
from backend.app.embeddings.embedder import embedding_generator

import os

logger = get_logger()

class QdrantSetup():
    """Connect to Qdrant and create the collection when it is missing."""

    def __init__(self):
        self.host = config.vector_db.host
        self.port = config.vector_db.port
        self.collection_name = config.vector_db.collection_name
        self.size = embedding_generator.embedding_dimension


    def setup(self):
        """Return a ready Qdrant client for the configured collection."""

        logger.info("Setting Qdrant up")

        try:
            client = QdrantClient(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY"),
            )

            collections = client.get_collections().collections

            collection_names = [
                collection.name
                for collection in collections
            ]

            if self.collection_name not in collection_names:
                
                client.create_collection(
                    collection_name = self.collection_name,
                    vectors_config = VectorParams(
                        size = self.size,
                        distance = Distance.COSINE
                    )
                )
            
            else:
                collection = client.get_collection(self.collection_name)
                vector_params = getattr(collection.config.params, "vectors", None)
                existing_size = getattr(vector_params, "size", None)

                if existing_size and existing_size != self.size:
                    raise QdrantSetupException(
                        f"Existing collection '{self.collection_name}' uses vector size {existing_size}, "
                        f"but the configured embedding model produces size {self.size}. "
                        "Recreate the collection before ingesting with the new model."
                    )

                logger.info("Collection already exists")

            logger.info("Successful Qdrant Setup")

            return client
        
        except Exception as e:
            logger.error(f"Error while setting up Qdrant client: {e}")
            raise QdrantSetupException(f"Error while setting up Qdrant client: {e}")
            
    
client = QdrantSetup().setup()
