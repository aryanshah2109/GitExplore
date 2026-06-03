from groq import Groq
import os
import time
from typing import Any

from backend.app.core.logger import get_logger
from backend.app.intelligence.prompt_templates import LLM_GENERATION_PROMPT
from backend.app.core.config_loader import config

logger = get_logger()

class LLMGenerationClient:
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
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.num_predict
                )
            except Exception as e:
                last_error = e
                error_text = str(e).lower()
                is_rate_limit = "429" in error_text or "rate limit" in error_text

                if attempt >= self.max_retries or not is_rate_limit:
                    break

                sleep_for = self.retry_delay_seconds * attempt
                logger.warning(
                    f"Groq rate limit hit on generation attempt {attempt}/{self.max_retries}; "
                    f"retrying in {sleep_for:.1f}s"
                )
                time.sleep(sleep_for)

        raise RuntimeError(f"Failed to generate answer after {self.max_retries} attempts: {last_error}")

    def generate_answer(self, query: str, context: str, query_type: str | None = None) -> str:

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
        """Call this when user starts a new repo session."""
        self.history = []
        logger.info("Conversation history cleared.")
