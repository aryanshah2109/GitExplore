from backend.app.chunking.language_extractors.python_extractor import PyExtractor
from backend.app.chunking.language_extractors.c_extractor import CExtractor
from backend.app.chunking.language_extractors.cpp_extractor import CPPExtractor
from backend.app.chunking.language_extractors.javascript_extractor import JSExtractor
from backend.app.chunking.language_extractors.java_extractor import JavaExtractor
from backend.app.chunking.language_extractors.go_extractor import GoExtractor
from backend.app.chunking.language_extractors.rust_extractor import RustExtractor
from backend.app.chunking.language_extractors.typescript_extractor import TSExtractor
from backend.app.chunking.language_extractors.fallback_extractor import FallbackExtractor


LANGUAGE_REGISTRY = {
    "c": {
        "extensions": [".c", ".h"],
        "extractor": CExtractor
    },
    "cpp": {
        "extensions": [".cpp", ".cc", ".cxx", ".hpp"],
        "extractor": CPPExtractor
    },
    "go": {
        "extensions": [".go"],
        "extractor": GoExtractor
    },
    "java": {
        "extensions": [".java"],
        "extractor": JavaExtractor
    },
    "js": {
        "extensions": [".js", ".jsx"],
        "extractor": JSExtractor
    },
    "py": {
        "extensions": [".py"],
        "extractor": PyExtractor
    },
    "rs": {
        "extensions": [".rs"],
        "extractor": RustExtractor
    },
    "ts": {
        "extensions": [".ts", ".tsx"],
        "extractor": TSExtractor
    },

}


def get_extractor(extension: str):
    normalized_extension = (extension or "").lower()
    if normalized_extension and not normalized_extension.startswith("."):
        normalized_extension = f".{normalized_extension}"

    for language_config in LANGUAGE_REGISTRY.values():
        extractor = language_config["extractor"]
        if (
            normalized_extension in language_config["extensions"]
            and hasattr(extractor, "extract_symbols")
        ):
            return extractor

    return FallbackExtractor
