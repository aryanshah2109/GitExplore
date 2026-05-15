from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Symbol:
    repo_id: str

    symbol_id: str

    symbol_kind: str

    name: str
    signature: Optional[str] = None

    language: str = ""
    file_path: str = ""
    module_path: Optional[str] = None

    parent_class: Optional[str] = None
    
    qualified_name: Optional[str] = None

    visibility: Optional[str] = None

    is_async: bool = False

    inherits: Optional[List[str]] = field(default_factory=list)

    start_line: int = 0
    end_line: int = 0

    start_byte: int = 0
    end_byte: int = 0

    parameters: Optional[List[str]] = field(default_factory=list)

    return_type: Optional[str] = None

    imports: Optional[List[str]] = field(default_factory=list)

    function_calls: Optional[List[str]] = field(default_factory=list)

    relationships: Optional[Dict[str, List[str]]] = field(default_factory=dict)

    docstring: Optional[str] = None

    decorators: Optional[List[str]] = field(default_factory=list)

    token_count: Optional[int] = None

    embedding_text: Optional[str] = None

    children: Optional[List[str]] = field(default_factory=list)

    code: str = ""