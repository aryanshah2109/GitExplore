"""Classify user queries so the pipeline can pick a better retrieval plan."""

import os
from groq import Groq
from backend.app.core.logger import get_logger
from backend.app.intelligence.prompt_templates import CLASSIFIER_PROMPT
from backend.app.core.config_loader import config

logger = get_logger()

VALID_TYPES = config.query.types

MODEL_NAME = config.query.model_name

def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def detect_query_type(query: str) -> str:
    """Return the detected query type, or fall back to explain_code."""
    try:
        response = get_client().chat.completions.create(
            model= MODEL_NAME,
            messages=[
                {"role": "system", "content": CLASSIFIER_PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0.0,
            max_tokens=10
        )
        result = response.choices[0].message.content.strip().lower()

        if result in VALID_TYPES:
            logger.info(f"Query classified as: {result}")
            return result

        logger.warning(f"Unexpected classifier output: {result}, defaulting to explain_code")
        return "explain_code"

    except Exception as e:
        logger.error(f"Classifier failed: {e}, defaulting to explain_code")
        return "explain_code"
