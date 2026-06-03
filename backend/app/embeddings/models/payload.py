from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class Payload:

    repo_id: str

    language: str
    symbol: str
    chunk_type: str

    module_path: str = ""

    start_line: int = 0
    end_line: int = 0

    symbol_id: str = ""

    parent_class: Optional[str] = None

    file_path: str = ""
    code: str = ""

    imports: list = field(default_factory=list)
    function_calls: list = field(default_factory=list)
    qualified_name: str = ""
    children: list = field(default_factory=list)
    docstring: str = ""
    relationships: Dict[str, List[str]] = field(default_factory=dict)
