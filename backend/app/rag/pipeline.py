"""Orchestrate retrieval, answer generation, and answer judging."""

from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger
from backend.app.retrieval.bm25 import BM25Retriever
from backend.app.retrieval.dense import DenseRetriever
from backend.app.retrieval.hybrid import RRFRetriever
from backend.app.retrieval.reranker import Reranker
from backend.app.retrieval.models.retrieval import Retrieval
from backend.app.retrieval.query_expander import QueryExpander
from backend.app.rag.context_builder import ContextBuilder
from backend.app.rag.citation_resolver import CitationResolver
from backend.app.rag.llm_generation_client import LLMGenerationClient
from backend.app.rag.judge import LLMJudgeClient
from backend.app.intelligence.classifier import detect_query_type

logger = get_logger()


class RAGPipeline:
    """Run the full retrieval and generation flow for one query."""

    def __init__(self, chunks: List[Dict], repo_id: str):
        self.chunks = chunks
        self.repo_id = repo_id

        self.bm25 = BM25Retriever(chunks)
        self.dense = DenseRetriever()
        self.rrf = RRFRetriever()
        self.reranker = Reranker()
        self.context_builder = ContextBuilder()
        self.llm = LLMGenerationClient()
        self.judge_llm = LLMJudgeClient()
        self.query_expander = QueryExpander()

        self.chunk_lookup = self._build_chunk_lookup(chunks)
        self.summary_chunks = [
            chunk for chunk in chunks
            if self._normalize(chunk.get("symbol_kind")) == "repo_summary"
        ]

    def query(self, user_query: str) -> dict:
        """Run retrieval, generation, citation fixing, and judging."""
        try:
            query_type = detect_query_type(user_query)
            logger.info(f"Query type: {query_type}")

            expanded_query = self.query_expander.expand(user_query, query_type=query_type)
            logger.info(
                "Expanded query terms: count=%d preview=%s",
                len(expanded_query.expanded_terms),
                expanded_query.expanded_terms[:5],
            )

            retrieval_plan = self._retrieval_plan(query_type)

            bm25_results = self.bm25.retrieve(
                user_query,
                exclude_kinds=retrieval_plan["exclude_kinds"],
                top_k=retrieval_plan["bm25_top_k"],
                query_type=query_type,
                repo_id=self.repo_id,
            )
            self._log_results("BM25", bm25_results)

            dense_results = self.dense.get_context(
                user_query,
                self.repo_id,
                top_k=retrieval_plan["dense_top_k"],
                query_type=query_type,
            )
            self._log_results("Dense", dense_results)

            hybrid_results = self.rrf.fuse([bm25_results, dense_results])
            if not hybrid_results:
                hybrid_results = bm25_results or dense_results or []
            hybrid_results = self._inject_summary_chunks(
                hybrid_results,
                query_type=query_type,
                max_summary=retrieval_plan["summary_top_k"],
            )
            self._log_results("Hybrid", hybrid_results)

            reranked_results = self.reranker.rerank(
                user_query,
                hybrid_results,
                top_n=retrieval_plan["rerank_top_k"],
            )
            self._log_results("Reranked", reranked_results)

            expanded_results = self._expand_structural_context(
                reranked_results,
                max_related=retrieval_plan["expanded_related_limit"],
                depth=retrieval_plan["expansion_depth"],
            )
            self._log_results("Expanded", expanded_results)

            context_budget = retrieval_plan["context_budget_tokens"]
            context = self.context_builder.build_context(
                expanded_results,
                budget=context_budget,
            )

            if not context.strip():
                logger.info("No context available after retrieval; returning fallback response.")
                return {
                    "status": "no_context",
                    "answer": "I couldn't find enough relevant code context to answer this query reliably.",
                    "judgement": {
                        "faithfulness": 0,
                        "retrieval_relevance": 0,
                        "citation_accuracy": 0,
                        "query_type_fit": 0,
                        "reasoning": "Retrieval returned no usable context, so generation was skipped.",
                    },
                    "query_type": query_type,
                    "citation_validation": {"invalid_source_ids": []},
                }

            logger.debug("Generating answer")
            raw_answer = self.llm.generate_answer(
                query=user_query,
                context=context,
                query_type=query_type,
            )

            citation_resolver = CitationResolver(self.context_builder.last_sources)
            answer, invalid_sources = citation_resolver.resolve(raw_answer)
            if invalid_sources:
                logger.warning(f"Invalid source citations referenced by model: {sorted(set(invalid_sources))}")

            logger.debug("Checking score from judge LLM")
            judgement = self.judge_llm.judge_answer(
                query=user_query,
                context=context,
                answer=answer,
                query_type=query_type,
            )

            return {
                "status": "ok",
                "answer": answer,
                "judgement": judgement,
                "query_type": query_type,
                "citation_validation": {"invalid_source_ids": sorted(set(invalid_sources))},
            }

        except Exception as e:
            logger.error(f"Error while running RAG Pipeline: {e}")
            return {
                "status": "error",
                "answer": None,
                "judgement": None,
                "error": str(e),
            }

    def clear_session(self):
        """Clear chat history when the active repo changes."""
        self.llm.clear_history()

    def _retrieval_plan(self, query_type: str) -> Dict[str, Any]:
        retrieval_config = getattr(config, "retrieval", None)
        architecture_config = getattr(retrieval_config, "architecture", None) if retrieval_config else None
        structural_config = getattr(retrieval_config, "structural_expansion", None) if retrieval_config else None

        is_architecture = query_type == "architecture"

        bm25_top_k = config.bm25.top_k
        dense_top_k = config.vector_db.top_k
        rerank_top_k = config.reranker.top_k
        summary_top_k = 1 if self.summary_chunks else 0
        context_budget_tokens = config.generation.context_budget_tokens
        expanded_related_limit = getattr(structural_config, "max_related_chunks", 8) if structural_config else 8
        expansion_depth = getattr(structural_config, "max_depth", 1) if structural_config else 1

        if is_architecture:
            bm25_top_k = max(bm25_top_k, int(getattr(architecture_config, "bm25_top_k", 40)) if architecture_config else 40)
            dense_top_k = max(dense_top_k, int(getattr(architecture_config, "dense_top_k", 40)) if architecture_config else 40)
            rerank_top_k = max(rerank_top_k, int(getattr(architecture_config, "rerank_top_k", 12)) if architecture_config else 12)
            summary_top_k = max(summary_top_k, 1)
            arch_budget = getattr(architecture_config, "context_budget_tokens", None) if architecture_config else None
            context_budget_tokens = int(arch_budget) if arch_budget else int(context_budget_tokens * 1.5)
            expanded_related_limit = max(expanded_related_limit, int(getattr(architecture_config, "expanded_related_limit", 12)) if architecture_config else 12)
            expansion_depth = max(expansion_depth, int(getattr(architecture_config, "expansion_depth", 2)) if architecture_config else 2)

        return {
            "exclude_kinds": [] if is_architecture else ["document"] + (["module"] if query_type in ("find_function", "debug") else []),
            "bm25_top_k": bm25_top_k,
            "dense_top_k": dense_top_k,
            "rerank_top_k": rerank_top_k,
            "summary_top_k": summary_top_k,
            "context_budget_tokens": context_budget_tokens,
            "expanded_related_limit": expanded_related_limit,
            "expansion_depth": expansion_depth,
        }

    def _inject_summary_chunks(
        self,
        results: List[Retrieval],
        query_type: str,
        max_summary: int,
    ) -> List[Retrieval]:
        if not self.summary_chunks or max_summary <= 0:
            return results

        if query_type != "architecture":
            return results

        existing_ids = {item.chunk_id for item in results}
        summary_results = []

        base_score = max((item.score for item in results), default=0.0) + 1.0

        for index, chunk in enumerate(self.summary_chunks[:max_summary], start=1):
            retrieval = self._chunk_to_retrieval(chunk)
            retrieval.score = base_score + index
            retrieval.retriever_type = "summary"
            if retrieval.chunk_id not in existing_ids:
                summary_results.append(retrieval)

        return summary_results + results

    def _chunk_to_retrieval(self, chunk: Dict) -> Retrieval:
        return Retrieval(
            chunk_id=chunk.get("symbol_id", ""),
            score=0.0,
            retriever_type="summary",
            metadata={
                "chunk_type": chunk.get("symbol_kind", ""),
                "language": chunk.get("language", ""),
                "parent_class": chunk.get("parent_class"),
                "file_path": chunk.get("file_path", ""),
                "module_path": chunk.get("module_path", ""),
                "name": chunk.get("name", ""),
                "qualified_name": chunk.get("qualified_name", ""),
                "imports": chunk.get("imports", []),
                "function_calls": chunk.get("function_calls", []),
                "children": chunk.get("children", []),
                "docstring": chunk.get("docstring", ""),
                "relationships": chunk.get("relationships", {}),
                "code_lines": f"{chunk.get('start_line', 1)} - {chunk.get('end_line', 1)}",
            },
            code=chunk.get("code", ""),
        )

    def _expand_structural_context(self, results: List[Retrieval], max_related: int, depth: int) -> List[Retrieval]:
        expanded: List[Retrieval] = []
        seen = set()
        seed_ids = {self._base_chunk_id(item.chunk_id) for item in results}

        for item in results:
            base_id = self._base_chunk_id(item.chunk_id)
            if base_id not in seen:
                expanded.append(item)
                seen.add(base_id)

        if depth <= 0 or max_related <= 0:
            return expanded

        queue: List[Tuple[Retrieval, int]] = [(item, 0) for item in results]

        while queue and len(expanded) < len(results) + max_related:
            current, current_depth = queue.pop(0)
            if current_depth >= depth:
                continue

            related_ids = self._collect_related_chunk_ids(current)

            for related_id in related_ids:
                base_related_id = self._base_chunk_id(related_id)
                if base_related_id in seen or (base_related_id in seed_ids and current_depth > 0):
                    continue

                related_chunk = self._pick_chunk_by_id(related_id)
                if not related_chunk:
                    continue

                retrieval = self._chunk_to_retrieval(related_chunk)
                retrieval.score = max(0.0, current.score - 0.01 * (current_depth + 1))
                retrieval.retriever_type = "expanded"
                expanded.append(retrieval)
                seen.add(base_related_id)
                queue.append((retrieval, current_depth + 1))

                if len(expanded) >= len(results) + max_related:
                    break

        return expanded

    def _collect_related_chunk_ids(self, retrieval: Retrieval) -> List[str]:
        metadata = retrieval.metadata or {}
        if self._normalize(metadata.get("chunk_type")) == "repo_summary":
            return []

        related_terms = []
        related_terms.extend(self._ensure_list(metadata.get("imports")))
        related_terms.extend(self._ensure_list(metadata.get("function_calls")))
        related_terms.extend(self._ensure_list(metadata.get("children")))

        relationships = metadata.get("relationships", {})
        if isinstance(relationships, dict):
            for value in relationships.values():
                related_terms.extend(self._ensure_list(value))

        related_ids = []
        for term in related_terms:
            related_ids.extend(self._lookup_related_ids(term, retrieval))

        return self._dedupe(related_ids)

    def _lookup_related_ids(self, term: str, retrieval: Retrieval) -> List[str]:
        normalized = self._normalize(term)
        if not normalized:
            return []

        matches = []

        for chunk in self.chunks:
            if self._base_chunk_id(chunk.get("symbol_id", "")) == self._base_chunk_id(retrieval.chunk_id):
                continue

            candidates = [
                self._normalize(chunk.get("name")),
                self._normalize(chunk.get("qualified_name")),
                self._normalize(chunk.get("module_path")),
                self._normalize(chunk.get("file_path")),
            ]

            if normalized in candidates or any(candidate.endswith(f".{normalized}") for candidate in candidates if candidate):
                matches.append(chunk.get("symbol_id", ""))
                continue

            if normalized and any(normalized in candidate for candidate in candidates if candidate):
                matches.append(chunk.get("symbol_id", ""))

        return matches

    def _pick_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        base_id = self._base_chunk_id(chunk_id)
        return self.chunk_lookup.get(base_id)

    def _build_chunk_lookup(self, chunks: List[Dict]) -> Dict[str, Dict]:
        lookup = {}
        for chunk in chunks:
            lookup.setdefault(self._base_chunk_id(chunk.get("symbol_id", "")), chunk)
        return lookup

    def _base_chunk_id(self, chunk_id: str) -> str:
        if "__part" in chunk_id:
            return chunk_id.split("__part", 1)[0]
        if "__sub" in chunk_id:
            return chunk_id.split("__sub", 1)[0]
        return chunk_id

    def _ensure_list(self, value) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if item is not None and str(item).strip()]
        if isinstance(value, tuple):
            return [str(item) for item in value if item is not None and str(item).strip()]
        if isinstance(value, set):
            return [str(item) for item in value if item is not None and str(item).strip()]
        if isinstance(value, dict):
            flattened = []
            for key, val in value.items():
                flattened.append(str(key))
                flattened.extend(self._ensure_list(val))
            return self._dedupe(flattened)
        text = str(value).strip()
        return [text] if text else []

    def _dedupe(self, items: List[str]) -> List[str]:
        seen = set()
        results = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            results.append(item)
        return results

    def _normalize(self, value) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    def _log_results(self, label: str, results: List[Retrieval]) -> None:
        formatted = [
            {
                "chunk_id": item.chunk_id,
                "score": round(float(item.score), 4),
                "type": item.metadata.get("chunk_type") if item.metadata else "",
                "symbol": item.metadata.get("name") if item.metadata else "",
            }
            for item in results[:3]
        ]
        logger.info(f"{label} top results: {formatted}")
