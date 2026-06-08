"""Turn retrieval results into a compact prompt context."""

from typing import List, Optional, Dict, Any

from backend.app.retrieval.models.retrieval import Retrieval
from backend.app.core.config_loader import config
from backend.app.utils.tokenizer import Tokenizer
from backend.app.core.logger import get_logger

logger = get_logger()


class ContextBuilder:
    """Build the prompt context and keep track of which sources were used."""

    def __init__(self):
        self.budget = config.generation.context_budget_tokens
        self.tokenizer = Tokenizer()
        self.last_sources: List[Dict[str, Any]] = []

    def _format_value(self, value) -> str:
        """Render nested metadata into a short flat string."""
        if value is None:
            return ""

        if isinstance(value, (list, tuple, set)):
            formatted_items = []
            for item in value:
                formatted_item = self._format_value(item)
                if formatted_item:
                    formatted_items.append(formatted_item)
            return ", ".join(formatted_items)

        if isinstance(value, dict):
            parts = []
            for key, val in value.items():
                formatted_val = self._format_value(val)
                if formatted_val:
                    parts.append(f"{key}: {formatted_val}")
            return "; ".join(parts)

        return str(value).strip()

    def build_context(self, results: List[Retrieval], budget: Optional[int] = None) -> str:
        """Assemble retrieval snippets until the token budget is used up."""
        try:
            max_budget = budget or self.budget
            context_parts = []
            used = 0
            self.last_sources = []

            for index, r in enumerate(results, start=1):
                metadata = r.metadata or {}
                source_id = index

                snippet = self._build_snippet(source_id, r, metadata)
                tokens = self.tokenizer.count_tokens(snippet)

                if used + tokens > max_budget:
                    break

                context_parts.append(snippet)
                used += tokens

                self.last_sources.append(
                    {
                        "source_id": source_id,
                        "chunk_id": r.chunk_id,
                        "file_path": metadata.get("file_path", ""),
                        "module_path": metadata.get("module_path", ""),
                        "symbol_type": metadata.get("chunk_type", ""),
                        "symbol_name": metadata.get("name", ""),
                        "qualified_name": metadata.get("qualified_name", ""),
                        "parent_class": metadata.get("parent_class", ""),
                        "code_lines": metadata.get("code_lines", ""),
                        "imports": metadata.get("imports", []),
                        "function_calls": metadata.get("function_calls", []),
                        "children": metadata.get("children", []),
                        "docstring": metadata.get("docstring", ""),
                        "relationships": metadata.get("relationships", {}),
                    }
                )

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error while building context {e}")
            self.last_sources = []
            return ""

    def _build_snippet(self, source_id: int, retrieval: Retrieval, metadata: Dict[str, Any]) -> str:
        """Create the text block that is fed to the generation model."""
        docstring = self._truncate(self._format_value(metadata.get("docstring")), 600)
        code = self._truncate(retrieval.code or "", 2500)

        return f"""
SOURCE_ID: {source_id}
File: {self._format_value(metadata.get('file_path'))}
Module: {self._format_value(metadata.get('module_path'))}
Symbol Type: {self._format_value(metadata.get('chunk_type'))}
Symbol Name: {self._format_value(metadata.get('name'))}
Qualified Name: {self._format_value(metadata.get('qualified_name'))}
Parent Class: {self._format_value(metadata.get('parent_class'))}
Imports: {self._format_value(metadata.get('imports', []))}
Function Calls: {self._format_value(metadata.get('function_calls', []))}
Children: {self._format_value(metadata.get('children', []))}
Lines: {self._format_value(metadata.get('code_lines'))}
Docstring: {docstring}
Code:
{code}
""".strip()

    def _truncate(self, text: str, max_chars: int) -> str:
        """Trim long text to a safe length for prompts."""
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."
