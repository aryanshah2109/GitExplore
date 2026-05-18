from collections import defaultdict
from typing import List, Dict

from backend.app.core.config_loader import config

class RRFRetriever:

    def __init__(self, k: int = 60):
        self.k = config.hybrid.rrf_k

    def fuse(self, retrieval_results: List[Dict]) -> List:

        """
        Input:
        retrieval_results = [
            bm25_results,
            dense_results
        ]
        """

        rrf_scores = defaultdict(float)
        documents = {}

        for results in retrieval_results:

            for rank, item in enumerate(results, start=1):

                chunk_id = item["chunk_id"]

                rrf_scores[chunk_id] += 1 / (
                    self.k + rank
                )

                documents[chunk_id] = item

        reranked = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        final_results = []

        for chunk_id, score in reranked:

            doc = documents[chunk_id]

            doc["rrf_score"] = score

            final_results.append(doc)

        return final_results