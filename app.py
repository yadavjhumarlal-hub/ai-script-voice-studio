import streamlit as st
import edge_tts
import asyncio
import requests
from google import genai
import os

st.set_page_config(page_title="Universal AI Voice Studio", page_icon="🎙️", layout="centered")

st.title("🎙️ Universal AI Voice Studio")
st.write("फ्री अनलिमिटेड न्यूरल आवाज़ें + Google Gemini AI + ElevenLabs कैरेक्टर")

# साइडबार - इंजन चयन
st.sidebar.header("⚙️ Engine & Voice Settings")
engine_choice = st.sidebar.radio(
    "वॉयस इंजन चुनें:",
    (
        "🆓 100% Free & Unlimited (Edge Neural)",
        "✨ Google Gemini Engine (Free API Key)",
        "💎 ElevenLabs Characters (API Key)"
    )
)

# 1. फ्री आवाज़ों की सूची (हिंदी 10, ओड़िया 2, इंग्लिश 2)
free_voices = {
    # 🇮🇳 हिंदी - 10 अलग-अलग प्रोफाइल्स
    "1. Hindi - Madhur (कहानी / क्लासिक कथावाचक - Male)": ("hi-IN-MadhurNeural", 0),
    "2. Hindi - Swara (समाचार / साफ़ व्याख्या - Female)": ("hi-IN-SwaraNeural", 0),
    "3. Hindi - Deep Documentary (गंभीर व भारी - Male)": ("hi-IN-MadhurNeural", -12),
    "4. Hindi - Energetic RJ (रेडियो जॉकी व पॉडकास्ट - Male)": ("hi-IN-MadhurNeural", 12),
    "5. Hindi - Calm Meditation (शांत व मधुर - Female)": ("hi-IN-SwaraNeural", -10),
    "6. Hindi - Fast Reels / Shorts (तेज़ व युवा - Female)": ("hi-IN-SwaraNeural", 15),
    "7. Hindi - Motivational Speaker (जोशीला अंदाज़ - Male)": ("hi-IN-MadhurNeural", 8),
    "8. Hindi - Soft Storyteller (भावुक व धीमी कहानी - Female)": ("hi-IN-SwaraNeural", -6),
    "9. Hindi - Heavy Villain / Dramatic (गहरा ड्रामेटिक विलेन - Male)": ("hi-IN-MadhurNeural", -18),
    "10. Hindi - Corporate Presentation (प्रोफेशनल - Female)": ("hi-IN-SwaraNeural", 4),
    
    # 🇮🇳 ओड़िया आधिकारिक न्यूरल आवाज़ें
    "11. Odia - Sukant (ଓଡ଼ିଆ ପୁରୁଷ / Male)": ("ory-IN-SukantNeural", 0),
    "12. Odia - Subhasini (ଓଡ଼ିଆ ମହିଳା / Female)": ("ory-IN-SubhasiniNeural", 0),
    
    # 🌍 इंग्लिश आवाज़ें
    "13. English - Guy (US Narration Male)": ("en-US-GuyNeural", 0),
    "14. English - Jenny (US Professional Female)": ("en-US-JennyNeural", 0)
}

# 2. ElevenLabs आवाज़ें
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
    speed_adjust = st.sidebar.slider("स्पीड और घटाएं/बढ़ाएं (%):", -30, 30, 0, step=5)
elif engine_choice.startswith("✨"):
    api_key = st.sidebar.text_input("Google Gemini API Key डालें:", type="password", help="aistudio.google.com से लें")
    gemini_tone = st.sidebar.selectbox("Gemini का अंदाज़:", ["कहानीकार (Storyteller)", "उत्साही (Excited)", "शांत व गंभीर (Calm & Professional)"])
    selected_voice = st.sidebar.selectbox("आउटपुट आवाज़:", ["Hindi - Madhur (Male)", "Hindi - Swara (Female)", "Odia - Subhasini (Female)", "Odia - Sukant (Male)"])
else:
    api_key = st.sidebar.text_input("ElevenLabs API Key डालें:", type="password", help="elevenlabs.io से लें")
    selected_voice = st.sidebar.selectbox("ElevenLabs कैरेक्टर चुनें:", list(elevenlabs_voices.keys()))

# टेक्स्ट इनपुट
text_input = st.text_area(
    "यहाँ अपना टेक्स्ट लिखें या पेस्ट करें (हिंदी / ଓଡ଼ିଆ / English):",
    height=200,
    placeholder="हिंदी, ଓଡ଼ିଆ या English टेक्स्ट यहाँ लिखें..."
)

# Edge TTS फंक्शन
async def generate_edge_clean(text, voice_code, rate_str, output_file):
    communicate = edge_tts.Communicate(text, voice_code, rate=rate_str)
    await communicate.save(output_file)

if st.button("🚀 Generate Audio (MP3)"):
    if not text_input.strip():
        st.error("कृपया पहले कोई टेक्स्ट दर्ज करें।")
    elif (engine_choice.startswith("✨") or engine_choice.startswith("💎")) and not api_key.strip():
        st.error("कृपया साइडबार में अपनी API Key दर्ज करें।")
    else:
        with st.spinner("AI आवाज़ तैयार की जा रही है..."):
            output_audio = "final_output.mp3"
            
            if os.path.exists(output_audio):
                os.remove(output_audio)
                
            try:
                # 1. फ्री न्यूरल इंजन
                if engine_choice.startswith("🆓"):
                    voice_code, base_speed = free_voices[selected_voice]
                    total_speed = base_speed + speed_adjust
                    rate_str = f"{total_speed:+d}%"
                    asyncio.run(generate_edge_clean(text_input, voice_code, rate_str, output_audio))

                # 2. Google Gemini इंजन
                elif engine_choice.startswith("✨"):
                    client = genai.Client(api_key=api_key)
                    
                    if "Odia" in selected_voice:
                        prompt = f"इस टेक्स्ट को शुद्ध ओड़िया लिपि (Odia Script) में {gemini_tone} वॉइस-ओवर के लिए सबसे सुंदर तरीके से ढालें: {text_input}"
                        target_code = "or-IN-SubhasiniNeural" if "Subhasini" in selected_voice else "or-IN-SukantNeural"
                    else:
                        prompt = f"इस टेक्स्ट को {gemini_tone} के अंदाज़ में वॉइस-ओवर के लिए सबसे बेहतरीन फ्लो में सुधारें: {text_input}"
                        target_code = "hi-IN-MadhurNeural" if "Madhur" in selected_voice else "hi-IN-SwaraNeural"
                    
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt
                    )
                    polished_text = response.text
                    asyncio.run(generate_edge_clean(polished_text, target_code, "+0%", output_audio))

                # 3. ElevenLabs इंजन
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
                    resp = requests.post(url, json=data, headers=headers)
                    if resp.status_code == 200:
                        with open(output_audio, "wb") as f:
                            f.write(resp.content)
                    else:
                        raise Exception(f"ElevenLabs Error ({resp.status_code}): {resp.text}")

                st.success("🎉 ऑडियो सफलतापूर्वक तैयार हो गया!")
                st.audio(output_audio, format="audio/mp3")
                
                with open(output_audio, "rb") as file:
                    st.download_button(
                        label="⬇️ Download MP3",
                        data=file,
                        file_name="ai_voice.mp3",
                        mime="audio/mp3"
                    )
            except Exception as e:
                st.error(f"त्रुटि: {e}")
