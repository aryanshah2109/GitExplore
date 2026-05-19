from groq import Groq
import os

from dotenv import load_dotenv
from backend.app.core.logger import get_logger
from backend.app.intelligence.prompt_templates import LLM_GENERATION_PROMPT
from backend.app.core.config_loader import config

logger = get_logger()

load_dotenv()

class LLMClient:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.generation_prompt = LLM_GENERATION_PROMPT
        self.max_turns = config.generation.conversation_history_turns
        self.history = []
        self.num_predict = config.generation.num_predict
        self.temperature = config.generation.temperature

    def generate_answer(self, query: str, context: str) -> str:

        logger.info("Generating answer for given query.")

        user_prompt = f"""
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

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.num_predict
        )

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