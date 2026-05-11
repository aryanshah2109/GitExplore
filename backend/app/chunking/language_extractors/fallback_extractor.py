"""
    Extracts semantic symbols from non-AST text files
    using recursive text chunking.
"""

from pathlib import Path
from typing import List
from uuid import uuid4

from backend.app.chunking.models.symbol import Symbol

from backend.app.core.logger import get_logger
from backend.app.core.config_loader import config


logger = get_logger()


class FallbackExtractor:
    """
    Extracts semantic chunks from non-AST files.

    Supported files:
    - txt
    - md
    - rst
    - yaml/yml
    - json
    - toml
    - ini
    - env
    - dockerfile
    - makefile
    - procfile
    - html/css
    - shell scripts
    - generic text/config files

    Strategy:
    - Recursive separator-based chunking
    - Overlapping chunks
    - Metadata-rich symbol creation

    Input:
        file_path: Path

    Output:
        List[Symbol]
    """

    def __init__(self):

        self.language = "text"

        self.chunk_size = (
            config.chunking.fallback_chunk_size
        )

        self.chunk_overlap = (
            config.chunking.fallback_overlap
        )

        self.min_chunk_length = (
            config.chunking.min_chunk_length
        )

        self.separators = [
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]

    def extract_symbols(
        self,
        file_path: Path
    ) -> List[Symbol]:
        """
        Extracts text chunks as semantic symbols.

        Input:
            file_path: Path

        Output:
            symbols: List[Symbol]
        """

        try:

            logger.info(
                f"Using fallback extractor for: {file_path}"
            )

            source_text = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            if not source_text.strip():

                logger.warning(
                    f"Skipping empty file: {file_path}"
                )

                return []

            chunks = self._recursive_split(
                text=source_text,
                separators=self.separators
            )

            symbols: List[Symbol] = []

            current_byte = 0

            for index, chunk in enumerate(chunks):

                if (
                    not chunk.strip()
                    or len(chunk) < self.min_chunk_length
                ):
                    continue

                symbol = self._create_document_symbol(
                    chunk=chunk,
                    chunk_index=index,
                    file_path=file_path,
                    full_text=source_text,
                    start_byte=current_byte
                )

                symbols.append(symbol)

                current_byte += (
                    len(chunk)
                    - self.chunk_overlap
                )

            logger.info(
                f"Extracted {len(symbols)} chunks "
                f"from {file_path.name}"
            )

            return symbols

        except Exception:

            logger.exception(
                f"Error extracting fallback symbols "
                f"from {file_path}"
            )

            return []

    def _create_document_symbol(
        self,
        chunk: str,
        chunk_index: int,
        file_path: Path,
        full_text: str,
        start_byte: int
    ) -> Symbol:
        """
        Creates Symbol object for document chunk.

        Input:
            chunk: str
            chunk_index: int
            file_path: Path
            full_text: str
            start_byte: int

        Output:
            Symbol
        """

        end_byte = start_byte + len(chunk)

        start_line = (
            full_text[:start_byte].count("\n") + 1
        )

        end_line = (
            full_text[:end_byte].count("\n") + 1
        )

        return Symbol(

            symbol_id=self._build_symbol_id(
                file_name=file_path.name,
                chunk_index=chunk_index
            ),

            symbol_kind="document",

            name=(
                f"{file_path.name}"
                f"_chunk_{chunk_index}"
            ),

            signature=None,

            language=self.language,

            file_path=str(file_path),

            module_path=None,

            parent_class=None,

            visibility=None,

            is_async=False,

            inherits=[],

            start_line=start_line,
            end_line=end_line,

            start_byte=start_byte,
            end_byte=end_byte,

            parameters=[],

            return_type=None,

            imports=[],

            function_calls=[],

            relationships={},

            docstring=None,

            decorators=[],

            token_count=self._estimate_tokens(
                chunk
            ),

            embedding_text=(
                self._build_embedding_text(
                    file_path=file_path,
                    chunk=chunk
                )
            ),

            children=[],

            code=chunk
        )

    def _recursive_split(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """
        Recursively splits text.

        Input:
            text: str
            separators: List[str]

        Output:
            List[str]
        """

        if len(text) <= self.chunk_size:
            return [text]

        if not separators:

            return [
                text[i:i+self.chunk_size]
                for i in range(
                    0,
                    len(text),
                    self.chunk_size
                )
            ]

        separator = separators[0]

        if separator == "":

            pieces = [
                text[i:i+self.chunk_size]
                for i in range(
                    0,
                    len(text),
                    self.chunk_size
                )
            ]

        else:

            pieces = text.split(separator)

        chunks = []

        current_chunk = ""

        for piece in pieces:

            if separator != "":
                piece += separator

            if (
                len(current_chunk) + len(piece)
                <= self.chunk_size
            ):

                current_chunk += piece

            else:

                if current_chunk:

                    chunks.append(
                        current_chunk.strip()
                    )

                if len(piece) > self.chunk_size:

                    sub_chunks = (
                        self._recursive_split(
                            text=piece,
                            separators=(
                                separators[1:]
                            )
                        )
                    )

                    chunks.extend(sub_chunks)

                    current_chunk = ""

                else:

                    current_chunk = piece

        if current_chunk.strip():

            chunks.append(
                current_chunk.strip()
            )

        return self._apply_overlap(chunks)

    def _apply_overlap(
        self,
        chunks: List[str]
    ) -> List[str]:
        """
        Applies overlap between chunks.

        Input:
            chunks: List[str]

        Output:
            List[str]
        """

        if not chunks:
            return []

        overlapped_chunks = []

        for index, chunk in enumerate(chunks):

            if index == 0:

                overlapped_chunks.append(chunk)

                continue

            previous_chunk = (
                overlapped_chunks[-1]
            )

            overlap_text = previous_chunk[
                -self.chunk_overlap:
            ]

            overlapped_chunks.append(
                overlap_text + chunk
            )

        return overlapped_chunks

    def _estimate_tokens(
        self,
        text: str
    ) -> int:
        """
        Rough token estimation.

        Input:
            text: str

        Output:
            int
        """

        return int(len(text.split()) * 1.3)

    def _build_embedding_text(
        self,
        file_path: Path,
        chunk: str
    ) -> str:
        """
        Builds embedding text with context prefix.

        Input:
            file_path: Path
            chunk: str

        Output:
            str
        """

        prefix = (
            f"File: {file_path.name}\n"
            f"Path: {file_path}\n"
            f"Chunk Type: document\n\n"
        )

        return prefix + chunk

    def _build_symbol_id(
        self,
        file_name: str,
        chunk_index: int
    ) -> str:
        """
        Creates unique symbol ID.

        Input:
            file_name: str
            chunk_index: int

        Output:
            symbol_id: str
        """

        return (
            f"document:"
            f"{file_name}:"
            f"{chunk_index}:"
            f"{uuid4()}"
        )