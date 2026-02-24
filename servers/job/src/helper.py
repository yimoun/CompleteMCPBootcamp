import fitz # PyMuPDF
import os 
import time
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to .env or export it.")

client = Groq(api_key=GROQ_API_KEY)


def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file.
    
    Args:
        uploaded_file (str): The path to the PDF file.
        
    Returns:
        str: The extracted text.
    """
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        return "".join(page.get_text() for page in doc)



def ask_groq(prompt, max_tokens=500, retries=3, backoff=0.6):
    """
    Sends a prompt to the Groq API and returns the response.
    
    Args:
        prompt (str): The prompt to send to the Groq API.
        model (str): The model to use for the request.
        temperature (float): The temperature for the response.
        
    Returns:
        str: The response from the Groq API.
    """
    

    last_error = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            last_error = exc
            time.sleep(backoff * (2 ** attempt))
    raise last_error


