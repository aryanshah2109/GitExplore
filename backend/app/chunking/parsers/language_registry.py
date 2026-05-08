from backend.app.chunking.language_extractors.python_extractor import PyExtractor
from backend.app.chunking.language_extractors.c_extractor import CExtractor
from backend.app.chunking.language_extractors.cpp_extractor import CPPExtractor
from backend.app.chunking.language_extractors.javascript_extractor import JSExtractor
from backend.app.chunking.language_extractors.java_extractor import JavaExtractor
from backend.app.chunking.language_extractors.go_extractor import GoExtractor
from backend.app.chunking.language_extractors.rust_extractor import RustExtractor
from backend.app.chunking.language_extractors.typescript_extractor import TSExtractor


LANGUAGE_REGISTRY = {
    "c": {
        "extensions": [".c"],
        "extractor": CExtractor
    },
    "cpp": {
        "extensions": [".cpp"],
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