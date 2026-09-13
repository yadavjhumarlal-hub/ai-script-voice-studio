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
st.write("वीडियो में जो-जो बोला गया है, हूबहू वही असली टेक्स्ट प्राप्त करें।")

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

# 2. VTT / सबटाइटल क्लीनर
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

# 3. लेयर 1: असली सबटाइटल फेच करना (Verbatim Captions)
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

# 4. लेयर 2: असली ऑडियो सुनकर ट्रांसक्राइब करना (Zero Hallucination)
def transcribe_real_audio(video_id, api_key, target_lang):
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_file = os.path.join(temp_dir, "real_audio.m4a")
        
        # 403 Forbidden को बाईपास करने वाली विशेष Android Client सेटिंग्स
        ydl_opts = {
            'format': 'ba/b[ext=m4a]/ba[ext=m4a]',
            'outtmpl': audio_file,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([clean_url])
            
        if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
            raise Exception("वीडियो का ऑडियो प्राप्त नहीं हो सका।")
            
        client = genai.Client(api_key=api_key)
        uploaded = client.files.upload(file=audio_file)
        
        lang_instruction = "in its original spoken language" if "मूल" in target_lang else f"translated into {target_lang}"
        
        prompt = f"""
        Listen to this audio file carefully.
        Task: Transcribe the exact spoken words and dialogue verbatim {lang_instruction}.
        Rules:
        - Output ONLY the exact speech/words spoken in the audio.
        - Do NOT summarize or invent text.
        - Do NOT add timestamps or headers.
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

if st.button("📥 Get Transcript", key="btn_run_verbatim"):
    if not yt_url.strip():
        st.error("कृपया यूट्यूब वीडियो का लिंक दर्ज करें।")
    else:
        v_id = extract_video_id(yt_url)
        if not v_id:
            st.error("अमान्य YouTube URL!")
        else:
            final_text = None
            
            # चरण 1: पहले वीडियो के आधिकारिक सबटाइटल चेक करें
            with st.spinner("1/2: आधिकारिक सबटाइटल से असली टेक्स्ट लोड किया जा रहा है..."):
                final_text = fetch_exact_subtitles(v_id)
                
            # चरण 2: यदि सबटाइटल नहीं हैं, तो असली ऑडियो सुनकर ट्रांसक्राइब करें
            if not final_text:
                if not gemini_key.strip():
                    st.warning("इस वीडियो में सबटाइटल बंद हैं। वीडियो का असली ऑडियो सुनने के लिए कृपया Google Gemini API Key दर्ज करें।")
                else:
                    with st.spinner("2/2: सबटाइटल बंद हैं — Gemini 3.6 असली ऑडियो सुनकर शब्द-दर-शब्द लिख रहा है..."):
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
                            lang_t = "Hindi" if "हिंदी" in translate_option else ("Odia" if "ଓଡ଼िଆ" in translate_option else "English")
                            res = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=f"Translate the following speech verbatim into {lang_t}:\n\n{final_text}"
                            )
                            final_text = res.text
                        except Exception:
                            pass

            if final_text:
                st.success("🎉 वीडियो में बोला गया असली टेक्स्ट तैयार हो गया!")
                st.text_area("वीडियो का असली बोला गया टेक्स्ट (Verbatim Transcript):", value=final_text, height=280)
                st.download_button(
                    label="⬇️ Download Transcript (TXT)", 
                    data=final_text, 
                    file_name=f"transcript_{v_id}.txt", 
                    mime="text/plain"
                )
