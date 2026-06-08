"""
    Extracts semantic symbols from non-AST text files
    using recursive text chunking.
"""

from pathlib import Path
from typing import List
from uuid import uuid4
from typing import Optional

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
        file_path: Path,
        repo_root: Optional[Path] = None,
        repo_id: Optional[str] = ""
    ) -> List[Symbol]:
        """Split a text file into symbols that can be embedded and searched."""

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
                    start_byte=current_byte,
                    repo_root=repo_root,
                    repo_id=repo_id
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
        start_byte: int,
        repo_root: Optional[Path] = None,
        repo_id: Optional[str] = ""
    ) -> Symbol:
        """Build one symbol record for a text chunk."""

        end_byte = start_byte + len(chunk)

        start_line = (
            full_text[:start_byte].count("\n") + 1
        )

        end_line = (
            full_text[:end_byte].count("\n") + 1
        )

        relative_file_path = self._relative_file_path(file_path, repo_root)

        return Symbol(
            repo_id = repo_id,

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

            file_path=relative_file_path,

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

            embedding_text=self._build_embedding_text(
                file_path=file_path,
                symbol_kind="document",
                name=f"{file_path.name}_chunk_{chunk_index}",
                parent_class=None,
                code=chunk
            ),

            children=[],

            code=chunk
        )

    def _recursive_split(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """Split text recursively using the configured separators."""

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
        """Carry a short tail from the previous chunk into the next one."""

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
        """Return a rough token count for chunk sizing."""

        return int(len(text.split()) * 1.3)

    def _build_embedding_text(
        self,
        file_path: Path,
        symbol_kind: str,
        name: str,
        parent_class: Optional[str],
        code: str
    ) -> str:
        """Build the text that gets embedded for a document chunk."""

        prefix_parts = [
            f"File: {file_path.name}",
            f"Type: {symbol_kind}",
            f"Name: {name}"
        ]

        if parent_class:
            prefix_parts.append(
                f"Class: {parent_class}"
            )

        prefix = " | ".join(prefix_parts)

        return f"{prefix}\n\n{code}"

    def _build_symbol_id(
        self,
        file_name: str,
        chunk_index: int
    ) -> str:
        """Create a unique id for the chunk symbol."""

        return (
            f"document:"
            f"{file_name}:"
            f"{chunk_index}:"
            f"{uuid4()}"
        )

    def _relative_file_path(self, file_path: Path, repo_root: Optional[Path] = None) -> str:
        """Return a repo-relative file path when a repo root is known."""
        try:
            if repo_root:
                return file_path.relative_to(repo_root).as_posix()
        except ValueError:
            pass

        return file_path.as_posix()
