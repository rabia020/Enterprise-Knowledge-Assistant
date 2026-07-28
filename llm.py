import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")

URL = "https://api.mistral.ai/v1/chat/completions"


def generate_answer(question, context):

    prompt = f"""
You are an Enterprise AI Assistant.

Use ONLY the information provided in the context below.

If the context contains partial information, summarize what is available.

Do NOT invent information.

If the context does not contain the answer, reply:

"I couldn't find this information in the company knowledge base."

-----------------------
Context
-----------------------
{context}

-----------------------
Question
-----------------------
{question}

Answer:
"""


    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]