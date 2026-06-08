"""Extract TypeScript symbols with a small TSX override."""

from pathlib import Path

from backend.app.chunking.language_extractors.tree_sitter_extractor import (
    TreeSitterExtractor,
)


class TSExtractor(TreeSitterExtractor):
    """Handle TypeScript and TSX source files."""

    language = "typescript"
    parser_language = "typescript"
    import_node_types = {
        "import_statement",
    }
    class_node_types = {
        "class_declaration",
        "interface_declaration",
        "enum_declaration",
        "type_alias_declaration",
    }
    function_node_types = {
        "function_declaration",
        "generator_function_declaration",
        "method_definition",
    }
    symbol_kind_by_node_type = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "type_alias_declaration": "type",
        "function_declaration": "function",
        "generator_function_declaration": "function",
        "method_definition": "function",
    }

    def _parser_language_for_file(
        self,
        file_path: Path
    ) -> str:
        """Use the TSX parser for `.tsx` files."""
        if file_path.suffix.lower() == ".tsx":
            return "tsx"

        return self.parser_language
