"""Lightweight result object shared by the retrieval pipeline."""

from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class Retrieval:
    """Hold a retrieved chunk, its score, and the metadata needed later."""

    chunk_id : str = ""
    score: float = 0.0
    retriever_type : str = ""
    metadata: Dict = field(default_factory=dict)
    code: Optional[str] = ""
    
