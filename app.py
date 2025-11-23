import streamlit as st

# Try to import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

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
    api_key = "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"  # Hardcoded for testing
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
        # Real API call
        try:
            messages = [{"role":"system","content":SYSTEM_PROMPT},
                        {"role":"user","content":user_text}]
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.35,
                max_tokens=800
            )
            return resp.choices[0].message["content"]
        except Exception as e:
            return f"Error generating plan: {e}"
    else:
        # Mock fallback
        return f"**Demo Workout Plan for:** {user_text}\n\n" \
               "Day 1: Push-ups, Squats, Plank, Dumbbell curls\n" \
               "Day 2: Lunges, Shoulder presses, Crunches, Stretching\n" \
               "\n*Increase reps or weight as you get stronger!*"

# =====================
# Streamlit UI
st.set_page_config(page_title="FitnessGPT", page_icon="🏋️", layout="centered")
st.title("FitnessGPT — Personalized Workout Planner")
st.markdown("Enter your fitness details below to generate a personalized workout plan.")

if not GROQ_AVAILABLE:
    st.warning("Groq SDK not installed. The app will use a mock demo plan.")

client = load_groq_client()
if not client and GROQ_AVAILABLE:
    st.warning("Cannot initialize Groq client. The app will use a demo plan.")

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

