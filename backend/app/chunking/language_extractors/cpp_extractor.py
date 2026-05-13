from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class CPPExtractor(TreeSitterExtractor):
    language = "cpp"
    parser_language = "cpp"
    import_node_types = {
        "preproc_include",
        "namespace_alias_definition",
        "using_declaration",
    }
    class_node_types = {
        "class_specifier",
        "struct_specifier",
        "union_specifier",
        "enum_specifier",
        "namespace_definition",
    }
    function_node_types = {
        "function_definition",
    }
    symbol_kind_by_node_type = {
        "class_specifier": "class",
        "struct_specifier": "struct",
        "union_specifier": "union",
        "enum_specifier": "enum",
        "namespace_definition": "namespace",
        "function_definition": "function",
    }
