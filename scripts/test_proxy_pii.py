import httpx
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def test_proxy_pii():
    url = "http://localhost:8000/proxy/v1/chat/completions"
    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "My PAN card is ABCDE1234F. What is it?"}
        ]
    }
    
    print(f"--- Proxy PII Test ---")
    print(f"Sending request to: {url}")
    
    start_time = time.time()
    try:
        with httpx.Client(timeout=70.0) as client:
            response = client.post(url, json=payload)
            latency = (time.time() - start_time) * 1000
            print(f"Status Code: {response.status_code}")
            print(f"Latency: {latency:.2f}ms")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Assistant: {data['choices'][0]['message']['content']}")
                print(f"Request ID: {data.get('proxy_request_id')}")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_proxy_pii()
