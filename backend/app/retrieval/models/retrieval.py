from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class Retrieval:

    chunk_id : str = ""
    score: float = 0.0
    retriever_type : str = ""
    metadata: Dict = field(default_factory=dict)
    code: Optional[str] = ""