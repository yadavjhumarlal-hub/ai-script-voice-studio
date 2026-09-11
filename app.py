import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
import edge_tts
import asyncio
import re

st.set_page_config(page_title="Auto AI Script & Voice Studio", page_icon="🎙️", layout="wide")

st.title("🎬 YouTube Video ➔ Script & Voiceover Generator")
st.write("YouTube लिंक डालें — AI स्क्रिप्ट तैयार करेगा और साथ ही उसकी आवाज़ (Audio) भी बना देगा।")

# साइडबार सेटिंग्स
st.sidebar.header("⚙️ Settings")
api_key = st.sidebar.text_input("Gemini API Key दर्ज करें:", type="password")

# ओड़िया और अन्य भाषाओं की आवाज़ें
voices = {
    "Hindi - Madhur (Male)": "hi-IN-MadhurNeural",
    "Hindi - Swara (Female)": "hi-IN-SwaraNeural",
    "Odia - Sukant (Male)": "or-IN-SukantNeural",
    "Odia - Subhasini (Female)": "or-IN-SubhasiniNeural",
    "English (India) - Prabhat (Male)": "en-IN-PrabhatNeural",
    "English (India) - Neerja (Female)": "en-IN-NeerjaNeural",
    "English (US) - Jenny (Female)": "en-US-JennyNeural"
}
selected_voice = st.sidebar.selectbox("ऑडियो के लिए आवाज़ चुनें:", list(voices.keys()))

def extract_video_id(url):
    pattern = r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

async def generate_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

video_url = st.text_input("YouTube Video URL पेस्ट करें:")
target_lang = st.selectbox("स्क्रिप्ट किस भाषा में चाहिए?", ["हिंदी (Hindi)", "ଓଡ଼ିଆ (Odia)", "English"])
tone = st.selectbox("स्क्रिप्ट का प्रकार चुनें:", ["YouTube Video Script", "Shorts/Reels (Fast & Punchy)", "Summary Explanation"])

if st.button("🚀 Generate Script & Audio"):
    if not api_key:
        st.error("कृपया पहले साइडबार में अपनी Gemini API Key डालें।")
    elif not video_url:
        st.error("कृपया YouTube वीडियो का लिंक डालें।")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("अमान्य YouTube लिंक।")
        else:
            try:
                with st.spinner("1/3: वीडियो से ट्रांसक्रिप्ट निकाली जा रही है..."):
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi', 'en', 'or'])
                    full_text = " ".join([item['text'] for item in transcript_data])

                with st.spinner("2/3: AI नई स्क्रिप्ट लिख रहा है..."):
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    नीचे दिए गए YouTube वीडियो ट्रांसक्रिप्ट को समझें और इसे {target_lang} भाषा में एक बेहतरीन {tone} के रूप में लिखें:
                    
                    मूल ट्रांसक्रिप्ट:
                    {full_text}
                    
                    निर्देश:
                    1. भाषा पूरी तरह शुद्ध और स्वाभाविक {target_lang} होनी चाहिए।
                    2. बिना किसी गैर-ज़रूरी चिन्ह (*, #) के ऐसा साफ़ टेक्स्ट लिखें जिसे वॉइसओवर में सीधे पढ़ा जा सके।
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    generated_script = response.text

                with st.spinner("3/3: AI आवाज़ (Voiceover) तैयार की जा रही है..."):
                    voice_id = voices[selected_voice]
                    audio_path = "output_voice.mp3"
                    asyncio.run(generate_speech(generated_script, voice_id, audio_path))

                st.success("🎉 स्क्रिप्ट और ऑडियो दोनों सफलतापूर्वक तैयार हो गए!")

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📝 जनरेट की गई स्क्रिप्ट")
                    st.text_area("स्क्रिप्ट:", value=generated_script, height=300)

                with col2:
                    st.subheader("🔊 AI वॉइसओवर")
                    st.audio(audio_path, format="audio/mp3")
                    with open(audio_path, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Audio (MP3)",
                            data=file,
                            file_name="generated_voiceover.mp3",
                            mime="audio/mp3"
                        )

            except Exception as e:
                st.error(f"त्रुटि: {e} (जाँचें कि वीडियो में कैप्शन्स ऑन हैं या नहीं)")
  
