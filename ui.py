import os
import streamlit as st
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()
st.set_page_config(page_title="Bhasha Bot", page_icon="🗣️", layout="centered")

st.markdown("""
<style>
.stApp {background: radial-gradient(circle at top, #1b1040 0%, #0b0b1a 70%); color: #fff;}
.title {font-size: 3rem; font-weight: 800; text-align: center;
  background: linear-gradient(90deg, #ff9933, #ffffff, #138808);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.sub {text-align: center; color: #b8b8d8; margin-bottom: 1.5rem;}
.chips {text-align: center; margin-bottom: 1rem;}
.chips span {display: inline-block; margin: 3px; padding: 4px 12px; border-radius: 999px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); font-size: 0.85rem;}
[data-testid="stChatMessage"] {background: rgba(255,255,255,0.05); border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);}
</style>
<div class="title">🗣️ Bhasha Bot</div>
<div class="sub">Write in any Indian language. I'll reply in yours.</div>
<div class="chips"><span>हिन्दी</span><span>தமிழ்</span><span>বাংলা</span><span>తెలుగు</span>
<span>मराठी</span><span>ગુજરાતી</span><span>ಕನ್ನಡ</span><span>മലയാളം</span><span>English</span></div>
""", unsafe_allow_html=True)

SYSTEM = {"role": "system", "content": "You are a friendly assistant. Always reply in the same language and script the user writes in (Hindi, Tamil, Bengali, English, etc.). Keep answers clear and warm."}


@st.cache_resource
def get_client():
    return SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Try these ✨")
    for label, text in [
        ("🇮🇳 Hindi", "नमस्ते! भारत के बारे में एक मज़ेदार बात बताओ।"),
        ("🌴 Tamil", "வணக்கம்! சென்னையில் பார்க்க வேண்டிய இடங்கள் என்ன?"),
        ("🐅 Bengali", "আমাকে একটি ছোট গল্প বলো।"),
        ("🌐 English", "Explain AI to a 10-year-old."),
    ]:
        if st.button(label, use_container_width=True):
            st.session_state.queued = text
    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("Powered by Sarvam AI · sarvam-105b-conversations")

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🤖"):
        st.markdown(m["content"])

prompt = st.chat_input("Type in any Indian language...")
if "queued" in st.session_state:
    prompt = st.session_state.pop("queued")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                reply = get_client().chat.completions(
                    model="sarvam-105b-conversations",
                    messages=[SYSTEM] + st.session_state.messages,
                ).choices[0].message.content
            except Exception as e:
                reply = f"⚠️ Something went wrong: {type(e).__name__}"
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})