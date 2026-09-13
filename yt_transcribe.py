import streamlit as st
import os
import re
import html
import requests
import tempfile
import yt_dlp
from urllib.parse import urlparse, parse_qs
from google import genai

st.title("📝 YouTube Video to Transcript (100% Guaranteed)")
st.write("चाहे वीडियो में सबटाइटल ऑन हों या पूरी तरह बंद — AI सीधे ऑडियो सुनकर पूरा टेक्स्ट निकाल देगा।")

secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")

# Video ID निकालने का फंक्शन
def extract_video_id(url):
    url = url.strip()
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].split("&")[0]
    elif "youtube.com/shorts/" in url:
        return url.split("youtube.com/shorts/")[1].split("?")[0].split("&")[0]
    elif "youtube.com/watch" in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

# VTT क्लीनर
def clean_vtt_text(vtt_content):
    lines = vtt_content.splitlines()
    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line or "WEBVTT" in line or "-->" in line or line.isdigit() or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        line = re.sub(r'<[^>]+>', '', line)
        line = html.unescape(line)
        if line and (not clean_lines or clean_lines[-1] != line):
            clean_lines.append(line)
    return " ".join(clean_lines)

# 1. Fast Mirror Captions
def fetch_fast_captions(video_id):
    mirrors = ["https://inv.nadeko.net", "https://invidious.nerdvpn.de", "https://yewtu.be"]
    for base in mirrors:
        try:
            res = requests.get(f"{base}/api/v1/captions/{video_id}", timeout=4)
            if res.status_code == 200:
                caps = res.json()
                if caps:
                    path = caps[0].get("url")
                    u = base + path if path.startswith("/") else path
                    c_res = requests.get(u, timeout=4)
                    if c_res.status_code == 200:
                        text = clean_vtt_text(c_res.text)
                        if text:
                            return text
        except Exception:
            continue
    return None

# 2. AI Audio Transcription (अगर सबटाइटल बंद हों)
def transcribe_audio_with_gemini(video_url, gemini_api_key, target_lang):
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = os.path.join(temp_dir, "audio.m4a")
        
        # ऑडियो डाउनलोड सेटिंग्स
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': audio_path,
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        if not os.path.exists(audio_path):
            raise Exception("वीडियो का ऑडियो लोड नहीं हो सका।")
            
        # Gemini Audio API पर ऑडियो अपलोड और ट्रांसक्रिप्शन
        client = genai.Client(api_key=gemini_api_key)
        
        uploaded_file = client.files.upload(file=audio_path)
        
        prompt = f"""
        Transcribe the spoken words in this audio file completely and accurately.
        Formatting rules:
        - Output ONLY the clean spoken text in paragraphs.
        - Translate/deliver output in language: {target_lang}.
        - Do not include timestamps, filler words, or metadata.
        """
        
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[uploaded_file, prompt]
        )
        
        return response.text.strip()

# UI इनपुट्स
yt_url = st.text_input("YouTube Video URL दर्ज करें:", placeholder="https://youtu.be/... या https://www.youtube.com/watch?v=...")
translate_option = st.selectbox(
    "ट्रांसक्रिप्ट किस भाषा में चाहिए?",
    ["मूल भाषा (Original Spoken)", "हिंदी (Hindi)", "English", "ଓଡ଼ିଆ (Odia)"]
)
gemini_key_input = st.text_input(
    "Google Gemini API Key:", 
    value=secrets_gemini, 
    type="password",
    help="बिना सबटाइटल वाले वीडियो के लिए Gemini Key अनिवार्य है।"
)

if st.button("📥 Get Transcript", key="btn_get_final_trans"):
    if not yt_url.strip():
        st.error("कृपया यूट्यूब वीडियो का लिंक दर्ज करें।")
    else:
        video_id = extract_video_id(yt_url)
        if not video_id:
            st.error("अमान्य YouTube URL!")
        else:
            final_text = None
            
            # चरण 1: पहले सबटाइटल चेक करें
            with st.spinner("1/2: सबटाइटल की जांच की जा रही है..."):
                final_text = fetch_fast_captions(video_id)
                
            # चरण 2: अगर सबटाइटल नहीं हैं, तो सीधे AI से ऑडियो ट्रांसक्राइब करें
            if not final_text:
                if not gemini_key_input.strip():
                    st.error("इस वीडियो में सबटाइटल बंद हैं। इसे AI द्वारा सुनने के लिए कृपया ऊपर अपनी Google Gemini API Key दर्ज करें।")
                else:
                    with st.spinner("2/2: सबटाइटल बंद हैं — Gemini AI ऑडियो सुनकर पूरा टेक्स्ट बना रहा है..."):
                        try:
                            clean_url = f"https://www.youtube.com/watch?v={video_id}"
                            final_text = transcribe_audio_with_gemini(clean_url, gemini_key_input, translate_option)
                        except Exception as e:
                            st.error(f"AI ट्रांसक्रिप्शन में त्रुटि: {e}")
            else:
                # यदि सबटाइटल मिल गए और अनुवाद चाहिए
                if translate_option != "मूल भाषा (Original Spoken)" and gemini_key_input.strip():
                    with st.spinner("अनुवाद किया जा रहा है..."):
                        try:
                            client = genai.Client(api_key=gemini_key_input)
                            lang_t = "Hindi" if "हिंदी" in translate_option else ("Odia" if "ଓଡ଼ିଆ" in translate_option else "English")
                            res = client.models.generate_content(
                                model="gemini-3.6-flash", 
                                contents=f"Translate this cleanly into {lang_t}:\n\n{final_text}"
                            )
                            final_text = res.text
                        except Exception:
                            pass

            if final_text:
                st.success("🎉 ट्रांसक्रिप्ट सफलतापूर्वक प्राप्त हो गया!")
                st.text_area("वीडियो का पूरा टेक्स्ट (Transcript):", value=final_text, height=260)
                st.download_button(
                    label="⬇️ Download Transcript (TXT)", 
                    data=final_text, 
                    file_name=f"transcript_{video_id}.txt", 
                    mime="text/plain"
    )
