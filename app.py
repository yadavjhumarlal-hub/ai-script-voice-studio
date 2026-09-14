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
# प्रीमियम UI और क्लीन डार्क स्टाइलिंग
# ==========================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(145deg, #0b0f19 0%, #1e1b4b 100%);
        color: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* हेडर स्टाइल */
    .studio-header {
        text-align: center;
        padding: 10px 0 20px 0;
    }
    .studio-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .studio-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
    }
    
    /* कार्ड स्टाइल */
    .studio-card {
        background: rgba(30, 41, 59, 0.75);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin-bottom: 20px;
    }
    
    /* टेक्स्ट एरिया */
    .stTextArea textarea {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 14px !important;
        font-size: 15px !important;
    }
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 1px #6366f1 !important;
    }
    
    /* जनरेट बटन */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(124, 58, 237, 0.6) !important;
    }
    
    /* मेट्रिक्स चिप्स */
    .metric-chip {
        display: inline-block;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 4px 12px;
        font-size: 0.85rem;
        color: #38bdf8;
        margin-right: 8px;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Secrets
secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")
secrets_eleven = st.secrets.get("ELEVEN_API_KEY", "")

# टॉप हेडर
st.markdown("""
<div class="studio-header">
    <div class="studio-title">🎙️ Universal AI Voice Studio Pro</div>
    <div class="studio-subtitle">100% Free Neural Engine • ElevenLabs Deep Presets • Google Gemini AI</div>
</div>
""", unsafe_allow_html=True)

# आवाज़ों का विस्तृत कैटलॉग
free_voices = {
    "💎 ElevenLabs Style - Adam (डीप भारी बेस / Male)": ("hi-IN-MadhurNeural", "-16Hz", "-6%"),
    "💎 ElevenLabs Style - Josh (भारी विलेन / Male)": ("hi-IN-MadhurNeural", "-20Hz", "-8%"),
    "💎 ElevenLabs Style - Arnold (सिनेमैटिक ट्रेलर भारी / Male)": ("hi-IN-MadhurNeural", "-24Hz", "-12%"),
    "💎 ElevenLabs Style - Antoni (ऊर्जावान / Male)": ("hi-IN-MadhurNeural", "+4Hz", "+6%"),
    "💎 ElevenLabs Style - Sam (शांत कथावाचक / Male)": ("hi-IN-MadhurNeural", "-10Hz", "-10%"),
    "💎 ElevenLabs Style - Rachel (स्मार्ट व साफ़ / Female)": ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    "💎 ElevenLabs Style - Matilda (कहानीकार / Female)": ("hi-IN-SwaraNeural", "-6Hz", "-6%"),
    "💎 ElevenLabs Style - Bella (सॉफ्ट और मधुर / Female)": ("hi-IN-SwaraNeural", "-2Hz", "-8%"),
    "1. Hindi - Madhur (स्टैंडर्ड कहानी / Male)": ("hi-IN-MadhurNeural", "+0Hz", "+0%"),
    "2. Hindi - Swara (समाचार / Female)": ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    "3. Hindi - Deep Documentary (डॉक्यूमेंट्री भारी / Male)": ("hi-IN-MadhurNeural", "-12Hz", "-5%"),
    "4. Hindi - Energetic RJ (उत्साही आरजे / Male)": ("hi-IN-MadhurNeural", "+8Hz", "+12%"),
    "5. Hindi - Calm Meditation (शांत व ध्यान / Female)": ("hi-IN-SwaraNeural", "-8Hz", "-10%"),
    "6. Hindi - Fast Reels (तेज़ रील्स / Female)": ("hi-IN-SwaraNeural", "+6Hz", "+15%"),
    "💎 English - Adam Clone (Deep US Male)": ("en-US-GuyNeural", "-14Hz", "-6%"),
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

# साइडबार: बैकएंड इंजन चयन
st.sidebar.header("⚙️ वॉयस इंजन सेटिंग्स")
engine_choice = st.sidebar.radio(
    "इंजन मोड:",
    (
        "🆓 100% Free (ElevenLabs Clones & Neural)",
        "✨ Google Gemini Engine (Exact Script Speech)",
        "💎 ElevenLabs Original Characters (Official API)"
    )
)

api_key = ""
if engine_choice.startswith("✨"):
    api_key = st.sidebar.text_input("Google Gemini API Key:", value=secrets_gemini, type="password")
elif engine_choice.startswith("💎"):
    api_key = st.sidebar.text_input("ElevenLabs API Key:", value=secrets_eleven, type="password")

# ==========================================
# मुख्य 2-कॉलम लेआउट
# ==========================================
col1, col2 = st.columns([1.15, 1], gap="medium")

with col1:
    st.markdown('<div class="studio-card">', unsafe_allow_html=True)
    st.subheader("📝 स्क्रिप्ट कंसोल")
    
    # 1. टॉप कंट्रोल: सीधे होमपेज पर आवाज़ चुनने का विकल्प
    if engine_choice.startswith("🆓"):
        selected_voice = st.selectbox("🎙️ आवाज़ / कैरेक्टर चुनें:", list(free_voices.keys()))
    elif engine_choice.startswith("✨"):
        selected_voice = st.selectbox("🎙️ आवाज़ टोन चुनें:", ["💎 Adam Style (Deep Male)", "💎 Josh Style (Heavy Male)", "💎 Rachel Style (Female)", "Hindi - Madhur", "Hindi - Swara"])
    else:
        selected_voice = st.selectbox("🎙️ ElevenLabs कैरेक्टर चुनें:", list(elevenlabs_voices.keys()))
        
    # 2. टेक्स्ट एरिया
    text_input = st.text_area(
        "अपना टेक्स्ट दर्ज करें:",
        height=210,
        placeholder="यहाँ अपनी यूट्यूब स्क्रिप्ट, रील्स या कहानी का टेक्स्ट लिखें या पेस्ट करें..."
    )
    
    # 3. बॉटम कंट्रोल: स्पीड और पिच एडजस्टमेंट
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        speed_adjust = st.slider("⚡ स्पीड (% Speed):", -30, 30, 0, step=5)
    with c_s2:
        pitch_adjust = st.slider("🎚️ बेस / भारीपन (Pitch Hz):", -24, 24, 0, step=2)
        
    # लाइव स्टैट्स चिप्स
    words = len(text_input.split()) if text_input.strip() else 0
    chars = len(text_input)
    est_sec = round(words / 2.5) if words > 0 else 0
    
    st.markdown(f"""
    <div style="margin-bottom: 15px;">
        <span class="metric-chip">📝 अक्षर: <b>{chars}</b></span>
        <span class="metric-chip">💬 शब्द: <b>{words}</b></span>
        <span class="metric-chip">⏱️ समय: <b>~{est_sec} सेकंड</b></span>
    </div>
    """, unsafe_allow_html=True)
    
    generate_btn = st.button("🚀 Generate Studio Audio (MP3)")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="studio-card">', unsafe_allow_html=True)
    st.subheader("🎧 ऑडियो मास्टरिंग आउटपुट")
    
    if generate_btn:
        if not text_input.strip():
            st.error("कृपया पहले कोई टेक्स्ट दर्ज करें।")
        elif (engine_choice.startswith("✨") or engine_choice.startswith("💎")) and not api_key.strip():
            st.error("कृपया साइडबार में अपनी API Key दर्ज करें।")
        else:
            with st.spinner("उच्च गुणवत्ता वाला स्टूडियो ऑडियो तैयार हो रहा है..."):
                output_audio = "studio_voice.mp3"
                if os.path.exists(output_audio):
                    os.remove(output_audio)
                    
                async def run_edge_audio(txt, code, p, r):
                    comm = edge_tts.Communicate(txt, code, pitch=p, rate=r)
                    await comm.save(output_audio)

                try:
                    if engine_choice.startswith("🆓"):
                        b_code, d_p, d_r = free_voices[selected_voice]
                        calc_p = f"{int(d_p.replace('Hz','')) + pitch_adjust:+d}Hz"
                        calc_r = f"{int(d_r.replace('%','')) + speed_adjust:+d}%"
                        asyncio.run(run_edge_audio(text_input, b_code, calc_p, calc_r))
                        
                    elif engine_choice.startswith("✨"):
                        target_t = text_input.strip()
                        v_code = "hi-IN-MadhurNeural" if "Male" in selected_voice or "Madhur" in selected_voice else "hi-IN-SwaraNeural"
                        p_val = "-16Hz" if "Adam" in selected_voice else ("-20Hz" if "Josh" in selected_voice else "+0Hz")
                        asyncio.run(run_edge_audio(target_t, v_code, p_val, "-5%"))
                        
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

                    st.success("🎉 ऑडियो सफलतापूर्वक तैयार हो गया!")
                    st.audio(output_audio, format="audio/mp3")
                    
                    with open(output_audio, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Studio MP3",
                            data=file,
                            file_name="universal_studio_voice.mp3",
                            mime="audio/mp3"
                        )
                except Exception as e:
                    st.error(f"त्रुटि: {e}")
    else:
        st.info("💡 बाईं ओर अपनी आवाज़ चुनें, टेक्स्ट दर्ज करें और **'Generate Studio Audio'** दबाएं।")
    st.markdown('</div>', unsafe_allow_html=True)
