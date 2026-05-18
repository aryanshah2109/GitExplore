from dataclasses import dataclass, asdict
from typing import Optional


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