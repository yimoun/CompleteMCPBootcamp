import os 
from dotenv import load_dotenv
from groq import Groq 

load_dotenv()

client = Groq(api_key = os.getenv("GROQ_API_KEY"))

def get_diagnosis(symptoms: list[str]) -> str:
    prompt = f"Patient has symptoms: {', '.join(symptoms)}. Suggest possible medical diagnosis.suggest me a possible cure fro the same"

    response = client.chat.completions.create(
        model = "llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful medical assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
