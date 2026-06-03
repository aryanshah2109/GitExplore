from groq import Groq
import os
import json
import time
import re
from typing import Any


from backend.app.core.logger import get_logger
from backend.app.intelligence.prompt_templates import LLM_JUDGE_PROMPT
from backend.app.core.config_loader import config

logger = get_logger()

class LLMJudgeClient:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.generation_prompt = LLM_JUDGE_PROMPT
        self.model_name = config.judge.model_name
        self.num_predict = config.judge.num_predict
        self.temperature = config.judge.temperature
        self.max_retries = getattr(config.judge, "max_retries", 3)
        self.retry_delay_seconds = getattr(config.judge, "retry_delay_seconds", 1.5)

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
                    f"Groq rate limit hit on judge attempt {attempt}/{self.max_retries}; "
                    f"retrying in {sleep_for:.1f}s"
                )
                time.sleep(sleep_for)

        raise RuntimeError(f"Failed to judge answer after {self.max_retries} attempts: {last_error}")

    def _parse_json_output(self, raw_output: str) -> dict:
        cleaned = raw_output.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

    def judge_answer(self, query: str, context: str, answer: str, query_type: str | None = None) -> dict:

        logger.info("Judging answer for given query, context and generated answer.")

        user_prompt = f"""
        QUERY TYPE:
        {query_type or "unknown"}

        QUERY:
        {query}

        CONTEXT:
        {context}

        ANSWER:
        {answer}
        """

        messages = [
            {
                "role": "system",
                "content": self.generation_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        response = self._create_completion(messages)

        raw_output = response.choices[0].message.content.strip()

        try:
            return self._parse_json_output(raw_output)

        except Exception:
            logger.error(
                f"Failed to parse judge output: {raw_output}"
            )

            return {
                "faithfulness": 0,
                "retrieval_relevance": 0,
                "citation_accuracy": 0,
                "query_type_fit": 0,
                "reasoning": raw_output
            }
