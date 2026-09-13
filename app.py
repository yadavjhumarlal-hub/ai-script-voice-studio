import streamlit as st
import edge_tts
import asyncio
import requests
from google import genai
import os

st.set_page_config(page_title="Universal All-in-One Voice Studio", page_icon="🎙️", layout="centered")

st.title("🎙️ Universal AI Voice Studio")
st.write("100% Free न्यूरल आवाज़ें + Google Gemini AI + ElevenLabs ओरिजिनल कैरेक्टर")

# Secrets से सुरक्षित रूप से API Keys लोड करना
secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")
secrets_eleven = st.secrets.get("ELEVEN_API_KEY", "")

# साइडबार इंजन सेलेक्टर
st.sidebar.header("⚙️ इंजन व आवाज़ सेटिंग्स")
engine_choice = st.sidebar.radio(
    "वॉयस इंजन चुनें:",
    (
        "🆓 100% Free & Unlimited (Edge Neural)",
        "✨ Google Gemini Engine (AI Script Polish + Voice)",
        "💎 ElevenLabs Original Characters (Official API)"
    )
)

# 1. फ्री आवाज़ों का कैटलॉग (10 हिंदी + 2 इंग्लिश + Adam डीप स्टाइल्स)
free_voices = {
    # मुख्य हिंदी आवाज़ें
    "1. Hindi - Madhur (कहानी / Male)": ("hi-IN-MadhurNeural", "+0Hz", "+0%"),
    "2. Hindi - Swara (समाचार / Female)": ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    "3. Hindi - Deep Documentary (भारी / Male)": ("hi-IN-MadhurNeural", "-12Hz", "-5%"),
    "4. Hindi - Energetic RJ (उत्साही / Male)": ("hi-IN-MadhurNeural", "+8Hz", "+12%"),
    "5. Hindi - Calm Meditation (शांत / Female)": ("hi-IN-SwaraNeural", "-8Hz", "-10%"),
    "6. Hindi - Fast Reels (तेज़ / Female)": ("hi-IN-SwaraNeural", "+6Hz", "+15%"),
    "7. Hindi - Motivational (जोशीला / Male)": ("hi-IN-MadhurNeural", "+4Hz", "+8%"),
    "8. Hindi - Soft Storyteller (भावुक / Female)": ("hi-IN-SwaraNeural", "-4Hz", "-6%"),
    "9. Hindi - Heavy Villain (विलेन / Male)": ("hi-IN-MadhurNeural", "-18Hz", "-8%"),
    "10. Hindi - Corporate (प्रोफेशनल / Female)": ("hi-IN-SwaraNeural", "+2Hz", "+4%"),
    
    # ElevenLabs स्टाइल फ्री डीप आवाज़ें
    "💎 Free Style - Adam (डीप भारी बेस / Male)": ("hi-IN-MadhurNeural", "-16Hz", "-5%"),
    "💎 Free Style - Josh (पॉडकास्ट भारी / Male)": ("hi-IN-MadhurNeural", "-12Hz", "-6%"),
    "💎 Free Style - Rachel (स्मार्ट व साफ़ / Female)": ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    "💎 Free Style - Matilda (कहानीकार / Female)": ("hi-IN-SwaraNeural", "-5Hz", "-4%"),
    
    # इंग्लिश आवाज़ें
    "11. English - Guy (US Male)": ("en-US-GuyNeural", "+0Hz", "+0%"),
    "12. English - Jenny (US Female)": ("en-US-JennyNeural", "+0Hz", "+0%"),
    "💎 English - Adam Clone (Deep US Male)": ("en-US-GuyNeural", "-14Hz", "-5%")
}

# 2. ElevenLabs आधिकारिक कैरेक्टर (Original Voice IDs)
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

# इंजन के अनुसार साइडबार सेटिंग्स
if engine_choice.startswith("🆓"):
    selected_voice = st.sidebar.selectbox("फ्री आवाज़ चुनें:", list(free_voices.keys()))
    speed_adjust = st.sidebar.slider("स्पीड एडजस्ट करें (%):", -30, 30, 0, step=5)
    pitch_adjust = st.sidebar.slider("बेस / पिच एडजस्ट करें (Pitch Hz):", -20, 20, 0, step=2)
    
elif engine_choice.startswith("✨"):
    api_key = st.sidebar.text_input("Google Gemini API Key:", value=secrets_gemini, type="password")
    gemini_tone = st.sidebar.selectbox(
        "Gemini का अंदाज़ (Script Enhancement):", 
        ["कहानीकार (Storyteller)", "उत्साही (Excited & Fast)", "शांत व गंभीर (Calm & Documentary)"]
    )
    selected_voice = st.sidebar.selectbox(
        "आउटपुट आवाज़ टोन:", 
        ["Hindi - Madhur (Male)", "Hindi - Swara (Female)", "Hindi - Deep Adam Style (Male)"]
    )
    
else:
    api_key = st.sidebar.text_input("ElevenLabs API Key:", value=secrets_eleven, type="password")
    selected_voice = st.sidebar.selectbox("ElevenLabs कैरेक्टर चुनें:", list(elevenlabs_voices.keys()))

# टेक्स्ट इनपुट
text_input = st.text_area(
    "यहाँ अपना टेक्स्ट लिखें या पेस्ट करें (हिंदी / English / ଓଡ଼ିଆ):",
    height=200,
    placeholder="यहाँ अपनी यूट्यूब स्क्रिप्ट, रील्स या कहानी का टेक्स्ट दर्ज करें..."
)

# Edge TTS जनरेशन हेल्पर
async def generate_edge_speech(text, base_code, pitch_str, rate_str, output_filename):
    communicate = edge_tts.Communicate(text, base_code, pitch=pitch_str, rate=rate_str)
    await communicate.save(output_filename)

if st.button("🚀 Generate Audio (MP3)", key="btn_run_voice"):
    if not text_input.strip():
        st.error("कृपया पहले कोई टेक्स्ट दर्ज करें।")
    elif (engine_choice.startswith("✨") or engine_choice.startswith("💎")) and not api_key.strip():
        st.error("कृपया साइडबार में अपनी API Key दर्ज करें।")
    else:
        with st.spinner("AI स्टूडियो ऑडियो तैयार कर रहा है..."):
            output_audio = "final_voice.mp3"
            if os.path.exists(output_audio):
                os.remove(output_audio)
                
            try:
                # ----------------------------------------------------
                # 1. फ्री न्यूरल इंजन (Edge-TTS)
                # ----------------------------------------------------
                if engine_choice.startswith("🆓"):
                    base_code, def_pitch, def_rate = free_voices[selected_voice]
                    calc_pitch = int(def_pitch.replace("Hz", "")) + pitch_adjust
                    calc_rate = int(def_rate.replace("%", "")) + speed_adjust
                    final_p = f"{calc_pitch:+d}Hz"
                    final_r = f"{calc_rate:+d}%"
                    asyncio.run(generate_edge_speech(text_input, base_code, final_p, final_r, output_audio))

                # ----------------------------------------------------
                # 2. Google Gemini AI इंजन (Script Polish + Voice)
                # ----------------------------------------------------
                elif engine_choice.startswith("✨"):
                    client = genai.Client(api_key=api_key)
                    prompt = f"Rewrite and enhance this script to make it sound natural and engaging in a {gemini_tone} tone. Keep the core meaning intact. Script: {text_input}"
                    res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
                    polished_text = res.text.strip()
                    
                    # वॉयस मैपिंग
                    if "Adam" in selected_voice:
                        v_code, p_str, r_str = "hi-IN-MadhurNeural", "-14Hz", "-5%"
                    elif "Madhur" in selected_voice:
                        v_code, p_str, r_str = "hi-IN-MadhurNeural", "+0Hz", "+0%"
                    else:
                        v_code, p_str, r_str = "hi-IN-SwaraNeural", "+0Hz", "+0%"
                        
                    asyncio.run(generate_edge_speech(polished_text, v_code, p_str, r_str, output_audio))

                # ----------------------------------------------------
                # 3. ElevenLabs आधिकारिक इंजन (Original Character API)
                # ----------------------------------------------------
                else:
                    v_id = elevenlabs_voices[selected_voice]
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{v_id}"
                    headers = {
                        "Accept": "audio/mpeg", 
                        "Content-Type": "application/json", 
                        "xi-api-key": api_key
                    }
                    data = {
                        "text": text_input, 
                        "model_id": "eleven_multilingual_v2", 
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                    }
                    resp = requests.post(url, json=data, headers=headers, timeout=30)
                    if resp.status_code == 200:
                        with open(output_audio, "wb") as f:
                            f.write(resp.content)
                    else:
                        raise Exception(f"ElevenLabs Error ({resp.status_code}): {resp.text}")

                # ऑडियो प्लेयर व डाउनलोड
                st.success("🎉 ऑडियो सफलतापूर्वक तैयार हो गया!")
                st.audio(output_audio, format="audio/mp3")
                with open(output_audio, "rb") as file:
                    st.download_button(
                        label="⬇️ Download MP3",
                        data=file,
                        file_name="universal_ai_voice.mp3",
                        mime="audio/mp3"
                    )

            except Exception as e:
                st.error(f"त्रुटि: {e}")
