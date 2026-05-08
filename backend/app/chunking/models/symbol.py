from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Symbol:

    symbol_id: str

    symbol_kind: str

    name: str
    signature: Optional[str]

    language: str
    file_path: str
    module_path: Optional[str]

    parent_class: Optional[str]

    visibility: Optional[str]

    is_async: bool = False

    inherits: Optional[List[str]]

    start_line: int
    end_line: int

    start_byte: int
    end_byte: int

    parameters: Optional[List[str]]

    return_type: Optional[str]

    imports: Optional[List[str]]

    function_calls: Optional[List[str]]

    relationships: Optional[Dict[str, List[str]]]

    docstring: Optional[str]

    decorators: Optional[List[str]]

    token_count: Optional[int]

    embedding_text: Optional[str]

    children: Optional[List[str]]

    code: str