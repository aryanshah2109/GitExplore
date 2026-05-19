from collections import defaultdict
from typing import List, Dict

from backend.app.core.config_loader import config
from backend.app.core.logger import get_logger

logger = get_logger()


class RRFRetriever:

    def __init__(self, k: int = 60):
        self.k = config.hybrid.rrf_k

    def deduplicate(self, results: List) -> List:
        seen = set()
        deduped = []
        for item in results:
            # Deduplicate by base symbol_id 
            base_id = item.chunk_id.rsplit("__part", 1)[0]
            if base_id not in seen:
                seen.add(base_id)
                deduped.append(item)
        return deduped

    def fuse(self, retrieval_results: List[List]) -> List:
        try:

            rrf_scores = defaultdict(float)
            documents = {}

            for results in retrieval_results:
                for rank, item in enumerate(results, start=1):
                    chunk_id = item.chunk_id          # attribute, not key
                    rrf_scores[chunk_id] += 1 / (self.k + rank)
                    documents[chunk_id] = item

            reranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

            final_top_k = config.hybrid.final_top_k
            final_results = []

            for chunk_id, rrf_score in reranked[:final_top_k]:
                doc = documents[chunk_id]
                doc.score = rrf_score          
                doc.retriever_type = "hybrid"  
                final_results.append(doc)

            return self.deduplicate(final_results)

        except Exception as e:
            logger.error(f"Error while hybrid retrieval: {e}")