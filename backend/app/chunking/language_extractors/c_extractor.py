from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class CExtractor(TreeSitterExtractor):
    language = "c"
    parser_language = "c"
    import_node_types = {
        "preproc_include",
    }
    class_node_types = {
        "struct_specifier",
        "union_specifier",
        "enum_specifier",
    }
    function_node_types = {
        "function_definition",
    }
    symbol_kind_by_node_type = {
        "preproc_include": "import",
        "struct_specifier": "struct",
        "union_specifier": "union",
        "enum_specifier": "enum",
        "function_definition": "function",
    }
