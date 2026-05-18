import tiktoken

from backend.app.core.config_loader import config

class Tokenizer:
    def __init__(self):
        self.tiktoken_encoder_name = config.tiktoken.name
        self._encoder = tiktoken.get_encoding(self.tiktoken_encoder_name)


    def count_tokens(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def split_by_tokens(
        self,
        text: str,
        max_tokens: int,
        overlap_tokens: int
    ) -> list[str]:

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