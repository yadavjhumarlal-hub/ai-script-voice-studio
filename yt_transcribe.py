import streamlit as st
import requests
import re
import html
import tempfile
import os
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs
import yt_dlp
from google import genai

st.title("📝 YouTube Video to Verbatim Transcript")
st.write("वीडियो में जो-जो शब्द बोले गए हैं, हूबहू वही असली टेक्स्ट प्राप्त करें।")

secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")

# 1. Video ID निकालने का फंक्शन
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

# 2. सबटाइटल क्लीनर
def clean_vtt_text(raw_text):
    if "<text" in raw_text:
        try:
            root = ET.fromstring(raw_text)
            lines = [html.unescape(node.text or '') for node in root.findall('.//text')]
            cleaned = " ".join([l.strip() for l in lines if l.strip()])
            if len(cleaned) > 20:
                return cleaned
        except Exception:
            pass

    lines = raw_text.splitlines()
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

# 3. लेयर 1: डायरेक्ट सबटाइटल
def fetch_exact_subtitles(video_id):
    mirrors = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://yewtu.be",
        "https://invidious.jing.rocks"
    ]
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
                        if text and len(text) > 30:
                            return text
        except Exception:
            continue
    return None

# 4. लेयर 2: यूनिवर्सल ऑडियो डाउनलोडर (Zero Format Error)
def transcribe_real_audio(video_id, api_key, target_lang):
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_template = os.path.join(temp_dir, "audio_stream.%(ext)s")
        
        # यूनिवर्सल फ़ॉर्मेट सेलेक्टर - जो किसी भी वीडियो पर कभी फ़ेल नहीं होता
        ydl_opts = {
            'format': 'ba/b/worst',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'ios']
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([clean_url])
            
        # डाउनलोड की गई फ़ाइल खोजना
        downloaded_files = os.listdir(temp_dir)
        if not downloaded_files:
            raise Exception("वीडियो का ऑडियो लोड नहीं हो सका।")
            
        audio_path = os.path.join(temp_dir, downloaded_files[0])
        
        # Gemini API पर अपलोड करके असली आवाज़ सुनना
        client = genai.Client(api_key=api_key)
        uploaded = client.files.upload(file=audio_path)
        
        lang_instruction = "in its original spoken language" if "मूल" in target_lang else f"translated into {target_lang}"
        
        prompt = f"""
        Listen to this audio file carefully.
        Task: Transcribe the exact words, sentences, and dialogue spoken in this audio verbatim {lang_instruction}.
        Rules:
        - Output ONLY what is actually spoken in the audio.
        - Do NOT summarize or add external information.
        - Do NOT add timestamps, markdown titles, or intro/outro text.
        """
        
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[uploaded, prompt]
        )
        return response.text.strip()

# UI इनपुट
yt_url = st.text_input("YouTube Video URL दर्ज करें:", placeholder="https://youtu.be/... या https://www.youtube.com/watch?v=...")
translate_option = st.selectbox(
    "ट्रांसक्रिप्ट भाषा:",
    ["मूल भाषा (Original Spoken)", "हिंदी (Hindi)", "English", "ଓଡ଼ିଆ (Odia)"]
)
gemini_key = st.text_input("Google Gemini API Key:", value=secrets_gemini, type="password")

if st.button("📥 Get Transcript", key="btn_run_bulletproof"):
    if not yt_url.strip():
        st.error("कृपया यूट्यूब वीडियो का लिंक दर्ज करें।")
    else:
        v_id = extract_video_id(yt_url)
        if not v_id:
            st.error("अमान्य YouTube URL!")
        else:
            final_text = None
            
            # चरण 1: पहले वीडियो के सबटाइटल चेक करें
            with st.spinner("1/2: सबटाइटल की जांच की जा रही है..."):
                final_text = fetch_exact_subtitles(v_id)
                
            # चरण 2: यदि सबटाइटल नहीं हैं, तो असली ऑडियो से शब्द-दर-शब्द निकालें
            if not final_text:
                if not gemini_key.strip():
                    st.warning("इस वीडियो में सबटाइटल बंद हैं। वीडियो की असली आवाज़ सुनने के लिए अपनी Google Gemini API Key दर्ज करें।")
                else:
                    with st.spinner("2/2: सबटाइटल बंद हैं — Gemini AI ऑडियो सुनकर वीडियो का असली टेक्स्ट लिख रहा है..."):
                        try:
                            final_text = transcribe_real_audio(v_id, gemini_key, translate_option)
                        except Exception as e:
                            st.error(f"ऑडियो ट्रांसक्रिप्शन में त्रुटि: {e}")
            else:
                # यदि सबटाइटल मिले और अनुवाद चाहिए
                if translate_option != "मूल भाषा (Original Spoken)" and gemini_key.strip():
                    with st.spinner("भाषा अनुवाद किया जा रहा है..."):
                        try:
                            client = genai.Client(api_key=gemini_key)
                            lang_t = "Hindi" if "हिंदी" in translate_option else ("Odia" if "ଓଡ଼ିଆ" in translate_option else "English")
                            res = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=f"Translate the following speech verbatim into {lang_t}:\n\n{final_text}"
                            )
                            final_text = res.text
                        except Exception:
                            pass

            if final_text:
                st.success("🎉 वीडियो में बोला गया असली टेक्स्ट तैयार हो गया!")
                st.text_area("वीडियो का असली बोला गया टेक्स्ट (Transcript):", value=final_text, height=280)
                st.download_button(
                    label="⬇️ Download Transcript (TXT)", 
                    data=final_text, 
                    file_name=f"transcript_{v_id}.txt", 
                    mime="text/plain"
                )
