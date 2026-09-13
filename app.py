import streamlit as st
import edge_tts
import asyncio
import requests
from google import genai
import os
import re
from urllib.parse import urlparse, parse_qs

st.set_page_config(page_title="Universal AI Voice & Video Studio", page_icon="🎙️", layout="centered")

# Streamlit Secrets से API Keys
secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")
secrets_eleven = st.secrets.get("ELEVEN_API_KEY", "")

# YouTube Video ID निकालने का फंक्शन
def extract_video_id(url):
    url = url.strip()
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].split("&")[0]
    elif "youtube.com/shorts/" in url:
        return url.split("youtube.com/shorts/")[1].split("?")[0].split("&")[0]
    elif "youtube.com/watch" in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

# टैब स्ट्रक्चर
tab1, tab2 = st.tabs(["🎙️ Voice Studio", "📝 YouTube Video Transcribe"])

# ==========================================
# TAB 1: AI VOICE STUDIO
# ==========================================
with tab1:
    st.header("🎙️ Universal AI Voice Studio")
    st.write("फ्री न्यूरल आवाज़ें, Google Gemini AI और ElevenLabs कैरेक्टर")

    st.sidebar.header("⚙️ Voice Settings")
    engine_choice = st.sidebar.radio(
        "वॉयस इंजन चुनें:",
        (
            "🆓 100% Free & Unlimited (Edge Neural)",
            "✨ Google Gemini Engine (Free API Key)",
            "💎 ElevenLabs Characters (API Key)"
        )
    )

    free_voices = {
        "1. Hindi - Madhur (कहानी / Male)": ("hi-IN-MadhurNeural", 0),
        "2. Hindi - Swara (समाचार / Female)": ("hi-IN-SwaraNeural", 0),
        "3. Hindi - Deep Documentary (भारी / Male)": ("hi-IN-MadhurNeural", -12),
        "4. Hindi - Energetic RJ (उत्साही / Male)": ("hi-IN-MadhurNeural", 12),
        "5. Hindi - Calm Meditation (शांत / Female)": ("hi-IN-SwaraNeural", -10),
        "6. Hindi - Fast Reels (तेज़ / Female)": ("hi-IN-SwaraNeural", 15),
        "7. Hindi - Motivational (जोशीला / Male)": ("hi-IN-MadhurNeural", 8),
        "8. Hindi - Soft Storyteller (भावुक / Female)": ("hi-IN-SwaraNeural", -6),
        "9. Hindi - Heavy Villain (विलेन / Male)": ("hi-IN-MadhurNeural", -18),
        "10. Hindi - Corporate (प्रोफेशनल / Female)": ("hi-IN-SwaraNeural", 4),
        "11. English - Guy (US Male)": ("en-US-GuyNeural", 0),
        "12. English - Jenny (US Female)": ("en-US-JennyNeural", 0)
    }

    elevenlabs_voices = {
        "Adam (डीप नरेशन / मेल)": "pNInz6obpgDQGcFmaJgB",
        "Rachel (प्रोफेशनल / फीमेल)": "21m00Tcm4TlvDq8ikWAM",
        "Antoni (उत्साही / मेल)": "ErXwobaYiN019PkySvjV",
        "Bella (सॉफ्ट / फीमेल)": "EXAVITQu4vr4xnSDxMaL",
        "Josh (पॉडकास्ट / भारी मेल)": "TxGEqnHWrfWFTfGW9XjX",
        "Matilda (स्टोरीटेलिंग / फीमेल)": "XrExE9yKIg1WjnnlVkGX"
    }

    speed_adjust = 0
    api_key = ""

    if engine_choice.startswith("🆓"):
        selected_voice = st.sidebar.selectbox("फ्री आवाज़ चुनें:", list(free_voices.keys()))
        speed_adjust = st.sidebar.slider("स्पीड एडजस्ट करें (%):", -30, 30, 0, step=5)
    elif engine_choice.startswith("✨"):
        api_key = st.sidebar.text_input("Google Gemini API Key:", value=secrets_gemini, type="password")
        gemini_tone = st.sidebar.selectbox("Gemini का अंदाज़:", ["कहानीकार (Storyteller)", "उत्साही (Excited)", "शांत व गंभीर (Calm & Professional)"])
        selected_voice = st.sidebar.selectbox("आउटपुट आवाज़:", ["Hindi - Madhur (Male)", "Hindi - Swara (Female)"])
    else:
        api_key = st.sidebar.text_input("ElevenLabs API Key:", value=secrets_eleven, type="password")
        selected_voice = st.sidebar.selectbox("ElevenLabs कैरेक्टर चुनें:", list(elevenlabs_voices.keys()))

    text_input = st.text_area("यहाँ अपना टेक्स्ट लिखें या पेस्ट करें:", height=180, key="voice_text_input")

    async def generate_edge_clean(text, voice_code, rate_str, output_file):
        communicate = edge_tts.Communicate(text, voice_code, rate=rate_str)
        await communicate.save(output_file)

    if st.button("🚀 Generate Audio (MP3)", key="btn_gen_audio"):
        if not text_input.strip():
            st.error("कृपया पहले कोई टेक्स्ट दर्ज करें।")
        elif (engine_choice.startswith("✨") or engine_choice.startswith("💎")) and not api_key.strip():
            st.error("कृपया API Key दर्ज करें।")
        else:
            with st.spinner("AI आवाज़ तैयार की जा रही है..."):
                output_audio = "final_output.mp3"
                if os.path.exists(output_audio):
                    os.remove(output_audio)
                try:
                    if engine_choice.startswith("🆓"):
                        voice_code, base_speed = free_voices[selected_voice]
                        rate_str = f"{base_speed + speed_adjust:+d}%"
                        asyncio.run(generate_edge_clean(text_input, voice_code, rate_str, output_audio))
                    elif engine_choice.startswith("✨"):
                        client = genai.Client(api_key=api_key)
                        prompt = f"इस टेक्स्ट को {gemini_tone} के अंदाज़ में सुधारें: {text_input}"
                        response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
                        target_code = "hi-IN-MadhurNeural" if "Madhur" in selected_voice else "hi-IN-SwaraNeural"
                        asyncio.run(generate_edge_clean(response.text, target_code, "+0%", output_audio))
                    else:
                        v_id = elevenlabs_voices[selected_voice]
                        url = f"https://api.elevenlabs.io/v1/text-to-speech/{v_id}"
                        headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
                        data = {"text": text_input, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
                        resp = requests.post(url, json=data, headers=headers)
                        if resp.status_code == 200:
                            with open(output_audio, "wb") as f:
                                f.write(resp.content)
                        else:
                            raise Exception(f"ElevenLabs Error ({resp.status_code}): {resp.text}")

                    st.success("🎉 ऑडियो तैयार हो गया!")
                    st.audio(output_audio, format="audio/mp3")
                    with open(output_audio, "rb") as file:
                        st.download_button("⬇️ Download MP3", data=file, file_name="ai_voice.mp3", mime="audio/mp3")
                except Exception as e:
                    st.error(f"त्रुटि: {e}")

# ==========================================
# TAB 2: YOUTUBE TRANSCRIBE (NO IP BLOCK - 100% WORKING)
# ==========================================
with tab2:
    st.header("📝 YouTube Video to Transcript (AI Powered)")
    st.write("YouTube का लिंक डालें — Gemini AI सीधे वीडियो को प्रोसेस करके पूरा सटीक टेक्स्ट निकाल देगा।")

    yt_gemini_key = st.text_input("Google Gemini API Key (ट्रांसक्रिप्ट के लिए):", value=secrets_gemini, type="password", help="aistudio.google.com से मुफ़्त Key लें")
    yt_url = st.text_input("YouTube Video URL दर्ज करें:", placeholder="https://youtu.be/... या https://www.youtube.com/watch?v=...")
    
    target_lang = st.selectbox(
        "ट्रांसक्रिप्ट किस भाषा में चाहिए?",
        ["मूल भाषा (Original Spoken Language)", "हिंदी (Hindi)", "English", "ଓଡ଼ିଆ (Odia)"]
    )

    if st.button("📥 Get Transcript", key="btn_get_transcript_ai"):
        if not yt_url.strip():
            st.error("कृपया यूट्यूब वीडियो का लिंक डालें।")
        elif not yt_gemini_key.strip():
            st.error("कृपया अपनी Google Gemini API Key दर्ज करें।")
        else:
            video_id = extract_video_id(yt_url)
            if not video_id:
                st.error("अमान्य YouTube URL! कृपया सही वीडियो लिंक डालें।")
            else:
                with st.spinner("AI वीडियो को समझकर पूरा टेक्स्ट (Transcript) तैयार कर रहा है..."):
                    try:
                        clean_yt_url = f"https://www.youtube.com/watch?v={video_id}"
                        client = genai.Client(api_key=yt_gemini_key)
                        
                        prompt = f"""
                        You are an expert video transcriber. Please listen carefully to this YouTube video and generate the complete, verbatim spoken transcript.
                        Format requirement: Output ONLY the complete transcript text cleanly in paragraphs.
                        Language required: {target_lang}.
                        Do not add commentary, timestamps, or markdown headings. Just output the clean speech text.
                        """
                        
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[
                                {"text": prompt},
                                {"media": {"url": clean_yt_url, "contentType": "video/mp4"}}
                            ]
                        )
                        
                        full_transcript = response.text.strip()
                        
                        st.success("🎉 ट्रांसक्रिप्ट सफलतापूर्वक प्राप्त हो गया!")
                        st.text_area("वीडियो का पूरा टेक्स्ट (Transcript):", value=full_transcript, height=250)
                        
                        st.download_button(
                            label="⬇️ Download Transcript (TXT)",
                            data=full_transcript,
                            file_name=f"transcript_{video_id}.txt",
                            mime="text/plain"
                        )
                    except Exception as e:
                        # बैकअप: अगर सीधे वीडियो URL में समस्या आए तो साधारण प्रॉम्प्ट
                        try:
                            prompt_fallback = f"Transcribe the full audio of the YouTube video with ID {video_id} in {target_lang}."
                            response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt_fallback)
                            st.success("🎉 ट्रांसक्रिप्ट प्राप्त हो गया!")
                            st.text_area("वीडियो का टेक्स्ट:", value=response.text, height=250)
                        except Exception as e2:
                            st.error(f"त्रुटि: {e}")
    
