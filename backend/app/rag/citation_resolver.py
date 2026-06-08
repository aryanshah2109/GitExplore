"""Replace model citation markers with readable source references."""

import re
from typing import Dict, List, Tuple


class CitationResolver:
    """Map source ids in answers back to file and symbol details."""

    def __init__(self, source_map: List[Dict]):
        self.source_map = {int(item["source_id"]): item for item in source_map}

    def resolve(self, answer: str) -> Tuple[str, List[int]]:
        """Rewrite citation tags and report any missing source ids."""
        invalid_sources: List[int] = []

        def replacement(match: re.Match) -> str:
            source_id = int(match.group(1))
            source = self.source_map.get(source_id)

            if not source:
                invalid_sources.append(source_id)
                return match.group(0)

            file_path = source.get("file_path", "")
            lines = source.get("code_lines", "")
            symbol = source.get("symbol_name") or source.get("symbol") or source.get("qualified_name") or ""
            return f"[{file_path} | {lines} | {symbol}]"

        resolved = re.sub(r"\[SOURCE:(\d+)\]", replacement, answer)
        return resolved, invalid_sources
