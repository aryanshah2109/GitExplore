"""Extract JavaScript symbols with the shared Tree-sitter base."""

from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class JSExtractor(TreeSitterExtractor):
    """Handle standard JavaScript source files."""

    language = "javascript"
    parser_language = "javascript"
    import_node_types = {
        "import_statement",
    }
    class_node_types = {
        "class_declaration",
    }
    function_node_types = {
        "function_declaration",
        "generator_function_declaration",
        "method_definition",
    }
    symbol_kind_by_node_type = {
        "class_declaration": "class",
        "function_declaration": "function",
        "generator_function_declaration": "function",
        "method_definition": "function",
    }
