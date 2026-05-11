"""
    Shared Tree-sitter based symbol extraction for source languages.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set

from tree_sitter import Node

from backend.app.chunking.models.symbol import Symbol
from backend.app.chunking.parsers.parser_manager import ParserManager
from backend.app.core.logger import get_logger


logger = get_logger()


class TreeSitterExtractor:
    """
    Base extractor for languages that can be parsed by tree-sitter.
    """

    language: str = ""
    parser_language: str = ""
    import_node_types: Set[str] = set()
    class_node_types: Set[str] = set()
    function_node_types: Set[str] = set()
    decorator_node_types: Set[str] = {
        "decorator",
        "annotation",
        "modifiers",
        "attribute_item",
    }
    call_node_types: Set[str] = {
        "call",
        "call_expression",
    }
    symbol_kind_by_node_type: Dict[str, str] = {}

    def __init__(self):
        pass

    def extract_symbols(
        self,
        file_path: Path
    ) -> List[Symbol]:
        """
        Parses a source file and extracts import/type/function symbols.
        """

        try:
            logger.info(
                f"Extracting {self.language} symbols from file: {file_path}"
            )

            source_code = file_path.read_bytes()
            parser = ParserManager.get_parser(
                self._parser_language_for_file(file_path)
            )
            tree = parser.parse(source_code)
            symbols: List[Symbol] = []

            self._traverse_tree(
                node=tree.root_node,
                source_code=source_code,
                symbols=symbols,
                file_path=file_path,
                parent_class=None,
                file_imports=[],
                decorators=[]
            )

            logger.info(
                f"Extracted {len(symbols)} symbols from {file_path.name}"
            )

            return symbols

        except Exception:
            logger.exception(
                f"Error extracting {self.language} symbols from {file_path}"
            )
            return []

    def _traverse_tree(
        self,
        node: Node,
        source_code: bytes,
        symbols: List[Symbol],
        file_path: Path,
        parent_class: Optional[str],
        file_imports: List[str],
        decorators: List[str]
    ) -> None:
        if node.type == "decorated_definition":
            definition_decorators = self._extract_decorators(
                node=node,
                source_code=source_code
            )

            for child in node.children:
                if child.type in self.decorator_node_types:
                    continue

                self._traverse_tree(
                    node=child,
                    source_code=source_code,
                    symbols=symbols,
                    file_path=file_path,
                    parent_class=parent_class,
                    file_imports=file_imports,
                    decorators=definition_decorators
                )

            return

        symbol_kind = self._symbol_kind_for_node(node)
        next_parent_class = parent_class

        if node.type in self.import_node_types:
            import_text = self._get_node_text(
                node=node,
                source_code=source_code
            ).strip()
            if import_text:
                file_imports.append(import_text)

            symbols.append(
                self._build_symbol(
                    node=node,
                    source_code=source_code,
                    file_path=file_path,
                    symbol_kind="import",
                    parent_class=None,
                    file_imports=file_imports,
                    decorators=[]
                )
            )

        elif node.type in self.class_node_types:
            symbol = self._build_symbol(
                node=node,
                source_code=source_code,
                file_path=file_path,
                symbol_kind=symbol_kind,
                parent_class=None,
                file_imports=file_imports,
                decorators=decorators
            )
            symbols.append(symbol)
            next_parent_class = symbol.name

        elif node.type in self.function_node_types:
            symbols.append(
                self._build_symbol(
                    node=node,
                    source_code=source_code,
                    file_path=file_path,
                    symbol_kind=symbol_kind,
                    parent_class=parent_class,
                    file_imports=file_imports,
                    decorators=decorators
                )
            )

        for child in node.children:
            self._traverse_tree(
                node=child,
                source_code=source_code,
                symbols=symbols,
                file_path=file_path,
                parent_class=next_parent_class,
                file_imports=file_imports,
                decorators=[]
            )

    def _build_symbol(
        self,
        node: Node,
        source_code: bytes,
        file_path: Path,
        symbol_kind: str,
        parent_class: Optional[str],
        file_imports: List[str],
        decorators: List[str]
    ) -> Symbol:
        code = self._get_node_text(
            node=node,
            source_code=source_code
        )
        fallback_name = code.splitlines()[0].strip() if code else node.type
        if symbol_kind == "import":
            name = fallback_name
        else:
            name = self._extract_name(
                node=node,
                source_code=source_code,
                fallback=fallback_name
            )

        if symbol_kind == "function" and parent_class:
            symbol_kind = "method"

        return Symbol(
            symbol_id=self._build_symbol_id(
                symbol_kind=symbol_kind,
                symbol_name=name,
                start_line=node.start_point[0] + 1
            ),
            symbol_kind=symbol_kind,
            name=name,
            signature=self._extract_signature(
                node=node,
                source_code=source_code
            ),
            language=self.language,
            file_path=str(file_path),
            parent_class=parent_class if symbol_kind == "method" else None,
            is_async=self._node_contains_child_type(
                node=node,
                child_type="async"
            ),
            inherits=self._extract_inherits(
                node=node,
                source_code=source_code
            ),
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parameters=self._extract_parameters(
                node=node,
                source_code=source_code
            ),
            return_type=self._extract_return_type(
                node=node,
                source_code=source_code
            ),
            imports=(
                [name]
                if symbol_kind == "import"
                else list(file_imports)
            ),
            function_calls=self._extract_function_calls(
                node=node,
                source_code=source_code
            ),
            relationships=self._extract_relationships(
                symbol_kind=symbol_kind,
                parent_class=parent_class,
                file_imports=file_imports
            ),
            docstring=self._extract_docstring(
                node=node,
                source_code=source_code
            ),
            decorators=decorators,
            children=self._extract_children(
                node=node,
                source_code=source_code
            ),
            code=code
        )

    def _symbol_kind_for_node(
        self,
        node: Node
    ) -> str:
        if node.type in self.symbol_kind_by_node_type:
            return self.symbol_kind_by_node_type[node.type]

        if node.type in self.class_node_types:
            return "class"

        if node.type in self.function_node_types:
            return "function"

        return "symbol"

    def _extract_name(
        self,
        node: Node,
        source_code: bytes,
        fallback: str
    ) -> str:
        for field_name in ("name", "declarator", "declaration"):
            name_node = node.child_by_field_name(field_name)
            if name_node is None:
                continue

            identifier = self._find_identifier(name_node, source_code)
            if identifier:
                return identifier

            text = self._get_node_text(name_node, source_code).strip()
            if text:
                return text

        identifier = self._find_identifier(node, source_code)
        if identifier:
            return identifier

        return fallback

    def _find_identifier(
        self,
        node: Node,
        source_code: bytes
    ) -> Optional[str]:
        identifier_types = {
            "identifier",
            "field_identifier",
            "property_identifier",
            "type_identifier",
            "scoped_identifier",
        }

        if node.type in identifier_types:
            return self._get_node_text(node, source_code).strip()

        for child in node.children:
            identifier = self._find_identifier(child, source_code)
            if identifier:
                return identifier

        return None

    def _extract_signature(
        self,
        node: Node,
        source_code: bytes
    ) -> Optional[str]:
        body_node = node.child_by_field_name("body")
        if body_node is None:
            return None

        return source_code[
            node.start_byte:body_node.start_byte
        ].decode("utf-8", errors="ignore").strip()

    def _extract_parameters(
        self,
        node: Node,
        source_code: bytes
    ) -> List[str]:
        parameters_node = node.child_by_field_name("parameters")
        if parameters_node is None:
            return []

        parameters = []
        for child in parameters_node.named_children:
            text = self._get_node_text(child, source_code).strip()
            if text and text not in {",", "(", ")"}:
                parameters.append(text)

        return parameters

    def _extract_return_type(
        self,
        node: Node,
        source_code: bytes
    ) -> Optional[str]:
        for field_name in ("return_type", "type"):
            return_node = node.child_by_field_name(field_name)
            if return_node is not None:
                return_type = self._get_node_text(
                    return_node,
                    source_code
                ).strip()
                if return_type.startswith("->"):
                    return_type = return_type[2:].strip()

                return return_type

        return None

    def _extract_inherits(
        self,
        node: Node,
        source_code: bytes
    ) -> List[str]:
        inheritance_node = node.child_by_field_name("superclasses")
        if inheritance_node is None:
            inheritance_node = node.child_by_field_name("bases")

        if inheritance_node is None:
            return []

        inherits = []
        for child in inheritance_node.named_children:
            text = self._get_node_text(child, source_code).strip()
            if text and text not in {",", "(", ")"}:
                inherits.append(text)

        return inherits

    def _extract_decorators(
        self,
        node: Node,
        source_code: bytes
    ) -> List[str]:
        decorators = []

        for child in node.children:
            if child.type not in self.decorator_node_types:
                continue

            text = self._get_node_text(child, source_code).strip()
            if text:
                decorators.append(text)

        return decorators

    def _extract_docstring(
        self,
        node: Node,
        source_code: bytes
    ) -> Optional[str]:
        body_node = node.child_by_field_name("body")
        if body_node is None:
            return None

        for child in body_node.named_children:
            docstring = self._string_literal_text(
                node=child,
                source_code=source_code
            )
            if docstring:
                return docstring

            if child.type not in {
                "comment",
                "pass_statement",
            }:
                return None

        return None

    def _string_literal_text(
        self,
        node: Node,
        source_code: bytes
    ) -> Optional[str]:
        if node.type in {
            "string",
            "string_literal",
            "raw_string_literal",
        }:
            return self._strip_string_quotes(
                self._get_node_text(node, source_code).strip()
            )

        if node.type == "expression_statement":
            for child in node.named_children:
                text = self._string_literal_text(child, source_code)
                if text:
                    return text

        return None

    def _strip_string_quotes(
        self,
        text: str
    ) -> str:
        prefixes = ("r", "R", "u", "U", "f", "F", "b", "B")
        while text and text[0] in prefixes:
            text = text[1:]

        quote_pairs = (
            ('"""', '"""'),
            ("'''", "'''"),
            ('"', '"'),
            ("'", "'"),
        )

        for start_quote, end_quote in quote_pairs:
            if text.startswith(start_quote) and text.endswith(end_quote):
                return text[
                    len(start_quote):-len(end_quote)
                ].strip()

        return text

    def _extract_function_calls(
        self,
        node: Node,
        source_code: bytes
    ) -> List[str]:
        calls: List[str] = []
        self._collect_function_calls(
            node=node,
            source_code=source_code,
            calls=calls
        )
        return calls

    def _collect_function_calls(
        self,
        node: Node,
        source_code: bytes,
        calls: List[str]
    ) -> None:
        if node.type in self.call_node_types:
            function_node = node.child_by_field_name("function")
            call_name = self._get_call_name(
                node=function_node or node,
                source_code=source_code
            )
            if call_name and call_name not in calls:
                calls.append(call_name)

        for child in node.children:
            self._collect_function_calls(
                node=child,
                source_code=source_code,
                calls=calls
            )

    def _get_call_name(
        self,
        node: Node,
        source_code: bytes
    ) -> Optional[str]:
        text = self._get_node_text(node, source_code).strip()
        if not text:
            return None

        if "(" in text:
            text = text.split("(", 1)[0].strip()

        return text

    def _extract_children(
        self,
        node: Node,
        source_code: bytes
    ) -> List[str]:
        if node.type not in self.class_node_types:
            return []

        children = []
        for child in node.children:
            if child.type not in self.function_node_types:
                self._collect_immediate_child_functions(
                    node=child,
                    source_code=source_code,
                    children=children
                )
                continue

            name = self._extract_name(
                node=child,
                source_code=source_code,
                fallback=self._get_node_text(
                    child,
                    source_code
                ).splitlines()[0].strip()
            )
            if name and name not in children:
                children.append(name)

        return children

    def _collect_immediate_child_functions(
        self,
        node: Node,
        source_code: bytes,
        children: List[str]
    ) -> None:
        for child in node.children:
            if child.type in self.class_node_types:
                continue

            if child.type in self.function_node_types:
                name = self._extract_name(
                    node=child,
                    source_code=source_code,
                    fallback=self._get_node_text(
                        child,
                        source_code
                    ).splitlines()[0].strip()
                )
                if name and name not in children:
                    children.append(name)
                continue

            self._collect_immediate_child_functions(
                node=child,
                source_code=source_code,
                children=children
            )

    def _extract_relationships(
        self,
        symbol_kind: str,
        parent_class: Optional[str],
        file_imports: List[str]
    ) -> Dict[str, List[str]]:
        relationships: Dict[str, List[str]] = {}

        if parent_class and symbol_kind == "method":
            relationships["parent_class"] = [parent_class]

        if file_imports:
            relationships["imports"] = list(file_imports)

        return relationships

    def _node_contains_child_type(
        self,
        node: Node,
        child_type: str
    ) -> bool:
        return any(child.type == child_type for child in node.children)

    def _get_node_text(
        self,
        node: Optional[Node],
        source_code: bytes
    ) -> str:
        if node is None:
            return ""

        return source_code[
            node.start_byte:node.end_byte
        ].decode("utf-8", errors="ignore")

    def _build_symbol_id(
        self,
        symbol_kind: str,
        symbol_name: str,
        start_line: int
    ) -> str:
        return (
            f"{symbol_kind}:"
            f"{symbol_name}:"
            f"{start_line}"
        )

    def _parser_language_for_file(
        self,
        file_path: Path
    ) -> str:
        return self.parser_language or self.language
