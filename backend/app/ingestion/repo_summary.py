from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional


class RepositorySummaryBuilder:
    def __init__(self, manifest: Dict, chunks: List[Dict]):
        self.manifest = manifest or {}
        self.chunks = chunks or []

    def build_summary_chunk(self) -> Dict:
        repo_id = self.manifest.get("repo_id", "repository")
        languages = self._format_languages()
        directories = self._format_directories()
        modules = self._format_modules()
        docs = self._format_files_by_kind({"document"})
        configs = self._format_config_files()

        summary_lines = [
            f"Repository summary for {self.manifest.get('repo_name', repo_id)}.",
            f"Detected languages: {languages}.",
            f"Directory structure: {directories}.",
            f"Notable modules: {modules}.",
            f"Documentation files: {docs}.",
            f"Configuration files: {configs}.",
            "This summary is derived from repository metadata and extracted symbols only.",
        ]

        summary_text = " ".join(line for line in summary_lines if line.strip())

        return {
            "repo_id": repo_id,
            "symbol_id": f"repo_summary:{repo_id}",
            "symbol_kind": "repo_summary",
            "name": "repository_summary",
            "qualified_name": "repository_summary",
            "language": "meta",
            "file_path": "__repository_summary__",
            "module_path": "repository.summary",
            "parent_class": None,
            "imports": [],
            "function_calls": [],
            "relationships": {
                "languages": self._top_languages(),
                "modules": self._top_module_paths(),
                "documents": self._top_document_paths(),
            },
            "docstring": summary_text,
            "children": [],
            "code": summary_text,
            "embedding_text": summary_text,
            "start_line": 1,
            "end_line": 1,
        }

    def _top_languages(self) -> List[str]:
        counts = Counter()
        for file_entry in self.manifest.get("files", []):
            language = file_entry.get("language")
            if language:
                counts[language] += 1
        return [f"{name} ({count})" for name, count in counts.most_common(8)]

    def _format_languages(self) -> str:
        items = self._top_languages()
        return ", ".join(items) if items else "not available"

    def _top_document_paths(self) -> List[str]:
        docs = []
        for chunk in self.chunks:
            if chunk.get("symbol_kind") == "document":
                docs.append(chunk.get("file_path", ""))
        return self._dedupe_top_entries(docs, 6)

    def _top_module_paths(self) -> List[str]:
        counts = Counter()
        for chunk in self.chunks:
            module_path = chunk.get("module_path")
            if module_path:
                counts[module_path] += 1
        return [module for module, _ in counts.most_common(8)]

    def _format_modules(self) -> str:
        modules = self._top_module_paths()
        return ", ".join(modules) if modules else "not available"

    def _format_files_by_kind(self, kinds: set[str]) -> str:
        matched = []
        for chunk in self.chunks:
            if chunk.get("symbol_kind") in kinds:
                matched.append(chunk.get("file_path", ""))
        top = self._dedupe_top_entries(matched, 6)
        return ", ".join(top) if top else "not available"

    def _format_config_files(self) -> str:
        matched = []
        config_suffixes = {".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".env"}
        for file_entry in self.manifest.get("files", []):
            file_name = file_entry.get("file_name", "")
            suffix = Path(file_name).suffix.lower()
            if suffix in config_suffixes or Path(file_name).name.lower() in {"dockerfile", "makefile", "procfile"}:
                matched.append(file_name)
        top = self._dedupe_top_entries(matched, 6)
        return ", ".join(top) if top else "not available"

    def _format_directories(self) -> str:
        directory_counts = Counter()
        for file_entry in self.manifest.get("files", []):
            file_name = file_entry.get("file_name", "")
            parent = str(Path(file_name).parent)
            if parent and parent != ".":
                directory_counts[parent] += 1
        top = [directory for directory, _ in directory_counts.most_common(8)]
        return ", ".join(top) if top else "root only"

    def _dedupe_top_entries(self, items: List[str], limit: int) -> List[str]:
        seen = set()
        results = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            results.append(item)
            if len(results) >= limit:
                break
        return results
