from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class RustExtractor(TreeSitterExtractor):
    language = "rust"
    parser_language = "rust"
    import_node_types = {
        "use_declaration",
        "mod_item",
        "extern_crate_declaration",
    }
    class_node_types = {
        "struct_item",
        "enum_item",
        "trait_item",
        "impl_item",
    }
    function_node_types = {
        "function_item",
    }
    symbol_kind_by_node_type = {
        "use_declaration": "import",
        "mod_item": "import",
        "extern_crate_declaration": "import",
        "struct_item": "struct",
        "enum_item": "enum",
        "trait_item": "trait",
        "impl_item": "impl",
        "function_item": "function",
    }
