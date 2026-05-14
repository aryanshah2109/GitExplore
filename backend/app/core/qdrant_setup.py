from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.core.exceptions import QdrantSetupException

logger = get_logger()

class QdrantSetup():
    def __init__(self):
        self.host = config.vector_db.host
        self.port = config.vector_db.port
        self.collection_name = config.vector_db.collection_name
        self.size = config.vector.size


    def setup(self):

        logger.info("Setting Qdrant up")

        try:
            client = QdrantClient(
                host = self.host,
                port = self.port
            )

            client.create_collection(
                collection_name = self.collection_name,
                vectors_config = VectorParams(
                    size = self.size,
                    distance = Distance.COSINE
                )
            )

            logger.info("Successful Qdrant Setup")

            return client
        
        except Exception as e:
            logger.error(f"Error while setting up Qdrant client: {e}")
            raise QdrantSetupException(f"Error while setting up Qdrant client: {e}")
            
    
client = QdrantSetup().setup()