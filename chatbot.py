import os
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()
client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])

messages = [{"role": "system", "content": "You are a helpful assistant. Always reply in the same language the user writes in (Hindi, Tamil, Bengali, English, etc.)."}]

print("Sarvam multilingual chatbot (type 'quit' to exit)")
while True:
    user = input("You: ").strip()
    if user.lower() in ("quit", "exit"):
        break
    if not user:
        continue
    messages.append({"role": "user", "content": user})
    reply = client.chat.completions(
        model="sarvam-105b-conversations", messages=messages
    ).choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    print("Bot:", reply)