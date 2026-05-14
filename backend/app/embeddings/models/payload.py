from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Payload:

    repo_id: str

    language: str
    symbol: str
    chunk_type: str

    text: str

    file_path: str = ""

    start_line: int = 0
    end_line: int = 0

    parent_class: Optional[str] = None