import streamlit as st
import edge_tts
import asyncio
from gtts import gTTS
import os

st.set_page_config(page_title="AI Voice Studio", page_icon="🎙️", layout="centered")

st.title("🎙️ AI Voice Studio")
st.write("हिंदी (6 अलग अंदाज़), ओड़िया और इंग्लिश की 100% वर्किंग AI आवाज़ें।")

# 100% टेस्टेड और बिना एरर वाली आवाज़ों की सूची
voice_profiles = {
    # 🇮🇳 हिंदी की 6 अलग-अलग आवाज़ें
    "1. Hindi - Madhur (कहानी / गंभीर पुरुष)": ("edge", "hi-IN-MadhurNeural", "+0%", "+0Hz"),
    "2. Hindi - Swara (समाचार / स्पष्ट महिला)": ("edge", "hi-IN-SwaraNeural", "+0%", "+0Hz"),
    "3. Hindi - Deep Villain / Documentary (गहरी भारी आवाज़ / पुरुष)": ("edge", "hi-IN-MadhurNeural", "-10%", "-15Hz"),
    "4. Hindi - Energetic Storyteller (उत्साही कहानीकार / पुरुष)": ("edge", "hi-IN-MadhurNeural", "+12%", "+4Hz"),
    "5. Hindi - Soft Calm Female (शांत व मधुर / महिला)": ("edge", "hi-IN-SwaraNeural", "-8%", "-3Hz"),
    "6. Hindi - Young / Fast Narration (तेज़ व युवा अंदाज़)": ("edge", "hi-IN-SwaraNeural", "+15%", "+10Hz"),
    
    # 🇮🇳 ओड़िया आवाज़ें (100% वर्किंग)
    "7. Odia - Female 1 (ଓଡ଼ିଆ ମହିଳା - ସାଧାରଣ)": ("gtts", "or", "normal"),
    "8. Odia - Female 2 (ଓଡ଼ିଆ ମହିଳା - ଧୀର/କାହାଣୀ)": ("gtts", "or", "slow"),
    
    # 🌍 इंग्लिश आवाज़ें
    "9. English - Guy (US Narration Male)": ("edge", "en-US-GuyNeural", "+0%", "+0Hz"),
    "10. English - Jenny (US Professional Female)": ("edge", "en-US-JennyNeural", "+0%", "+0Hz")
}

# साइडबार
st.sidebar.header("⚙️ वॉयस सेटिंग्स")
selected_name = st.sidebar.selectbox("आवाज़ (Voice) चुनें:", list(voice_profiles.keys()))
profile = voice_profiles[selected_name]

# अतिरिक्त स्पीड स्लाइडर
speed_adjust = st.sidebar.slider("स्पीड और घटाएं/बढ़ाएं (%):", -30, 30, 0, step=5)

# टेक्स्ट इनपुट
text_input = st.text_area(
    "यहाँ अपना टेक्स्ट लिखें या पेस्ट करें (हिंदी / ଓଡ଼ିଆ / English):",
    height=200,
    placeholder="यहाँ टेक्स्ट लिखें जिसे आप ऑडियो में बदलना चाहते हैं..."
)

# Edge TTS फंक्शन
async def generate_edge(text, voice_code, rate_str, pitch_str, output_file):
    communicate = edge_tts.Communicate(text, voice_code, rate=rate_str, pitch=pitch_str)
    await communicate.save(output_file)

if st.button("🚀 Generate Audio (MP3)"):
    if not text_input.strip():
        st.error("कृपया पहले कोई टेक्स्ट लिखें।")
    else:
        with st.spinner("AI आवाज़ तैयार की जा रही है..."):
            output_audio = "voice_output.mp3"
            
            # पुरानी फ़ाइल हटाना
            if os.path.exists(output_audio):
                os.remove(output_audio)
                
            try:
                engine = profile[0]
                
                # ओड़िया इंजन (gTTS)
                if engine == "gtts":
                    is_slow = (profile[2] == "slow") or (speed_adjust < 0)
                    tts = gTTS(text=text_input, lang="or", slow=is_slow)
                    tts.save(output_audio)
                
                # हिंदी और इंग्लिश इंजन (Edge-TTS)
                else:
                    voice_code = profile[1]
                    base_rate = int(profile[2].replace("%", ""))
                    final_rate = f"{base_rate + speed_adjust:+d}%"
                    pitch_val = profile[3]
                    
                    asyncio.run(generate_edge(text_input, voice_code, final_rate, pitch_val, output_audio))

                st.success("🎉 ऑडियो सफलतापूर्वक तैयार हो गया!")
                st.audio(output_audio, format="audio/mp3")
                
                with open(output_audio, "rb") as file:
                    st.download_button(
                        label="⬇️ Download MP3",
                        data=file,
                        file_name="ai_audio.mp3",
                        mime="audio/mp3"
                    )
            except Exception as e:
                st.error(f"त्रुटि: {e}")
                
