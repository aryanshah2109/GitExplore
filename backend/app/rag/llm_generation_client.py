"""Generate final answers with the configured LLM."""

from groq import Groq
import os
from typing import Any

from backend.app.core.logger import get_logger
from backend.app.intelligence.prompt_templates import LLM_GENERATION_PROMPT
from backend.app.core.config_loader import config
from backend.app.utils.groq_retry import groq_completion_with_retry

logger = get_logger()

class LLMGenerationClient:
    """Wrap the answer model and keep a short conversation history."""

    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.generation_prompt = LLM_GENERATION_PROMPT
        self.model_name = config.generation.model_name
        self.max_turns = config.generation.conversation_history_turns
        self.history = []
        self.num_predict = config.generation.num_predict
        self.temperature = config.generation.temperature
        self.max_retries = getattr(config.generation, "max_retries", 3)
        self.retry_delay_seconds = getattr(config.generation, "retry_delay_seconds", 1.5)

    def _create_completion(self, messages: list[dict[str, str]]) -> Any:
        """Call the LLM with simple retry handling for rate limits."""
        return groq_completion_with_retry(
            client=self.client,
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.num_predict,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay_seconds,
        )

    def generate_answer(self, query: str, context: str, query_type: str | None = None) -> str:
        """Return the model answer for the current query and context."""

        logger.info("Generating answer for given query.")

        user_prompt = f"""
        QUERY TYPE:
        {query_type or "unknown"}

        QUERY:
        {query}

        CONTEXT:
        {context}
        """

        messages = [
            {
                "role": "system",
                "content": self.generation_prompt
            },
            *self.history,
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        response = self._create_completion(messages)

        answer = response.choices[0].message.content

        self.history.append({"role": "user", "content": user_prompt})
        self.history.append({"role": "assistant", "content": answer})

        # Keep only last N turns
        self.history = self.history[-(self.max_turns * 2):]

        logger.info(f"History length: {len(self.history) // 2} turns")

        return answer

    def clear_history(self):
        """Reset the stored chat history for a new repo session."""
        self.history = []
        logger.info("Conversation history cleared.")
