from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.core.qdrant_setup import client
from backend.app.core.exceptions import *
from backend.app.embeddings.models.payload import Payload

from backend.app.embeddings.embedder import embedding_generator

from qdrant_client.models import PointStruct, Field, MatchAny
from typing import List, Dict, Optional
from dataclasses import asdict
from pathlib import Path
import json
import uuid

logger = get_logger()

class StorageToQdrant:

    def __init__(self):
        self.collection_name = config.vector_db.collection_name

    def _read_chunks(self):

        try:

            with open(
                file=self.symbol_path,
                mode="r",
                encoding="utf-8"
            ) as file:

                chunks = json.load(file)

            self.chunks_corpus.extend(chunks)

        except Exception as e:
            logger.error(f"Error while reading chunks: {e}")
            raise


                
    def store_chunks(self, all_chunks: List[Dict]):

        try:

            if not all_chunks:
                logger.warning("No chunks received")
                return

            batch_size = config.embedding.batch_size

            logger.info(
                f"Processing {len(all_chunks)} chunks"
            )

            for i in range(0, len(all_chunks), batch_size):

                chunk_batch = all_chunks[
                    i:i + batch_size
                ]

                embedding_texts = [
                    chunk["embedding_text"]
                    for chunk in chunk_batch
                ]

                embeddings = (
                    embedding_generator.generate_embeddings(
                        embedding_texts
                    )
                )

                points = []

                for chunk, embedding in zip(
                    chunk_batch,
                    embeddings
                ):

                    payload = Payload(
                        repo_id=chunk["repo_id"],
                        language=chunk["language"],
                        symbol=chunk["name"],
                        chunk_type=chunk["symbol_kind"],
                        module_path=chunk["module_path"],
                        start_line=chunk["start_line"],
                        end_line=chunk["end_line"],
                        parent_class=chunk["parent_class"]
                    )

                    points.append(
                        PointStruct(
                            id=str(
                                uuid.uuid5(
                                    uuid.NAMESPACE_DNS,
                                    chunk["symbol_id"]
                                )
                            ),
                            vector=embedding,
                            payload=asdict(payload)
                        )
                    )

                client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=False
                )

                logger.info(
                    f"Stored batch "
                    f"{i // batch_size + 1}"
                )

            logger.info(
                "Completed Qdrant storage"
            )

        except Exception as e:

            logger.error(
                f"Error during storage: {e}"
            )

            raise EmbeddingGenerationException(
                str(e)
            )