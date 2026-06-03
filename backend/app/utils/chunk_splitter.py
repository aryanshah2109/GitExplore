from typing import List, Dict

from backend.app.core.config_loader import config
from backend.app.utils.tokenizer import Tokenizer


class ChunkSplitter:
    def __init__(self):
        self.max_tokens = min(
            config.chunking.max_tokens,
            400
        )
        self.overlap_tokens = config.chunking.overlap_tokens
        self.tokenizer = Tokenizer()

    def split_chunk(
        self,
        chunk: Dict
    ) -> List[Dict]:

        embedding_text = chunk.get(
            "embedding_text",
            ""
        )

        if not embedding_text:
            return []

        total_tokens = self.tokenizer.count_tokens(
            embedding_text
        )

        if total_tokens <= self.max_tokens:
            return [chunk]

        # Preserve metadata header       
        header = ""
        body = embedding_text

        if "\n\n" in embedding_text:
            header, body = embedding_text.split(
                "\n\n",
                1
            )

        body_parts = self.tokenizer.split_by_tokens(
            text=body,
            max_tokens=self.max_tokens,
            overlap_tokens=self.overlap_tokens
        )

        sub_chunks = []

        for i, part in enumerate(body_parts):

            sub = chunk.copy()

            # Preserve metadata on every chunk
            if header:
                sub["embedding_text"] = (
                    header
                    + "\n\n"
                    + part
                )
            else:
                sub["embedding_text"] = part

            sub["symbol_id"] = (
                f"{chunk['symbol_id']}__part{i}"
            )

            sub_chunks.append(sub)

        return sub_chunks

    def split_all_chunks(
        self,
        chunks: List[Dict]
    ) -> List[Dict]:

        result = []

        for chunk in chunks:

            split_chunks = self.split_chunk(
                chunk
            )

            for split_chunk in split_chunks:

                token_count = (
                    self.tokenizer.count_tokens(
                        split_chunk["embedding_text"]
                    )
                )

                # Final safety check
                if token_count > self.max_tokens:

                    # Force second split
                    smaller_parts = (
                        self.tokenizer.split_by_tokens(
                            split_chunk["embedding_text"],
                            self.max_tokens // 2,
                            self.overlap_tokens
                        )
                    )

                    for idx, part in enumerate(
                        smaller_parts
                    ):
                        forced_chunk = (
                            split_chunk.copy()
                        )

                        forced_chunk["embedding_text"] = (
                            part
                        )

                        forced_chunk["symbol_id"] = (
                            f"{split_chunk['symbol_id']}__sub{idx}"
                        )

                        result.append(
                            forced_chunk
                        )

                else:
                    result.append(
                        split_chunk
                    )

        return result