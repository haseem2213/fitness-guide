# FitnessGPT — Streamlit frontend for Groq-powered personalized workout plans

## Overview
This Streamlit app collects user details (text or short audio), sends them to a Groq chat model (Llama-3.1-8B instant recommended), and returns a structured personalized workout plan. The app also offers simple text-to-speech playback.

## Files
- `app.py` - Streamlit application
- `requirements.txt` - Python dependencies

## Deploy to Hugging Face Spaces
1. Create a new Space (https://huggingface.co/spaces)  
   - Choose **Streamlit** as the SDK.  
   - Make it Public or Private.

2. Add repository files:
   - `app.py`, `requirements.txt`, `README.md`

3. Add Secrets (Space Settings → Secrets)
   - `GROQ_API_KEY` = your Groq API key

4. Push files:
git clone https://huggingface.co/spaces/
<your-username>/<space-name>
cp app.py requirements.txt README.md <space-name>/
cd <space-name>
git add .
git commit -m "Initial commit"
git push

5. The Space will build and then be available online.  
Check build logs in the Space UI if anything fails.

## Tips & Upgrades
- For better STT, use a hosted Whisper API or a cloud STT (OpenAI/Google) instead of local Whisper in the Space.  
- For higher-quality TTS, add ElevenLabs or Google TTS and store the API key in your Space Secrets.  
- To persist user plans long-term, integrate a small DB (Supabase or simple SQLite) and secure authentication.
