import streamlit as st
import edge_tts
import asyncio
from gtts import gTTS
import requests
import os

st.set_page_config(page_title="Universal AI Voice Studio", page_icon="🎙️", layout="centered")

st.title("🎙️ Universal AI Voice Studio")
st.write("फ्री अनलिमिटेड न्यूरल आवाज़ें + ElevenLabs प्रीमियम कैरेक्टर एक ही जगह।")

# साइडबार - इंजन चयन
st.sidebar.header("⚙️ वॉयस इंजन चुनें")
engine_choice = st.sidebar.radio(
    "इंजन का प्रकार:",
    ("🆓 100% Free & Unlimited (Edge/Google)", "💎 ElevenLabs Premium Characters")
)

# 1. फ्री वॉयस लिस्ट (हिंदी, ओड़िया, इंग्लिश + स्पेशल कैरेक्टर प्रीसेट्स)
free_voices = {
    # 🇮🇳 हिंदी आवाज़ें
    "Hindi - Madhur (गंभीर कहानी / YouTube Male)": ("edge", "hi-IN-MadhurNeural", "0%", "0Hz"),
    "Hindi - Swara (स्पष्ट समाचार / Female)": ("edge", "hi-IN-SwaraNeural", "0%", "0Hz"),
    "Hindi - Prabhat (यूट्यूब व रील्स / Male)": ("edge", "en-IN-PrabhatNeural", "0%", "0Hz"),
    "Hindi - Neerja (नेचुरल व मधुर / Female)": ("edge", "en-IN-NeerjaNeural", "0%", "0Hz"),
    "Hindi - Gul (गहरी व शांत / Female)": ("edge", "ur-PK-GulNeural", "0%", "0Hz"),
    "Hindi - Asad (भारी व डॉक्यूमेंट्री / Male)": ("edge", "ur-PK-AsadNeural", "0%", "0Hz"),
    
    # 🎭 स्पेशल कैरेक्टर प्रीसेट्स (फ्री में अलग-अलग रोल)
    "Character - Kid / Cartoon (बच्चा / कार्टून)": ("edge", "hi-IN-SwaraNeural", "+10%", "+18Hz"),
    "Character - Deep Villain / Monster (भारी दानव / विलेन)": ("edge", "hi-IN-MadhurNeural", "-10%", "-18Hz"),
    "Character - Old Storyteller (बुज़ुर्ग कहानीकार)": ("edge", "hi-IN-MadhurNeural", "-15%", "-4Hz"),
    "Character - Energetic RJ (रेडियो जॉकी)": ("edge", "en-IN-PrabhatNeural", "+15%", "+4Hz"),
    
    # 🇮🇳 ओड़िया (100% वर्किंग)
    "Odia - Female 1 (ଓଡ଼ିଆ ମହିଳା - ସ୍ପଷ୍ଟ)": ("gtts", "or", "0%", "0Hz"),
    "Odia - Female 2 (ଓଡ଼ିଆ ମହିଳା - ଧୀର/କାହାଣୀ)": ("gtts_slow", "or", "0%", "0Hz"),
    
    # 🌍 इंग्लिश
    "English - Guy (US Male Narration)": ("edge", "en-US-GuyNeural", "0%", "0Hz"),
    "English - Jenny (US Warm Female)": ("edge", "en-US-JennyNeural", "0%", "0Hz")
}

# 2. ElevenLabs प्रीमियम कैरेक्टर लिस्ट
elevenlabs_voices = {
    "Adam (डीप नरेशन व कहानी)": "pNInz6obpgDQGcFmaJgB",
    "Rachel (शांत व प्रोफेशनल फीमेल)": "21m00Tcm4TlvDq8ikWAM",
    "Antoni (उत्साही मेल कैरेक्टर)": "ErXwobaYiN019PkySvjV",
    "Bella (सॉफ्ट व इमोशनल फीमेल)": "EXAVITQu4vr4xnSDxMaL",
    "Josh (पॉडकास्ट व भारी आवाज)": "TxGEqnHWrfWFTfGW9XjX",
    "Matilda (वार्म स्टोरीटेलर)": "XrExE9yKIg1WjnnlVkGX",
    "Arnold (क्रिस्प व भारी एक्शन आवाज)": "VR6AewLTigWG4xSOukaG",
    "Charlie (कैजुअल मेल बातचीत)": "IKne3meq5aSn9XLyUdCD",
    "Callum (इंटेंस ड्रामा कैरेक्टर)": "N2lVS1w4EtoT3dr4eOWO",
    "Liam (यंग मेल)": "TX3LPaxmHKxFdv7VOQHJ"
}

# UI रेंडरिंग
if engine_choice == "🆓 100% Free & Unlimited (Edge/Google)":
    selected_voice = st.sidebar.selectbox("फ्री आवाज़ चुनें:", list(free_voices.keys()))
    speed_slider = st.sidebar.slider("स्पीड एडजस्ट करें (%):", -50, 50, 0, step=5)
    api_key = None
else:
    api_key = st.sidebar.text_input("ElevenLabs API Key डालें:", type="password", help="elevenlabs.io से अपनी API Key लें")
    selected_voice = st.sidebar.selectbox("ElevenLabs कैरेक्टर चुनें:", list(elevenlabs_voices.keys()))
    speed_slider = 0

# टेक्स्ट इनपुट एरिया
text_input = st.text_area(
    "यहाँ अपना टेक्स्ट लिखें या पेस्ट करें (हिंदी / ଓଡ଼ିଆ / English):",
    height=220,
    placeholder="यहाँ टेक्स्ट दर्ज करें जिसे ऑडियो में बदलना है..."
)

# Edge TTS फंक्शन
async def generate_edge(text, voice_code, rate_str, pitch_str, output_file):
    communicate = edge_tts.Communicate(text, voice_code, rate=rate_str, pitch=pitch_str)
    await communicate.save(output_file)

if st.button("🚀 Generate Audio (MP3)"):
    if not text_input.strip():
        st.error("कृपया पहले कोई टेक्स्ट लिखें।")
    elif engine_choice.startswith("💎") and not api_key:
        st.error("कृपया साइडबार में अपनी ElevenLabs API Key दर्ज करें।")
    else:
        with st.spinner("AI आवाज़ तैयार की जा रही है..."):
            output_audio = "final_voice.mp3"
            try:
                # 1. फ्री इंजन लॉजिक
                if engine_choice.startswith("🆓"):
                    engine_type, voice_code, default_rate, default_pitch = free_voices[selected_voice]
                    
                    # स्पीड कैलकुलेशन
                    base_rate = int(default_rate.replace("%", ""))
                    final_rate = f"{base_rate + speed_slider:+d}%"
                    
                    if engine_type == "gtts":
                        tts = gTTS(text=text_input, lang='or', slow=False)
                        tts.save(output_audio)
                    elif engine_type == "gtts_slow":
                        tts = gTTS(text=text_input, lang='or', slow=True)
                        tts.save(output_audio)
                    else:
                        asyncio.run(generate_edge(text_input, voice_code, final_rate, default_pitch, output_audio))
                
                # 2. ElevenLabs प्रीमियम लॉजिक
                else:
                    voice_id = elevenlabs_voices[selected_voice]
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
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
                        raise Exception(f"{resp.status_code} - {resp.text}")

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
