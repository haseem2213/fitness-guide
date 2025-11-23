# app.py
import os
import streamlit as st
from datetime import datetime
from io import BytesIO

# Optional audio handling
import soundfile as sf

# Simple TTS
from gtts import gTTS

# Groq SDK
try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except Exception:
    GROQ_SDK_AVAILABLE = False

# ----------------------------
# Config / Prompting
# ----------------------------
SYSTEM_PROMPT = """
You are FitnessGPT — an expert personal fitness coach specialized in producing personalized workout plans.
Behaviors:
- Provide short, structured, actionable workout plans.
- Always include duration, sets/reps, warm-up, cooldown, and progressions.
- When appropriate, include calorie/nutrition guidance and safety notes.
- End each answer with exactly one clarifying question to gather missing data.
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

DEFAULT_MODEL = "llama-3.1-8b-instant"  # recommended working Groq model

# ----------------------------
# Utilities
# ----------------------------
def load_groq_client():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return None
    if not GROQ_SDK_AVAILABLE:
        return None
    return Groq(api_key=key)

def call_groq_api(client, user_text, model_name=DEFAULT_MODEL, temp=0.35, max_tokens=800):
    messages = [{"role":"system","content":SYSTEM_PROMPT}]
    # add few-shot examples
    for ex in FEW_SHOT_EXAMPLES:
        messages.append(ex)
    # append user
    messages.append({"role":"user","content":user_text})

    resp = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temp,
        max_tokens=max_tokens
    )

    # response content extraction (SDK may return nested objects)
    try:
        return resp.choices[0].message["content"]
    except Exception:
        try:
            return resp.choices[0].message.content
        except Exception:
            return str(resp)

def simple_tts_bytes(text):
    """Return MP3 bytes using gTTS (quick offline-ish TTS)."""
    tts = gTTS(text)
    bio = BytesIO()
    tts.write_to_fp(bio)
    bio.seek(0)
    return bio.read()

def transcribe_with_whisper_local(audio_bytes):
    """
    Optional: attempts local whisper transcription if whisper is installed in the environment.
    Whisper is large and often doesn't run in Spaces. Use only if you know Whisper is available.
    """
    try:
        import whisper
    except Exception:
        return None, "Whisper not installed in runtime."
    tmp_path = "/tmp/tmp_audio_for_transcription.wav"
    with open(tmp_path, "wb") as f:
        f.write(audio_bytes)
    model = whisper.load_model("small")
    result = model.transcribe(tmp_path)
    return result.get("text", ""), None

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="FitnessGPT — Personalized Plans", layout="centered")
st.title("FitnessGPT — Personalized Workout Planner")
st.markdown("Enter details (text) or upload a short voice clip (optional). The app uses a Groq model to generate a personalized workout plan.")

# Show Groq key state
if "GROQ_API_KEY" not in os.environ:
    st.warning("No `GROQ_API_KEY` environment variable found. To deploy on Hugging Face Spaces, add `GROQ_API_KEY` in your Space Secrets.")
else:
    st.success("Groq API key found ✅")

# Input method
input_method = st.radio("Input method", ["Text", "Upload audio (optional)"], index=0)

user_text = ""
if input_method == "Text":
    st.subheader("Enter user details")
    st.text("Example: 'Male, 28yo, 78kg, 178cm, 2200 kcal/day, goal: lose 6kg in 3 months, equipment: dumbbells'")
    user_text = st.text_area("Your details", height=180)
else:
    st.subheader("Upload a short audio clip (wav/mp3)")
    uploaded = st.file_uploader("Upload audio (optional)", type=["wav","mp3","m4a"])
    if uploaded is not None:
        audio_bytes = uploaded.read()
        st.audio(audio_bytes)
        # Try local whisper transcription (only if installed)
        st.info("Attempting local Whisper transcription (only if Whisper is available in this runtime).")
        transcription, err = transcribe_with_whisper_local(audio_bytes)
        if err:
            st.warning(err)
            # fallback to asking user to type
            user_text = st.text_area("Or type your details here", height=160)
        else:
            st.success("Transcription complete")
            user_text = st.text_area("Transcribed text (edit if needed)", value=transcription, height=160)
    else:
        user_text = st.text_area("Or type your details here", height=160)

# Options
col1, col2 = st.columns(2)
with col1:
    temperature = st.slider("Creativity (temperature)", min_value=0.0, max_value=1.0, value=0.35)
with col2:
    model_choice = st.selectbox("Groq model", [DEFAULT_MODEL, "llama-3.1-70b-versatile"], index=0)

# Generate
if st.button("Generate Plan"):
    if not user_text or user_text.strip() == "":
        st.error("Please provide user details (text or uploaded audio) before generating.")
    elif "GROQ_API_KEY" not in os.environ:
        st.error("Missing GROQ_API_KEY. Add it as a secret in your Space settings.")
    else:
        client = load_groq_client()
        if not client:
            st.error("Groq client not available in this runtime. Ensure 'groq' is installed and the GROQ_API_KEY secret is set.")
        else:
            with st.spinner("Generating personalized plan..."):
                try:
                    plan = call_groq_api(client, user_text, model_name=model_choice, temp=temperature)
                except Exception as e:
                    st.exception(e)
                    plan = None

            if plan:
                st.subheader("Generated Workout Plan")
                st.markdown(plan.replace("\n", "\n\n"))

                # Keep session history
                if "history" not in st.session_state:
                    st.session_state["history"] = []
                st.session_state["history"].append({"query": user_text, "plan": plan, "ts": datetime.utcnow().isoformat()})

                # TTS
                if st.checkbox("Play plan audio (gTTS)", value=True):
                    try:
                        audio_bytes = simple_tts_bytes(plan)
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.error(f"TTS failed: {e}")

# Show history
if st.session_state.get("history"):
    st.markdown("---")
    st.subheader("History (this session)")
    for item in reversed(st.session_state["history"][-10:]):
        st.markdown(f"**Query:** {item['query']}")
        st.markdown(f"**Plan:** {item['plan']}")
        st.caption(item["ts"])
