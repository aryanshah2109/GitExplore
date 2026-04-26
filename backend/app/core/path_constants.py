from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

CONFIG_PATH = ROOT_DIR / "app" / "core" / "config.yaml"

LOGS_DIR = ROOT_DIR / "logs"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB

REPOS_DIR = ROOT_DIR / "data" / "repos"
MANIFESTS_DIR = ROOT_DIR / "data" / "manifests"
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"
EMBEDDINGS_DIR = ROOT_DIR / "data" / "embeddings"
BM25_DIR = ROOT_DIR / "data" / "bm25"

EVAL_DIR = ROOT_DIR / "eval"
QUERIES_PATH = EVAL_DIR / "queries.json"
GROUND_TRUTH_PATH = EVAL_DIR / "ground_truth.json"
EVAL_RESULTS_DIR = EVAL_DIR / "results"