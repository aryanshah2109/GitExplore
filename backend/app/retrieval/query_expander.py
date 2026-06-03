import re
from dataclasses import dataclass
from typing import List, Set

from backend.app.core.config_loader import config


@dataclass
class QueryExpansionResult:
    original_query: str
    expanded_terms: List[str]
    expanded_query_text: str


class QueryExpander:
    def __init__(self):
        retrieval_config = getattr(config, "retrieval", None)
        query_expansion_config = getattr(retrieval_config, "query_expansion", None) if retrieval_config else None

        self.enabled = True if query_expansion_config is None else bool(getattr(query_expansion_config, "enabled", True))
        self.max_terms = int(getattr(query_expansion_config, "max_terms", 12)) if query_expansion_config else 12

    def expand(self, query: str, query_type: str | None = None) -> QueryExpansionResult:
        if not self.enabled:
            return QueryExpansionResult(
                original_query=query,
                expanded_terms=[],
                expanded_query_text=query,
            )

        terms = self._build_terms(query, query_type=query_type)
        expanded_query_text = " ".join([query] + terms)
        return QueryExpansionResult(
            original_query=query,
            expanded_terms=terms,
            expanded_query_text=expanded_query_text,
        )

    def _build_terms(self, query: str, query_type: str | None = None) -> List[str]:
        raw_tokens = self._tokenize(query)
        variants: List[str] = []
        seen: Set[str] = set()

        for token in raw_tokens:
            for variant in self._variants_for_token(token):
                normalized = variant.lower().strip()
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                variants.append(normalized)
                if len(variants) >= self.max_terms:
                    return variants

        for phrase in self._generic_variants(query_type):
            normalized = phrase.lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                variants.append(normalized)
                if len(variants) >= self.max_terms:
                    return variants

        return variants

    def _tokenize(self, query: str) -> List[str]:
        query = re.sub(r"([a-z])([A-Z])", r"\1 \2", query)
        query = query.replace("_", " ")
        return re.findall(r"\b[\w/.-]+\b", query)

    def _variants_for_token(self, token: str) -> List[str]:
        token = token.strip()
        if not token:
            return []

        variants = [token]

        parts = [part for part in re.split(r"[./:-]+", token) if part]
        variants.extend(parts)

        camel_split = re.sub(r"([a-z])([A-Z])", r"\1 \2", token).split()
        variants.extend(camel_split)

        if len(token) > 3:
            if token.endswith("s"):
                variants.append(token[:-1])
            else:
                variants.append(f"{token}s")

        return variants

    def _generic_variants(self, query_type: str | None) -> List[str]:
        if query_type == "find_function":
            return ["definition", "implementation", "location", "defined", "declared"]
        if query_type == "explain_code":
            return ["flow", "process", "usage", "behavior"]
        if query_type == "debug":
            return ["error", "failure", "root cause", "fix", "issue"]
        if query_type == "architecture":
            return ["architecture", "components", "modules", "flow", "end-to-end"]
        return []
