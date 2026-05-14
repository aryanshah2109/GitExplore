from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.core.qdrant_setup import client
from backend.app.core.exceptions import *
from backend.app.embeddings.models.payload import Payload

from backend.app.embeddings.embedder import embedding_generator


from pathlib import Path
import json

logger = get_logger()

class StorageToQdrant:

    def __init__(self, symbol_path: Path):
        self.collection_name = config.vector_db.collection_name
        self.symbol_path = symbol_path
        self.chunks_corpus = []

    def _read_chunks(self):
        
        try:
            for json_file in self.symbol_path.rglob("*_symbols.json"):

                with open(file=json_file, mode="r", encoding="utf-8") as file:
                    chunks = json.load(file)

                self.chunks_corpus.extend(chunks)
        
        except Exception as e:
            logger.error(f"Error while reading chunks: {e}")
            raise

    def _payload_creation(self, chunk):
        
        pass

    def store_to_db(self):
        
        try:

            logger.info("Reading symbols and storing embeddings")

            self._read_chunks()

            self.embedding_corpus = embedding_generator.generate_embeddings(self.chunks_corpus)      

            client.c  

        except Exception as e:
            message = f"Error while reading chunks: {e}"
            logger.error(message)
            raise EmbeddingGenerationException(message)



