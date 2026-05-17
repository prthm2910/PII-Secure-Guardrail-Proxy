import os
import httpx
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def test_groq_direct():
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    
    print(f"--- Groq Direct Connectivity Test ---")
    print(f"Model: {model}")
    
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Groq is Active' and nothing else.",
                }
            ],
            model=model,
            max_tokens=10
        )
        print(f"Status: SUCCESS")
        print(f"Response: {chat_completion.choices[0].message.content}")
    except Exception as e:
        print(f"Exception during Groq request: {e}")

if __name__ == "__main__":
    test_groq_direct()
