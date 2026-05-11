from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class GoExtractor(TreeSitterExtractor):
    language = "go"
    parser_language = "go"
    import_node_types = {
        "import_declaration",
        "package_clause",
    }
    class_node_types = {
        "type_declaration",
    }
    function_node_types = {
        "function_declaration",
        "method_declaration",
    }
    symbol_kind_by_node_type = {
        "package_clause": "import",
        "import_declaration": "import",
        "type_declaration": "type",
        "function_declaration": "function",
        "method_declaration": "function",
    }
