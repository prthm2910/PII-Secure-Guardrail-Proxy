import httpx
import json
import time

def test_proxy_bypass():
    url = "http://localhost:8000/proxy/v1/chat/completions"
    headers = {"X-PII-Skip": "true"}
    payload = {
        "model": "meta/llama-3.2-1b-instruct",
        "messages": [
            {"role": "user", "content": "Say 'Bypass Active'"}
        ]
    }
    
    print(f"--- Proxy Bypass Test ---")
    start_time = time.time()
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            latency = (time.time() - start_time) * 1000
            print(f"Status Code: {response.status_code}")
            print(f"Latency: {latency:.2f}ms")
            
            if response.status_code == 200:
                print(f"Assistant: {response.json()['choices'][0]['message']['content']}")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_proxy_bypass()
