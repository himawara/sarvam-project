import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("SARVAM_API_KEY")

print("Checking API key...")
if not api_key:
    print("❌ ERROR: SARVAM_API_KEY is missing or empty in .env file!")
else:
    print("✅ API Key found! Calling Sarvam AI...")

    url = "https://api.sarvam.ai/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": api_key
    }

    payload = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "user", "content": "Hello! Reply with one short sentence."}
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        print("\n--- Response from Sarvam ---")
        print(data["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"❌ API Error: {e}")
        if 'response' in locals() and response.text:
            print(f"Details: {response.text}")