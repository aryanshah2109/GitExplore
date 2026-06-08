"""Count and split text by tokens using the configured tokenizer."""

import tiktoken

from backend.app.core.config_loader import config

class Tokenizer:
    """Wrap the shared token encoder used across chunking and RAG."""

    def __init__(self):
        self.tiktoken_encoder_name = config.tiktoken.name
        self._encoder = tiktoken.get_encoding(self.tiktoken_encoder_name)


    def count_tokens(self, text: str) -> int:
        """Return how many tokens the given text uses."""
        return len(self._encoder.encode(text))

    def split_by_tokens(
        self,
        text: str,
        max_tokens: int,
        overlap_tokens: int
    ) -> list[str]:
        """Split text into token-sized parts with a small overlap."""

        tokens = self._encoder.encode(text)

        if len(tokens) <= max_tokens:
            return [text]

        parts = []
        start = 0

        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            parts.append(
                self._encoder.decode(tokens[start:end])
            )
            if end == len(tokens):
                break
            start = end - overlap_tokens

        return parts
