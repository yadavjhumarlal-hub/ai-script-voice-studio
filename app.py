import streamlit as st
import edge_tts
import asyncio
from gtts import gTTS
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
        "🆓 100% Free & Unlimited (Edge/Google)",
        "✨ Google Gemini Engine (Free API Key)",
        "💎 ElevenLabs Characters (API Key)"
    )
)

# 1. फ्री आवाज़ें
free_voices = {
    # 🇮🇳 हिंदी आवाज़ें
    "1. Hindi - Madhur (गंभीर पुरुष / कहानी व यूट्यूब)": ("edge", "hi-IN-MadhurNeural", "+0%", "+0Hz"),
    "2. Hindi - Swara (स्पष्ट महिला / समाचार व व्याख्या)": ("edge", "hi-IN-SwaraNeural", "+0%", "+0Hz"),
    "3. Hindi - Deep Villain / Documentary (गहरी भारी आवाज़ / पुरुष)": ("edge", "hi-IN-MadhurNeural", "-10%", "-15Hz"),
    "4. Hindi - Energetic Storyteller (उत्साही कहानीकार / पुरुष)": ("edge", "hi-IN-MadhurNeural", "+12%", "+4Hz"),
    "5. Hindi - Soft Calm Female (शांत व मधुर / महिला)": ("edge", "hi-IN-SwaraNeural", "-8%", "-3Hz"),
    "6. Hindi - Young Narration (तेज़ व युवा अंदाज़ / महिला)": ("edge", "hi-IN-SwaraNeural", "+15%", "+10Hz"),
    
    # 🇮🇳 ओड़िया आवाज़ें (gTTS Engine)
    "7. Odia - Female 1 (ଓଡ଼ିଆ ମହିଳା - ସାଧାରଣ)": ("gtts", "or", "normal", "0Hz"),
    "8. Odia - Female 2 (ଓଡ଼ିଆ ମହିଳା - ଧୀର/କାହାଣୀ)": ("gtts", "or", "slow", "0Hz"),
    
    # 🌍 इंग्लिश आवाज़ें
    "9. English - Guy (US Narration Male)": ("edge", "en-US-GuyNeural", "+0%", "+0Hz"),
    "10. English - Jenny (US Professional Female)": ("edge", "en-US-JennyNeural", "+0%", "+0Hz")
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

# UI कंट्रोल्स
speed_adjust = 0
api_key = ""

if engine_choice.startswith("🆓"):
    selected_voice = st.sidebar.selectbox("फ्री आवाज़ चुनें:", list(free_voices.keys()))
    speed_adjust = st.sidebar.slider("स्पीड और घटाएं/बढ़ाएं (%):", -30, 30, 0, step=5)
elif engine_choice.startswith("✨"):
    api_key = st.sidebar.text_input("Google Gemini API Key डालें:", type="password", help="aistudio.google.com से मुफ़्त में लें")
    gemini_tone = st.sidebar.selectbox("Gemini का अंदाज़ (Tone):", ["कहानीकार (Storyteller)", "उत्साही (Excited)", "शांत व गंभीर (Calm & Professional)"])
    selected_voice = st.sidebar.selectbox("आउटपुट आवाज़:", ["Hindi - Madhur (Male)", "Hindi - Swara (Female)", "Odia - Female (ଓଡ଼ିଆ)"])
else:
    api_key = st.sidebar.text_input("ElevenLabs API Key डालें:", type="password", help="elevenlabs.io से अपनी Key लें")
    selected_voice = st.sidebar.selectbox("ElevenLabs कैरेक्टर चुनें:", list(elevenlabs_voices.keys()))

# टेक्स्ट इनपुट
text_input = st.text_area(
    "यहाँ अपना टेक्स्ट लिखें या पेस्ट करें (हिंदी / ଓଡ଼ିଆ / English):",
    height=200,
    placeholder="यहाँ वह टेक्स्ट लिखें जिसे आप AI आवाज़ में बदलना चाहते हैं..."
)

# Edge TTS फंक्शन
async def generate_edge(text, voice_code, rate_str, pitch_str, output_file):
    communicate = edge_tts.Communicate(text, voice_code, rate=rate_str, pitch=pitch_str)
    await communicate.save(output_file)

if st.button("🚀 Generate Audio (MP3)"):
    if not text_input.strip():
        st.error("कृपया पहले कोई टेक्स्ट लिखें।")
    elif (engine_choice.startswith("✨") or engine_choice.startswith("💎")) and not api_key.strip():
        st.error("कृपया साइडबार में अपनी API Key दर्ज करें।")
    else:
        with st.spinner("AI आवाज़ तैयार की जा रही है..."):
            output_audio = "final_output.mp3"
            
            if os.path.exists(output_audio):
                os.remove(output_audio)
                
            try:
                # 1. फ्री इंजन
                if engine_choice.startswith("🆓"):
                    eng_type, code, default_rate, default_pitch = free_voices[selected_voice]
                    
                    if eng_type == "gtts":
                        is_slow = (default_rate == "slow") or (speed_adjust < 0)
                        tts = gTTS(text=text_input, lang="or", slow=is_slow)
                        tts.save(output_audio)
                    else:
                        base_rate = int(default_rate.replace("%", ""))
                        final_rate = f"{base_rate + speed_adjust:+d}%"
                        asyncio.run(generate_edge(text_input, code, final_rate, default_pitch, output_audio))

                # 2. Google Gemini इंजन (लेटेस्ट मॉडल: gemini-3.6-flash)
                elif engine_choice.startswith("✨"):
                    client = genai.Client(api_key=api_key)
                    prompt = f"इस टेक्स्ट को {gemini_tone} के अंदाज़ में वॉइस-ओवर के लिए सबसे बेहतरीन और नेचुरल फ्लो में सुधारें: {text_input}"
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt
                    )
                    polished_text = response.text
                    
                    if "Odia" in selected_voice:
                        tts = gTTS(text=polished_text, lang="or", slow=False)
                        tts.save(output_audio)
                    elif "Madhur" in selected_voice:
                        asyncio.run(generate_edge(polished_text, "hi-IN-MadhurNeural", "+0%", "+0Hz", output_audio))
                    else:
                        asyncio.run(generate_edge(polished_text, "hi-IN-SwaraNeural", "+0%", "+0Hz", output_audio))

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
    
