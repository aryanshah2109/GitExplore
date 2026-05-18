from typing import List, Dict

from backend.app.core.config_loader import config
from backend.app.utils.tokenizer import Tokenizer


class ChunkSplitter:
    def __init__(self):
        self.max_tokens = config.chunking.max_tokens
        self.overlap_tokens = config.chunking.overlap_tokens
        self.tokenizer = Tokenizer()

    def split_chunk(
        self,
        chunk: Dict
    ) -> List[Dict]:

        text = chunk.get("embedding_text", "")

        if self.tokenizer.count_tokens(text) <= self.max_tokens:
            return [chunk]

        parts = self.tokenizer.split_by_tokens(text, self.max_tokens,self.overlap_tokens)
        sub_chunks = []

        for i, part in enumerate(parts):
            sub = chunk.copy()
            sub["embedding_text"] = part
            sub["symbol_id"] = f"{chunk['symbol_id']}__part{i}"
            sub_chunks.append(sub)

        return sub_chunks


    def split_all_chunks(
        self,
        chunks: List[Dict],
    ) -> List[Dict]:

        result = []
        for chunk in chunks:
            result.extend(
                self.split_chunk(chunk)
            )
        return result
