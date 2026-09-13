import streamlit as st
import os
import re
import html
import requests
from urllib.parse import urlparse, parse_qs
from google import genai
from google.genai import types

st.title("📝 YouTube Video to Transcript (Cloud Bypass)")
st.write("Google Gemini AI सीधे YouTube वीडियो को प्रोसेस करके पूरा सटीक टेक्स्ट निकालता है।")

secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")

# 100% सटीक Video ID निकालने का फंक्शन
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

# Fast Mirror Captions
def fetch_fast_captions(video_id):
    mirrors = ["https://inv.nadeko.net", "https://invidious.nerdvpn.de", "https://yewtu.be", "https://invidious.jing.rocks"]
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
    help="aistudio.google.com से मुफ़्त Key लें"
)

if st.button("📥 Get Transcript", key="btn_get_transcript_direct"):
    if not yt_url.strip():
        st.error("कृपया यूट्यूब वीडियो का लिंक दर्ज करें।")
    else:
        video_id = extract_video_id(yt_url)
        if not video_id:
            st.error("अमान्य YouTube URL!")
        else:
            final_text = None
            
            # चरण 1: पहले फ़ास्ट कैप्शन चेक करें
            with st.spinner("1/2: सबटाइटल की जांच की जा रही है..."):
                final_text = fetch_fast_captions(video_id)
                
            # चरण 2: अगर सबटाइटल नहीं मिले या अनुवाद चाहिए, तो सीधे Gemini AI इंजन का उपयोग करें
            if not final_text:
                if not gemini_key_input.strip():
                    st.error("कृपया अपनी Google Gemini API Key दर्ज करें।")
                else:
                    with st.spinner("2/2: Gemini AI सीधे YouTube वीडियो का ऑडियो सुनकर ट्रांसक्रिप्ट बना रहा है..."):
                        try:
                            clean_yt_link = f"https://www.youtube.com/watch?v={video_id}"
                            client = genai.Client(api_key=gemini_key_input)
                            
                            lang_instruction = "in its original spoken language" if "Original" in translate_option else f"translated into {translate_option}"
                            
                            prompt = f"""
                            You are an expert audio/video transcriber. Listen carefully to this YouTube video: {clean_yt_link}
                            Task:
                            1. Transcribe the entire speech spoken in this video {lang_instruction}.
                            2. Output ONLY the clean spoken text/paragraphs.
                            3. Do not include introductory notes, timestamps, or summary headers.
                            """
                            
                            # Gemini 2.5 Flash / Flash Native Multimodal
                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=prompt
                            )
                            final_text = response.text.strip()
                        except Exception as e:
                            st.error(f"AI ट्रांसक्रिप्शन में त्रुटि: {e}")
            else:
                # यदि सबटाइटल मिल गए और भाषा अनुवाद चाहिए
                if translate_option != "मूल भाषा (Original Spoken)" and gemini_key_input.strip():
                    with st.spinner("अनुवाद किया जा रहा है..."):
                        try:
                            client = genai.Client(api_key=gemini_key_input)
                            lang_t = "Hindi" if "हिंदी" in translate_option else ("Odia" if "ଓଡ଼ିଆ" in translate_option else "English")
                            res = client.models.generate_content(
                                model="gemini-2.5-flash", 
                                contents=f"Translate this text accurately and naturally into {lang_t}:\n\n{final_text}"
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
