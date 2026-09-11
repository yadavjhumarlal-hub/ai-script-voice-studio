import streamlit as st
import edge_tts
import asyncio

st.set_page_config(page_title="AI Text to Speech Studio", page_icon="🎙️", layout="centered")

st.title("🎙️ AI Text to Audio Generator")
st.write("अपना टेक्स्ट लिखें और सीधे हाई-क्वालिटी AI आवाज़ (हिंदी / ଓଡ଼ିଆ / English) में ऑडियो बनाएं।")

# आवाज़ के विकल्प
voices = {
    "Hindi - Madhur (Male)": "hi-IN-MadhurNeural",
    "Hindi - Swara (Female)": "hi-IN-SwaraNeural",
    "Odia - Sukant (Male)": "or-IN-SukantNeural",
    "Odia - Subhasini (Female)": "or-IN-SubhasiniNeural",
    "English (India) - Prabhat (Male)": "en-IN-PrabhatNeural",
    "English (India) - Neerja (Female)": "en-IN-NeerjaNeural",
    "English (US) - Jenny (Female)": "en-US-JennyNeural"
}

# साइडबार सेटिंग्स
st.sidebar.header("⚙️ Voice Settings")
selected_voice = st.sidebar.selectbox("आवाज़ चुनें:", list(voices.keys()))
rate = st.sidebar.slider("बोलने की गति (Speed):", min_value=-50, max_value=50, value=0, step=5)
rate_str = f"{rate:+d}%"

# टेक्स्ट इनपुट
text_input = st.text_area(
    "यहाँ अपना टेक्स्ट लिखें या पेस्ट करें:", 
    height=220, 
    placeholder="यहाँ वह टेक्स्ट लिखें जिसे आप ऑडियो में बदलना चाहते हैं..."
)

async def generate_speech(text, voice, rate_val, output_file):
    communicate = edge_tts.Communicate(text, voice, rate=rate_val)
    await communicate.save(output_file)

if st.button("🚀 Generate Audio (MP3)"):
    if not text_input.strip():
        st.error("कृपया पहले कुछ टेक्स्ट दर्ज करें।")
    else:
        with st.spinner("AI आवाज़ तैयार की जा रही है..."):
            voice_id = voices[selected_voice]
            output_audio = "generated_voice.mp3"
            
            try:
                asyncio.run(generate_speech(text_input, voice_id, rate_str, output_audio))
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
