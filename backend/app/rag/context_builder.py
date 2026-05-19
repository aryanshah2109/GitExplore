from typing import List

from backend.app.retrieval.models.retrieval import Retrieval
from backend.app.core.config_loader import config
from backend.app.utils.tokenizer import Tokenizer
from backend.app.core.logger import get_logger

logger = get_logger()

class ContextBuilder:
    def __init__(self):
        self.budget = config.generation.context_budget_tokens
        self.tokenizer = Tokenizer()

    def build_context(self, results: List[Retrieval]) -> str:
        
        try:

            context_parts = []
            used = 0

            for r in results:
                
                code_lines = r.metadata.get('code_lines', '')
                file_path = r.metadata.get('file_path', '')
                name = r.metadata.get('name', '')
                snippet = (
                    f"[SOURCE]\n"
                    f"file_path: {file_path}\n"
                    f"symbol: {name}\n"
                    f"lines: {code_lines}\n\n"
                    f"{r.code}"
                )

                tokens = self.tokenizer.count_tokens(snippet)
                if used + tokens > self.budget:
                    break
                context_parts.append(snippet)
                used += tokens

            return "\n\n---\n\n".join(context_parts)
        
        except Exception as e:
            logger.error(f"Error while building context {e}")