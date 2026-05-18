from groq import Groq
import os

from scripts.run_query import get_context

from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_answer(query: str, context: str):

    system_prompt = """
    You are an expert codebase assistant.

    Answer ONLY using the provided code context below.
    Always cite sources inline as [file:start_line:symbol_name].
    If the answer is not found in the context, say so — do not guess.

    When explaining:
    - Trace the logic step by step
    - Mention exact function names and file paths
    - Show relevant code snippets if helpful
    """

    user_prompt = f"""
    QUERY:
    {query}

    CONTEXT:
    {context}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.2,
        max_tokens=1600
    )

    return response.choices[0].message.content

query = "How should i run the code in the repository"
repo_id = "265dc296-f7f0-4ec9-906d-d2a30a27189e"

context = get_context(query, repo_id)

answer = generate_answer(query, context)

print(answer)

print("\n"*4)
print(context)