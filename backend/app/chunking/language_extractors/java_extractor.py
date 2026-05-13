from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class JavaExtractor(TreeSitterExtractor):
    language = "java"
    parser_language = "java"
    import_node_types = {
        "import_declaration",
        "package_declaration",
    }
    class_node_types = {
        "class_declaration",
        "interface_declaration",
        "enum_declaration",
        "annotation_type_declaration",
    }
    function_node_types = {
        "method_declaration",
        "constructor_declaration",
    }
    symbol_kind_by_node_type = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "annotation_type_declaration": "annotation",
        "method_declaration": "function",
        "constructor_declaration": "function",
    }
