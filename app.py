# app.py
import os
import streamlit as st
from datetime import datetime
from io import BytesIO

# Optional TTS
from gtts import gTTS

# Groq SDK
try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    GROQ_SDK_AVAILABLE = False

# ----------------------------
# Config
# ----------------------------
SYSTEM_PROMPT = """
You are FitnessGPT — an expert personal fitness coach specialized in producing personalized workout plans.
Behaviors:
- Provide short, structured, actionable workout plans.
- Include sets/reps, duration, warmup, cooldown, and progressions.
- End each answer with one clarifying question.
- Be friendly, motivational, and clear.
"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": "Create a 2-day fat-loss home workout plan"
    },
    {
        "role": "assistant",
        "content": "- Day 1 (Full body circuit): 3 rounds of 10 squats, 10 incline push-ups, 12 walking lunges per leg, 30s plank. Warmup 5 min. Cooldown 5 min.\n- Day 2 (Cardio + core): 20-min steady state cardio + core circuit.\nClarifying question: What is your current weight and how many days per week can you train?"
    }
]

DEFAULT_MODEL = "llama-3.1-8b-instant"

# ----------------------------
# Utilities
# ----------------------------
def load_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    if not GROQ_SDK_AVAILABLE:
        return None
    return Groq(api_key=api_key)

def call_groq_api(client, user_text, model_name=DEFAULT_MODEL, temp=0.35, max_tokens=800):
    messages = [{"role":"system","content":SYSTEM_PROMPT}]
    for ex in FEW_SHOT_EXAMPLES:
        messages.append(ex)
    messages.append({"role":"user","content":user_text})

    resp = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temp,
        max_tokens=max_tokens
    )

    try:
        return resp.choices[0].message["content"]
    except Exception:
        return str(resp)

def simple_tts_bytes(text):
    tts = gTTS(text)
    bio = BytesIO()
    tts.write_to_fp(bio)
    bio.seek(0)
    return bio.read()

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="FitnessGPT", layout="centered")
st.title("FitnessGPT — Personalized Workout Planner")
st.markdown("Enter your fitness details (text) or upload a short audio clip (optional).")

# Check API key
if "GROQ_API_KEY" not in os.environ:
    st.error("No GROQ_API_KEY environment variable found. Add your Groq API key in Space Secrets.")
    st.stop()

client = load_groq_client()
if not client:
    st.error("Groq client not available in this runtime. Make sure 'groq' is installed.")
    st.stop()

# Input
input_method = st.radio("Input method", ["Text", "Upload audio"], index=0)
user_text = ""

if input_method == "Text":
    st.subheader("Enter your details")
    st.text("Example: 'Male, 28yo, 78kg, 178cm, 2200 kcal/day, goal: lose 6kg in 3 months, equipment: dumbbells'")
    user_text = st.text_area("Your details", height=180)
else:
    st.subheader("Upload audio (wav/mp3)")
    uploaded = st.file_uploader("Upload audio", type=["wav","mp3","m4a"])
    if uploaded is not None:
        audio_bytes = uploaded.read()
        st.audio(audio_bytes)
        st.info("Audio transcription is not available in this version. Please type your details below if needed.")
        user_text = st.text_area("Or type your details here", height=160)
    else:
        user_text = st.text_area("Or type your details here", height=160)

# Options
col1, col2 = st.columns(2)
with col1:
    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.35)
with col2:
    model_choice = st.selectbox("Groq model", [DEFAULT_MODEL, "llama-3.1-70b-versatile"], index=0)

# Generate plan
if st.button("Generate Plan"):
    if not user_text.strip():
        st.error("Please provide details before generating.")
    else:
        with st.spinner("Generating workout plan..."):
            plan = call_groq_api(client, user_text, model_name=model_choice, temp=temperature)
        if plan:
            st.subheader("Generated Workout Plan")
            st.markdown(plan.replace("\n","\n\n"))

            if st.checkbox("Play plan audio (gTTS)", value=True):
                audio_bytes = simple_tts_bytes(plan)
                st.audio(audio_bytes, format="audio/mp3")

# Session history
if "history" not in st.session_state:
    st.session_state["history"] = []

if st.session_state["history"]:
    st.markdown("---")
    st.subheader("History (this session)")
    for item in reversed(st.session_state["history"][-10:]):
        st.markdown(f"**Query:** {item['query']}")
        st.markdown(f"**Plan:** {item['plan']}")
        st.caption(item["ts"])
