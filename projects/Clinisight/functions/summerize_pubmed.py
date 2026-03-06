import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def summarize_text(text: str) -> str:
    prompt = f"Summarize the following medical abstract:\n\n{text}"

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a medical research summarizer."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()