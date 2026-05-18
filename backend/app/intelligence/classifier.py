from backend.app.core.logger import get_logger

logger = get_logger()

def detect_query_type(query: str) -> str:

    query = query.lower()

    if "class" in query:
        return "class"

    if (
        "function" in query
        or "method" in query
    ):
        return "method"

    if (
        "architecture" in query
        or "flow" in query
        or "system" in query
    ):
        return "architecture"

    if (
        "bug" in query
        or "error" in query
        or "fix" in query
    ):
        return "debug"

    return "general"