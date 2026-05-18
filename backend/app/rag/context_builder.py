from backend.app.retrieval.bm25 import BM25Okapi
from backend.app.retrieval.dense import DenseRetriever
from backend.app.retrieval.hybrid import RRFRetriever
from backend.app.core.logger import get_logger

logger = get_logger()

class ContextBuilder:
    def __init__(self):
        pass

    def build_context(self):
        pass