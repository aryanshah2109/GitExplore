from backend.app.pipeline.ingestion_pipeline import IngestionPipeline
from backend.app.chunking.ast_traverser import ASTTraverser

repo_url = "https://github.com/aryanshah2109/FraudDetect"
branch = "main"

# repo_url = "https://github.com/aryanshah2109/DSA-Codes"
# branch = "master"

ingestion_pipeline = IngestionPipeline(
    repo_url=repo_url,
    branch_name=branch
)

manifest_path = ingestion_pipeline.run()

traverser = ASTTraverser(manifest_path)

traverser.symbol_extraction()