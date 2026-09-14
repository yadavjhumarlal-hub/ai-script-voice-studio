import streamlit as st
import edge_tts
import asyncio
import requests
from google import genai
import os

st.set_page_config(
    page_title="Universal AI Voice Studio Pro",
    page_icon="🎙️",
    layout="wide"
)

# ==========================================
# कस्टम CSS: डार्क ग्लास और प्रीमियम स्टाइलिंग
# ==========================================
st.markdown("""
<style>
    /* बैकग्राउंड और फॉन्ट */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* मुख्य हेडर */
    .header-box {
        text-align: center;
        padding: 20px 10px 10px 10px;
        margin-bottom: 25px;
    }
    .header-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .header-sub {
        font-size: 1rem;
        color: #94a3b8;
    }
    
    /* ग्लास कार्ड कंटेनर */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
    }
    
    /* टेक्स्ट एरिया */
    .stTextArea textarea {
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        font-size: 15px !important;
    }
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 1px #6366f1 !important;
    }
    
    /* मुख्य जनरेट बटन */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 14px 0 rgba(124, 58, 237, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(124, 58, 237, 0.6) !important;
    }
    
    /* ऑडियो प्लेयर बॉक्स */
    .audio-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid #4f46e5;
        border-radius: 16px;
        padding: 20px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Secrets
secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")
secrets_eleven = st.secrets.get("ELEVEN_API_KEY", "")

# टॉप हेडर
st.markdown("""
<div class="header-box">
    <div class="header-title">🎙️ Universal AI Voice Studio Pro</div>
    <div class="header-sub">अल्ट्रा-न्यूरल आवाज़ें • ElevenLabs डीप टोन • Google Gemini AI • 100% Free & Unlimited</div>
</div>
""", unsafe_allow_html=True)

# साइडबार
st.sidebar.header("⚙️ इंजन व ऑडियो ट्यूनिंग")
engine_choice = st.sidebar.radio(
    "वॉयस इंजन चुनें:",
    (
        "🆓 100% Free (ElevenLabs Clone & Neural)",
        "✨ Google Gemini Engine (Exact Script Speech)",
        "💎 ElevenLabs Original Characters (Official API)"
    )
)

free_voices = {
    "💎 ElevenLabs Style - Adam (डीप भारी बेस / Male)": ("hi-IN-MadhurNeural", "-16Hz", "-6%"),
    "💎 ElevenLabs Style - Josh (भारी विलेन / Male)": ("hi-IN-MadhurNeural", "-20Hz", "-8%"),
    "💎 ElevenLabs Style - Arnold (सिनेमैटिक ट्रेलर / Male)": ("hi-IN-MadhurNeural", "-24Hz", "-12%"),
    "💎 ElevenLabs Style - Antoni (ऊर्जावान / Male)": ("hi-IN-MadhurNeural", "+4Hz", "+6%"),
    "💎 ElevenLabs Style - Sam (शांत कथावाचक / Male)": ("hi-IN-MadhurNeural", "-10Hz", "-10%"),
    "💎 ElevenLabs Style - Rachel (स्मार्ट व साफ़ / Female)": ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    "💎 ElevenLabs Style - Matilda (इमोशनल कहानीकार / Female)": ("hi-IN-SwaraNeural", "-6Hz", "-6%"),
    "💎 ElevenLabs Style - Bella (सॉफ्ट और मधुर / Female)": ("hi-IN-SwaraNeural", "-2Hz", "-8%"),
    "1. Hindi - Madhur (स्टैंडर्ड कहानी / Male)": ("hi-IN-MadhurNeural", "+0Hz", "+0%"),
    "2. Hindi - Swara (समाचार / Female)": ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    "3. Hindi - Deep Documentary (भारी / Male)": ("hi-IN-MadhurNeural", "-12Hz", "-5%"),
    "4. Hindi - Energetic RJ (उत्साही आरजे / Male)": ("hi-IN-MadhurNeural", "+8Hz", "+12%"),
    "5. Hindi - Calm Meditation (शांत व ध्यान / Female)": ("hi-IN-SwaraNeural", "-8Hz", "-10%"),
    "6. Hindi - Fast Reels (तेज़ रील्स / Female)": ("hi-IN-SwaraNeural", "+6Hz", "+15%"),
    "💎 English - Adam Clone (Deep US Narration Male)": ("en-US-GuyNeural", "-14Hz", "-6%"),
    "11. English - Guy Natural (US Male)": ("en-US-GuyNeural", "+0Hz", "+0%"),
    "12. English - Jenny Natural (US Female)": ("en-US-JennyNeural", "+0Hz", "+0%")
}

elevenlabs_voices = {
    "Adam (डीप नरेशन / भारी मेल)": "pNInz6obpgDQGcFmaJgB",
    "Rachel (प्रोफेशनल / शांत फीमेल)": "21m00Tcm4TlvDq8ikWAM",
    "Antoni (उत्साही / ऊर्जावान मेल)": "ErXwobaYiN019PkySvjV",
    "Bella (सॉफ्ट नैरेटर / फीमेल)": "EXAVITQu4vr4xnSDxMaL",
    "Josh (पॉडकास्ट / भारी बेस मेल)": "TxGEqnHWrfWFTfGW9XjX",
    "Matilda (स्टोरीटेलिंग / भावुक फीमेल)": "XrExE9yKIg1WjnnlVkGX"
}

speed_adjust = 0
pitch_adjust = 0
api_key = ""

if engine_choice.startswith("🆓"):
    selected_voice = st.sidebar.selectbox("आवाज़ कैरेक्टर चुनें:", list(free_voices.keys()))
    speed_adjust = st.sidebar.slider("स्पीड एडजस्ट करें (%):", -30, 30, 0, step=5)
    pitch_adjust = st.sidebar.slider("बेस / पिच (Pitch Hz):", -24, 24, 0, step=2)
elif engine_choice.startswith("✨"):
    api_key = st.sidebar.text_input("Google Gemini API Key:", value=secrets_gemini, type="password")
    gemini_mode = st.sidebar.radio("मोड:", ["1. केवल मेरा दिया गया टेक्स्ट ही बोलें (Exact Verbatim)", "2. स्क्रिप्ट सुधारकर बोलें (Enhance)"])
    selected_voice = st.sidebar.selectbox("आवाज़ टोन:", ["💎 Adam Style (Deep Male)", "💎 Josh Style (Heavy Male)", "💎 Rachel Style (Female)", "Hindi - Madhur", "Hindi - Swara"])
else:
    api_key = st.sidebar.text_input("ElevenLabs API Key:", value=secrets_eleven, type="password")
    selected_voice = st.sidebar.selectbox("ElevenLabs कैरेक्टर:", list(elevenlabs_voices.keys()))

# 2-कॉलम लेआउट
col1, col2 = st.columns([1.2, 1], gap="large")

with col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📝 स्क्रिप्ट कंसोल")
    text_input = st.text_area(
        "अपना टेक्स्ट दर्ज करें:",
        height=240,
        placeholder="यहाँ अपनी कहानी, यूट्यूब स्क्रिप्ट या रील्स का डायलॉग लिखें..."
    )
    
    # लाइव स्टैट्स
    char_count = len(text_input)
    word_count = len(text_input.split()) if text_input.strip() else 0
    est_time = round(word_count / 2.5) # ~150 wpm
    st.markdown(f"<small style='color:#94a3b8;'>📊 <b>अक्षर:</b> {char_count} | <b>शब्द:</b> {word_count} | <b>अनुमानित समय:</b> ~{est_time} सेकंड</small>", unsafe_allow_html=True)
    
    generate_btn = st.button("🚀 Generate Studio Audio (MP3)")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🎧 ऑडियो मास्टरिंग आउटपुट")
    
    if generate_btn:
        if not text_input.strip():
            st.error("कृपया पहले कोई टेक्स्ट दर्ज करें।")
        elif (engine_choice.startswith("✨") or engine_choice.startswith("💎")) and not api_key.strip():
            st.error("कृपया साइडबार में अपनी API Key दर्ज करें।")
        else:
            with st.spinner("उच्च गुणवत्ता वाला ऑडियो प्रोसेस किया जा रहा है..."):
                output_audio = "studio_voice.mp3"
                if os.path.exists(output_audio):
                    os.remove(output_audio)
                    
                async def run_edge(txt, code, p, r):
                    comm = edge_tts.Communicate(txt, code, pitch=p, rate=r)
                    await comm.save(output_audio)

                try:
                    if engine_choice.startswith("🆓"):
                        b_code, d_p, d_r = free_voices[selected_voice]
                        f_p = f"{int(d_p.replace('Hz','')) + pitch_adjust:+d}Hz"
                        f_r = f"{int(d_r.replace('%','')) + speed_adjust:+d}%"
                        asyncio.run(run_edge(text_input, b_code, f_p, f_r))
                    elif engine_choice.startswith("✨"):
                        target_t = text_input.strip()
                        if "सुधारकर" in gemini_mode:
                            client = genai.Client(api_key=api_key)
                            prmpt = f"Enhance phrasing naturally. Output ONLY the script. Text: {text_input}"
                            res = client.models.generate_content(model="gemini-3.6-flash", contents=prmpt)
                            target_t = res.text.strip()
                        v_code = "hi-IN-MadhurNeural" if "Male" in selected_voice or "Madhur" in selected_voice else "hi-IN-SwaraNeural"
                        p_val = "-16Hz" if "Adam" in selected_voice else ("-20Hz" if "Josh" in selected_voice else "+0Hz")
                        asyncio.run(run_edge(target_t, v_code, p_val, "-5%"))
                    else:
                        v_id = elevenlabs_voices[selected_voice]
                        u = f"https://api.elevenlabs.io/v1/text-to-speech/{v_id}"
                        h = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
                        d = {"text": text_input, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
                        resp = requests.post(u, json=d, headers=h, timeout=30)
                        if resp.status_code == 200:
                            with open(output_audio, "wb") as f:
                                f.write(resp.content)
                        else:
                            raise Exception(f"ElevenLabs Error: {resp.text}")

                    st.markdown("""
                    <div class="audio-card">
                        <div style="color: #4ade80; font-weight: bold; margin-bottom: 10px;">✅ ऑडियो सफलतापूर्वक तैयार!</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.audio(output_audio, format="audio/mp3")
                    with open(output_audio, "rb") as file:
                        st.download_button(
                            label="⬇️ Download High Quality MP3",
                            data=file,
                            file_name="universal_ai_audio.mp3",
                            mime="audio/mp3"
                        )
                except Exception as e:
                    st.error(f"त्रुटि: {e}")
    else:
        st.info("👈 बाईं ओर अपना टेक्स्ट लिखें और **'Generate Studio Audio'** बटन दबाएं।")
    st.markdown('</div>', unsafe_allow_html=True)
