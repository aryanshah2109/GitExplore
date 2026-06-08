"""Extract Python symbols with the shared Tree-sitter base."""

from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class PyExtractor(TreeSitterExtractor):
    """Handle standard Python source files."""

    language = "python"
    parser_language = "python"
    import_node_types = {
        "import_statement",
        "import_from_statement",
    }
    class_node_types = {
        "class_definition",
    }
    function_node_types = {
        "function_definition",
    }
    symbol_kind_by_node_type = {
        "class_definition": "class",
        "function_definition": "function",
    }
