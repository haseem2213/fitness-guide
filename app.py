import os
import streamlit as st
from io import BytesIO

# Try to import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# For audio
try:
    import whisper
    from gtts import gTTS
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# =====================
# Settings
DEFAULT_MODEL = "llama-3.1-8b-instant"
SYSTEM_PROMPT = """
You are FitnessGPT — an expert personal fitness coach. Generate short, actionable, personalized workout plans
based on the user's details (weight, height, goals, equipment). Include sets/reps, warmup, cooldown, and
progressions. Be friendly and motivational.
"""

# =====================
# Load Groq client
def load_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")  # secure via secrets
    if not api_key or not GROQ_AVAILABLE:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        return None

# =====================
# Generate workout plan
def generate_workout_plan(client, user_text, model_name=DEFAULT_MODEL):
    if client:
        try:
            messages = [
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":user_text}
            ]
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.35,
                max_tokens=800
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error generating plan: {e}"
    else:
        # Fallback demo plan
        return f"**Demo Workout Plan for:** {user_text}\n\n" \
               "Day 1: Push-ups, Squats, Plank, Dumbbell curls\n" \
               "Day 2: Lunges, Shoulder presses, Crunches, Stretching\n" \
               "\n*Increase reps or weight as you get stronger!*"

# =====================
# Convert text to speech
def text_to_speech(text):
    if not AUDIO_AVAILABLE:
        return None
    tts = gTTS(text=text, lang="en")
    audio_bytes = BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes

# =====================
# Streamlit UI
st.set_page_config(page_title="FitnessGPT", page_icon="🏋️", layout="centered")

st.title("🏋️ FitnessGPT — Personalized Workout Planner")
st.markdown(
    "Enter your fitness details below to generate a **personalized workout plan**.\n\n"
    "You can either type your details or upload a short voice clip."
)

st.markdown("---")

# 1. User input
input_method = st.radio("Input method:", ["Text", "Voice"])

user_text = ""
if input_method == "Text":
    user_text = st.text_area(
        "Your details (weight, height, goals, equipment, etc.)",
        height=150,
        placeholder="Example: 'Male, 28yo, 78kg, 178cm, 2200 kcal/day, goal: lose 6kg in 3 months, equipment: dumbbells'"
    )
else:
    uploaded_file = st.file_uploader("Upload audio file (wav/mp3)", type=["wav", "mp3"])
    if uploaded_file and AUDIO_AVAILABLE:
        st.audio(uploaded_file, format='audio/wav')
        st.info("Transcribing your audio...")
        model = whisper.load_model("base")
        audio = uploaded_file.read()
        transcription = model.transcribe(BytesIO(audio))
        user_text = transcription['text']
        st.success(f"Transcribed text: {user_text}")
    elif uploaded_file:
        st.warning("Audio features not available. Install whisper and gTTS packages.")

st.markdown("---")

# 2. Generate plan
client = load_groq_client()
if not client and GROQ_AVAILABLE:
    st.warning("Cannot initialize Groq client. Using demo plan.")

if st.button("Generate Workout Plan"):
    if not user_text.strip():
        st.error("Please provide your fitness details first!")
    else:
        with st.spinner("Generating your personalized workout plan..."):
            plan = generate_workout_plan(client, user_text)
        st.subheader("💪 Your Workout Plan")
        st.markdown(plan.replace("\n","\n\n"))

        # 3. Text-to-speech
        if AUDIO_AVAILABLE:
            audio_bytes = text_to_speech(plan)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")


