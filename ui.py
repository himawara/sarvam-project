import base64
import hashlib
import os
import re
import tempfile

import streamlit as st
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()
st.set_page_config(page_title="Bhasha Bot", page_icon="🗣️", layout="centered")

st.markdown("""
<style>
.stApp {background: radial-gradient(circle at top, #1b1040 0%, #0b0b1a 70%);}
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
<div class="sub">Speak or type in any Indian language. Hear the answer in the language you choose.</div>
<div class="chips"><span>हिन्दी</span><span>தமிழ்</span><span>বাংলা</span><span>తెలుగు</span>
<span>मराठी</span><span>ગુજરાતી</span><span>ಕನ್ನಡ</span><span>മലയാളം</span><span>English</span></div>
""", unsafe_allow_html=True)

PERSONAS = {
    "😊 Friendly Assistant": "You are a friendly, helpful assistant.",
    "👩‍🏫 Teacher": "You are a patient teacher. Explain step by step in simple words and give one easy example.",
    "📖 Storyteller": "You are a storyteller. Tell short, vivid stories with Indian cultural flavour.",
    "🧳 Travel Guide": "You are a knowledgeable India travel guide. Give practical, specific tips.",
    "💪 Health Info": "You give general wellness information only. Always end with a short note that this is not medical advice and they should consult a doctor.",
}

REPLY_LANGS = {
    "Auto (same as I write)": None,
    "English": "en-IN",
    "हिन्दी Hindi": "hi-IN",
    "தமிழ் Tamil": "ta-IN",
    "বাংলা Bengali": "bn-IN",
    "తెలుగు Telugu": "te-IN",
    "मराठी Marathi": "mr-IN",
    "ગુજરાતી Gujarati": "gu-IN",
    "ಕನ್ನಡ Kannada": "kn-IN",
    "മലയാളം Malayalam": "ml-IN",
    "ਪੰਜਾਬੀ Punjabi": "pa-IN",
    "ଓଡ଼ିଆ Odia": "od-IN",
}

# Unicode script ranges -> Sarvam language codes
SCRIPTS = [
    (0x0900, 0x097F, "hi-IN"), (0x0980, 0x09FF, "bn-IN"), (0x0A00, 0x0A7F, "pa-IN"),
    (0x0A80, 0x0AFF, "gu-IN"), (0x0B00, 0x0B7F, "od-IN"), (0x0B80, 0x0BFF, "ta-IN"),
    (0x0C00, 0x0C7F, "te-IN"), (0x0C80, 0x0CFF, "kn-IN"), (0x0D00, 0x0D7F, "ml-IN"),
]


def detect_lang(text):
    counts = {}
    for ch in text:
        o = ord(ch)
        for lo, hi, code in SCRIPTS:
            if lo <= o <= hi:
                counts[code] = counts.get(code, 0) + 1
    return max(counts, key=counts.get) if counts else "en-IN"


def friendly(e):
    code = getattr(e, "status_code", None)
    if code == 429:
        return "Rate limit reached. Wait a few seconds and try again."
    if code in (401, 403):
        return "API key problem. Check SARVAM_API_KEY in your .env or Secrets."
    return f"{type(e).__name__}: {e}"


@st.cache_resource
def get_client():
    return SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])


def speak(text, lang=None, pace=1.0):
    clean = re.sub(r"[*#_`>]", "", text)[:2500]
    resp = get_client().text_to_speech.convert(
        text=clean,
        language_code=lang or detect_lang(clean),
        model="bulbul:v3",
        pace=pace,
    )
    return base64.b64decode("".join(resp.audios))


def transcribe(audio_bytes):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        path = f.name
    try:
        with open(path, "rb") as fh:
            resp = get_client().speech_to_text.transcribe(
                file=fh, model="saaras:v3", mode="transcribe"
            )
        return (resp.transcript or "").strip()
    finally:
        os.remove(path)


def build_system(persona, target):
    if target:
        lang_rule = "Reply in clear, simple English."
    else:
        lang_rule = "Always reply in the same language and script the user writes in."
    return f"{PERSONAS[persona]} {lang_rule} Keep answers warm, clear and under 150 words."


def get_reply(persona, target):
    msgs = [{"role": "system", "content": build_system(persona, target)}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]
    reply = get_client().chat.completions(
        model="sarvam-105b-conversations", messages=msgs
    ).choices[0].message.content
    if target and target != "en-IN":
        reply = get_client().text.translate(
            input=reply[:2000],
            source_language_code="en-IN",
            target_language_code=target,
            model="sarvam-translate:v1",
        ).translated_text
    return reply


if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio" not in st.session_state:
    st.session_state.audio = {}

with st.sidebar:
    st.header("🎤 Speak")
    voice = st.audio_input("Record (up to 30 sec)")
    st.divider()
    st.header("⚙️ Settings")
    persona = st.selectbox("Persona", list(PERSONAS.keys()))
    reply_label = st.selectbox("Reply language", list(REPLY_LANGS.keys()))
    target = REPLY_LANGS[reply_label]
    pace = st.slider("Voice speed", 0.5, 2.0, 1.0, 0.1)
    st.divider()
    st.header("Try these ✨")
    for label, text in [
        ("🪔 Hindi", "नमस्ते! भारत के बारे में एक मज़ेदार बात बताओ।"),
        ("🌴 Tamil", "வணக்கம்! சென்னையில் பார்க்க வேண்டிய இடங்கள் என்ன?"),
        ("🐅 Bengali", "আমাকে একটি ছোট গল্প বলো।"),
        ("🌐 English", "Explain AI to a 10-year-old."),
    ]:
        if st.button(label, use_container_width=True):
            st.session_state.queued = text
    st.divider()
    if st.session_state.messages:
        transcript = "\n\n".join(
            f"{'You' if m['role'] == 'user' else 'Bhasha Bot'}: {m['content']}"
            for m in st.session_state.messages
        )
        st.download_button("⬇️ Download chat", transcript, file_name="bhasha_chat.txt",
                           use_container_width=True)
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.audio = {}
        st.rerun()
    st.caption("Sarvam AI · chat: sarvam-105b-conversations · voice: bulbul:v3 · ears: saaras:v3 · translate: sarvam-translate")

autoplay_idx = st.session_state.pop("autoplay_idx", None)

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🤖"):
        st.markdown(m["content"])
        if m["role"] == "assistant" and not m["content"].startswith("⚠️"):
            if i in st.session_state.audio:
                st.audio(st.session_state.audio[i], format="audio/wav", autoplay=(i == autoplay_idx))
            elif st.button("🔊 Listen", key=f"tts_{i}"):
                with st.spinner("Generating voice..."):
                    try:
                        st.session_state.audio[i] = speak(m["content"], m.get("lang"), pace)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Voice failed: {friendly(e)}")

prompt = st.chat_input("Type in any Indian language...")
from_voice = False

if "queued" in st.session_state:
    prompt = st.session_state.pop("queued")

if voice is not None:
    data = voice.getvalue()
    digest = hashlib.md5(data).hexdigest()
    if st.session_state.get("last_voice") != digest:
        st.session_state.last_voice = digest
        with st.spinner("Listening..."):
            try:
                heard = transcribe(data)
            except Exception as e:
                heard = ""
                st.error(f"Speech recognition failed: {friendly(e)}")
        if heard:
            prompt, from_voice = heard, True
        else:
            st.warning("I couldn't hear anything. Please try recording again.")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                reply = get_reply(persona, target)
                ok = True
            except Exception as e:
                reply = f"⚠️ {friendly(e)}"
                ok = False
    st.session_state.messages.append({"role": "assistant", "content": reply, "lang": target})
    if from_voice and ok:
        try:
            idx = len(st.session_state.messages) - 1
            st.session_state.audio[idx] = speak(reply, target, pace)
            st.session_state.autoplay_idx = idx
        except Exception as e:
            st.error(f"Voice failed: {friendly(e)}")
    st.rerun()