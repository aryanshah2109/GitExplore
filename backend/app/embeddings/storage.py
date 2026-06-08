"""Store chunk embeddings and metadata in Qdrant."""

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
    """Turn chunk records into Qdrant points and upload them in batches."""

    def __init__(self):
        self.collection_name = config.vector_db.collection_name
                
    def store_chunks(self, all_chunks: List[Dict]):
        """Embed each chunk and write the results into Qdrant."""

        try:

            if not all_chunks:
                logger.warning("No chunks received")
                return

            batch_size = config.embedding.batch_size

            logger.info(
                f"Processing {len(all_chunks)} chunks"
            )

            for i in range(
                0,
                len(all_chunks),
                batch_size
            ):

                chunk_batch = all_chunks[
                    i:i + batch_size
                ]

                valid_chunks = []
                texts = []

                for chunk in chunk_batch:

                    try:

                        text = chunk["embedding_text"]

                        token_count = len(
                            text.split()
                        )

                        if token_count > 250:

                            logger.warning(
                                f"[LARGE] "
                                f"{chunk['file_path']} "
                                f"| {chunk['symbol_id']} "
                                f"| {token_count} words"
                            )

                        valid_chunks.append(chunk)
                        texts.append(text)

                    except Exception as e:

                        logger.error(
                            "\nFAILED CHUNK\n"
                            f"File: {chunk['file_path']}\n"
                            f"Symbol: {chunk['symbol_id']}\n"
                            f"Type: {chunk['symbol_kind']}\n"
                            f"Chars: {len(chunk['embedding_text'])}\n"
                            f"Words: {len(chunk['embedding_text'].split())}\n"
                            f"Start Line: {chunk['start_line']}\n"
                            f"End Line: {chunk['end_line']}\n"
                            f"Error: {e}\n"
                        )

                        continue

                if valid_chunks:

                    try:
                        try:
                            embeddings = embedding_generator.generate_embeddings(texts)
                        except Exception as batch_error:
                            logger.warning(
                                f"Batch embedding failed for batch {i // batch_size + 1}: {batch_error}. "
                                "Falling back to per-chunk embedding."
                            )
                            embeddings = []
                            for text in texts:
                                try:
                                    embeddings.append(
                                        embedding_generator.generate_embeddings([text])[0]
                                    )
                                except Exception as item_error:
                                    logger.error(
                                        f"Per-chunk embedding fallback failed in batch {i // batch_size + 1}: {item_error}"
                                    )
                                    embeddings.append(None)

                        if len(embeddings) != len(valid_chunks):
                            raise ValueError(
                                "Embedding count did not match chunk count"
                            )

                        points = []

                        for chunk, embedding in zip(valid_chunks, embeddings):
                            if embedding is None:
                                continue

                            payload = Payload(
                                repo_id=chunk["repo_id"],
                                language=chunk["language"],
                                symbol=chunk["name"],
                                chunk_type=chunk["symbol_kind"],
                                module_path=chunk["module_path"],
                                start_line=chunk["start_line"],
                                end_line=chunk["end_line"],
                                parent_class=chunk["parent_class"],
                                file_path=chunk["file_path"],
                                code=chunk["code"],
                                symbol_id=chunk["symbol_id"],
                                imports=chunk.get("imports", []),
                                function_calls=chunk.get("function_calls", []),
                                qualified_name=chunk.get("qualified_name", ""),
                                children=chunk.get("children", []),
                                docstring=chunk.get("docstring", ""),
                                relationships=chunk.get("relationships", {})
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
                                    payload=asdict(
                                        payload
                                    )
                                )
                            )

                        client.upsert(
                            collection_name=self.collection_name,
                            points=points,
                            wait=True
                        )

                        logger.info(
                            f"Stored batch "
                            f"{i // batch_size + 1}"
                        )

                    except Exception as e:

                        logger.error(
                            f"Qdrant upsert failed: {e}"
                        )

                else:

                    logger.warning(
                        f"Batch {i // batch_size + 1} "
                        f"contained no valid points"
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
