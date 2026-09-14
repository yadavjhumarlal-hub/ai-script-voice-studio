import streamlit as st
import edge_tts
import asyncio
import requests
from google import genai
import os

st.set_page_config(page_title="Universal All-in-One Voice Studio", page_icon="🎙️", layout="centered")

st.title("🎙️ Universal AI Voice Studio")
st.write("100% Free न्यूरल आवाज़ें + ElevenLabs क्लोन स्टाइल + Google Gemini AI + ElevenLabs Official API")

# Secrets से सुरक्षित रूप से API Keys लोड करना
secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")
secrets_eleven = st.secrets.get("ELEVEN_API_KEY", "")

# साइडबार इंजन सेलेक्टर
st.sidebar.header("⚙️ इंजन व आवाज़ सेटिंग्स")
engine_choice = st.sidebar.radio(
    "वॉयस इंजन चुनें:",
    (
        "🆓 100% Free & Unlimited (ElevenLabs Clone & Neural)",
        "✨ Google Gemini Engine (Exact Text AI Speech)",
        "💎 ElevenLabs Original Characters (Official API)"
    )
)

# 1. फ्री आवाज़ों का विस्तृत कैटलॉग (10 क्लासिक + 10 ElevenLabs क्लोन स्टाइल + 3 इंग्लिश)
free_voices = {
    # --- ElevenLabs स्टाइल फ्री डीप / सिनेमैटिक कैरेक्टर्स (हिंदी में) ---
    "💎 ElevenLabs Style - Adam (डीप भारी बेस / पॉडकास्ट / Male)": ("hi-IN-MadhurNeural", "-16Hz", "-6%"),
    "💎 ElevenLabs Style - Josh (भारी विलेन / गहरी आवाज़ / Male)": ("hi-IN-MadhurNeural", "-20Hz", "-8%"),
    "💎 ElevenLabs Style - Antoni (ऊर्जावान / मोटिवेशनल / Male)": ("hi-IN-MadhurNeural", "+4Hz", "+6%"),
    "💎 ElevenLabs Style - Sam (शांत कथावाचक / गहरा ठहराव / Male)": ("hi-IN-MadhurNeural", "-10Hz", "-10%"),
    "💎 ElevenLabs Style - Arnold (सिनेमैटिक ट्रेलर भारी / Male)": ("hi-IN-MadhurNeural", "-24Hz", "-12%"),
    "💎 ElevenLabs Style - Clyde (हॉरर / सस्पेंस विलेन / Male)": ("hi-IN-MadhurNeural", "-18Hz", "-4%"),
    "💎 ElevenLabs Style - Rachel (स्मार्ट व साफ़ नैरेटर / Female)": ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    "💎 ElevenLabs Style - Matilda (इमोशनल कहानीकार / Female)": ("hi-IN-SwaraNeural", "-6Hz", "-6%"),
    "💎 ElevenLabs Style - Bella (सॉफ्ट और मधुर / Female)": ("hi-IN-SwaraNeural", "-2Hz", "-8%"),
    "💎 ElevenLabs Style - Freya (तेज़ और उत्साही न्यूज़ / Female)": ("hi-IN-SwaraNeural", "+4Hz", "+12%"),

    # --- क्लासिक 10 हिंदी आवाज़ें ---
    "1. Hindi - Madhur (कहानी / Male)": ("hi-IN-MadhurNeural", "+0Hz", "+0%"),
    "2. Hindi - Swara (समाचार / Female)": ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    "3. Hindi - Deep Documentary (डॉक्यूमेंट्री भारी / Male)": ("hi-IN-MadhurNeural", "-12Hz", "-5%"),
    "4. Hindi - Energetic RJ (उत्साही आरजे / Male)": ("hi-IN-MadhurNeural", "+8Hz", "+12%"),
    "5. Hindi - Calm Meditation (शांत व ध्यान / Female)": ("hi-IN-SwaraNeural", "-8Hz", "-10%"),
    "6. Hindi - Fast Reels (शॉर्ट्स / तेज़ रील्स / Female)": ("hi-IN-SwaraNeural", "+6Hz", "+15%"),
    "7. Hindi - Motivational (जोशीला भाषण / Male)": ("hi-IN-MadhurNeural", "+4Hz", "+8%"),
    "8. Hindi - Soft Storyteller (भावुक स्टोरी / Female)": ("hi-IN-SwaraNeural", "-4Hz", "-6%"),
    "9. Hindi - Heavy Villain (विलेन बेस / Male)": ("hi-IN-MadhurNeural", "-18Hz", "-8%"),
    "10. Hindi - Corporate (प्रोफेशनल वॉइस / Female)": ("hi-IN-SwaraNeural", "+2Hz", "+4%"),
    
    # --- इंग्लिश आवाज़ें ---
    "💎 English - Adam Clone (Deep US Narration Male)": ("en-US-GuyNeural", "-14Hz", "-6%"),
    "11. English - Guy Natural (US Male)": ("en-US-GuyNeural", "+0Hz", "+0%"),
    "12. English - Jenny Natural (US Female)": ("en-US-JennyNeural", "+0Hz", "+0%")
}

# 2. ElevenLabs आधिकारिक कैरेक्टर (Official API)
elevenlabs_voices = {
    "Adam (डीप नरेशन / भारी मेल)": "pNInz6obpgDQGcFmaJgB",
    "Rachel (प्रोफेशनल / शांत फीमेल)": "21m00Tcm4TlvDq8ikWAM",
    "Antoni (उत्साही / ऊर्जावान मेल)": "ErXwobaYiN019PkySvjV",
    "Bella (सॉफ्ट नैरेटर / फीमेल)": "EXAVITQu4vr4xnSDxMaL",
    "Josh (पॉडकास्ट / भारी बेस मेल)": "TxGEqnHWrfWFTfGW9XjX",
    "Matilda (स्टोरीटेलिंग / भावुक फीमेल)": "XrExE9yKIg1WjnnlVkGX",
    "Sam (गंभीर नैरेटर / मेल)": "yoZ06aMxZJJ28mfd3POQ",
    "Clyde (सस्पेंस विलेन / मेल)": "2EiwWnXFnvU5JabPnv8n"
}

speed_adjust = 0
pitch_adjust = 0
api_key = ""

# साइडबार ऑप्शंस
if engine_choice.startswith("🆓"):
    selected_voice = st.sidebar.selectbox("फ्री आवाज़ चुनें:", list(free_voices.keys()))
    speed_adjust = st.sidebar.slider("स्पीड एडजस्ट करें (%):", -30, 30, 0, step=5)
    pitch_adjust = st.sidebar.slider("बेस / पिच एडजस्ट करें (Pitch Hz):", -24, 24, 0, step=2)
    
elif engine_choice.startswith("✨"):
    api_key = st.sidebar.text_input("Google Gemini API Key:", value=secrets_gemini, type="password")
    gemini_mode = st.sidebar.radio(
        "Gemini मोड चुनें:",
        ["1. केवल मेरा दिया गया टेक्स्ट ही बोलें (Exact Verbatim)", "2. टेक्स्ट को सुधारकर बोलें (Enhance Script)"]
    )
    if "सुधारकर" in gemini_mode:
        gemini_tone = st.sidebar.selectbox(
            "स्क्रिप्ट का अंदाज़:", 
            ["कहानीकार (Storyteller)", "उत्साही (Excited & Fast)", "शांत व गंभीर (Calm & Documentary)"]
        )
    else:
        gemini_tone = "Exact"
        
    selected_voice = st.sidebar.selectbox(
        "आउटपुट आवाज़ कैरेक्टर:", 
        [
            "💎 Adam Style (Deep Male)", 
            "💎 Josh Style (Heavy Villain Male)", 
            "💎 Rachel Style (Smart Female)", 
            "💎 Matilda Style (Storyteller Female)",
            "Hindi - Madhur (Standard Male)", 
            "Hindi - Swara (Standard Female)"
        ]
    )
    
else:
    api_key = st.sidebar.text_input("ElevenLabs API Key:", value=secrets_eleven, type="password")
    selected_voice = st.sidebar.selectbox("ElevenLabs कैरेक्टर चुनें:", list(elevenlabs_voices.keys()))

# टेक्स्ट इनपुट
text_input = st.text_area(
    "यहाँ अपना टेक्स्ट लिखें या पेस्ट करें (हिंदी / English / ଓଡ଼ିଆ):",
    height=220,
    placeholder="यहाँ अपनी यूट्यूब स्क्रिप्ट, रील्स या कहानी का टेक्स्ट दर्ज करें..."
)

# Edge TTS जनरेशन हेल्पर
async def generate_edge_speech(text, base_code, pitch_str, rate_str, output_filename):
    communicate = edge_tts.Communicate(text, base_code, pitch=pitch_str, rate=rate_str)
    await communicate.save(output_filename)

if st.button("🚀 Generate Studio Audio (MP3)", key="btn_run_voice"):
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
                # 1. फ्री न्यूरल इंजन (100% Free ElevenLabs Clones)
                # ----------------------------------------------------
                if engine_choice.startswith("🆓"):
                    base_code, def_pitch, def_rate = free_voices[selected_voice]
                    calc_pitch = int(def_pitch.replace("Hz", "")) + pitch_adjust
                    calc_rate = int(def_rate.replace("%", "")) + speed_adjust
                    final_p = f"{calc_pitch:+d}Hz"
                    final_r = f"{calc_rate:+d}%"
                    asyncio.run(generate_edge_speech(text_input, base_code, final_p, final_r, output_audio))

                # ----------------------------------------------------
                # 2. Google Gemini AI इंजन (Exact Text Only - No Extra Garbage)
                # ----------------------------------------------------
                elif engine_choice.startswith("✨"):
                    if gemini_tone == "Exact":
                        # बिना किसी छेड़छाड़ के सीधे आपका टेक्स्ट बोलेगा
                        target_text = text_input.strip()
                    else:
                        client = genai.Client(api_key=api_key)
                        prompt = f"""
                        Task: Polish the phrasing of the input text into a {gemini_tone} tone.
                        STRICT RULES:
                        - Output ONLY the polished script itself.
                        - Do NOT add any introductory words, notes, explanations, or conclusions.
                        - Do NOT add dialogue tags or scene descriptions.
                        Input Text: {text_input}
                        """
                        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
                        target_text = res.text.strip()
                    
                    # वॉयस ट्यूनिंग मैपिंग
                    if "Adam" in selected_voice:
                        v_code, p_str, r_str = "hi-IN-MadhurNeural", "-16Hz", "-6%"
                    elif "Josh" in selected_voice:
                        v_code, p_str, r_str = "hi-IN-MadhurNeural", "-20Hz", "-8%"
                    elif "Rachel" in selected_voice:
                        v_code, p_str, r_str = "hi-IN-SwaraNeural", "+0Hz", "+0%"
                    elif "Matilda" in selected_voice:
                        v_code, p_str, r_str = "hi-IN-SwaraNeural", "-6Hz", "-6%"
                    elif "Madhur" in selected_voice:
                        v_code, p_str, r_str = "hi-IN-MadhurNeural", "+0Hz", "+0%"
                    else:
                        v_code, p_str, r_str = "hi-IN-SwaraNeural", "+0Hz", "+0%"
                        
                    asyncio.run(generate_edge_speech(target_text, v_code, p_str, r_str, output_audio))

                # ----------------------------------------------------
                # 3. ElevenLabs आधिकारिक इंजन (Official API)
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
                        file_name="ultra_ai_voice.mp3",
                        mime="audio/mp3"
                    )

            except Exception as e:
                st.error(f"त्रुटि: {e}")
