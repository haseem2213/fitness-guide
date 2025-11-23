# app.py
import os
import streamlit as st

# Try to import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# ----------------------------
# Config
# ----------------------------
DEFAULT_MODEL = "llama-3.1-8b-instant"
SYSTEM_PROMPT = """
You are FitnessGPT — an expert personal fitness coach. Generate short, actionable, personalized workout plans
based on the user's details (weight, height, goals, equipment). Include sets/reps, warmup, cooldown, and
progressions. Be friendly and motivational.
"""

# ----------------------------
# Utilities
# ----------------------------
def load_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not GROQ_AVAILABLE:
        return None
    return Groq(api_key=api_key)

def generate_workout_plan(client, user_text, model_name=DEFAULT_MODEL):
    messages = [{"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":user_text}]
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.35,
            max_tokens=800
        )
        return resp.choices[0].message["content"]
    except Exception as e:
        return f"Error generating plan: {e}"

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="FitnessGPT", page_icon="🏋️", layout="centered")
st.title("FitnessGPT — Personalized Workout Planner")
st.markdown("Enter your fitness details below to generate a personalized workout plan.")

# Check API key
if "GROQ_API_KEY" not in os.environ:
    st.error("No GROQ_API_KEY found! Add it in Space Secrets and restart the Space.")
    st.stop()

if not GROQ_AVAILABLE:
    st.error("Groq SDK not installed. Add `groq` to your requirements.txt.")
    st.stop()

client = load_groq_client()
if not client:
    st.error("Cannot initialize Groq client. Check your API key and SDK.")
    st.stop()

# User input
user_text = st.text_area(
    "Your details (weight, height, goals, equipment, etc.)",
    height=150,
    placeholder="Example: 'Male, 28yo, 78kg, 178cm, 2200 kcal/day, goal: lose 6kg in 3 months, equipment: dumbbells'"
)

if st.button("Generate Workout Plan"):
    if not user_text.strip():
        st.error("Please enter your fitness details first!")
    else:
        with st.spinner("Generating your personalized workout plan..."):
            plan = generate_workout_plan(client, user_text)
        st.subheader("Your Workout Plan")
        st.markdown(plan.replace("\n","\n\n"))

