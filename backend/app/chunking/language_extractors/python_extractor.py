from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class PyExtractor(TreeSitterExtractor):
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
        "import_statement": "import",
        "import_from_statement": "import",
        "class_definition": "class",
        "function_definition": "function",
    }
