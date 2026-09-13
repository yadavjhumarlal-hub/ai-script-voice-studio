import streamlit as st
import requests
import re
import html
import json
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs
from google import genai

st.title("📝 YouTube Video to Transcript")
st.write("बिना किसी कोटा एरर या IP ब्लॉक के किसी भी यूट्यूब वीडियो का पूरा टेक्स्ट निकालें।")

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

# VTT / XML टेक्स्ट क्लीनर
def clean_subtitle_data(raw_text):
    # XML टेक्स्ट क्लीनर
    if "<text" in raw_text:
        try:
            root = ET.fromstring(raw_text)
            lines = [html.unescape(node.text or '') for node in root.findall('.//text')]
            return " ".join([l.strip() for l in lines if l.strip()])
        except Exception:
            pass
            
    # WebVTT / Plain lines क्लीनर
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

# 100% फ्री मल्टी-स्ट्रीम ट्रांसक्रिप्ट इंजन (No AI Token Quota Used)
def fetch_bulletproof_transcript(video_id):
    # 1. YouTube Web Timedtext API
    timedtext_urls = [
        f"https://www.youtube.com/api/timedtext?v={video_id}&lang=hi",
        f"https://www.youtube.com/api/timedtext?v={video_id}&lang=en",
        f"https://www.youtube.com/api/timedtext?v={video_id}&lang=hi&fmt=vtt",
        f"https://www.youtube.com/api/timedtext?v={video_id}&lang=en&fmt=vtt"
    ]
    for t_url in timedtext_urls:
        try:
            res = requests.get(t_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
            if res.status_code == 200 and len(res.text.strip()) > 30:
                cleaned = clean_subtitle_data(res.text)
                if len(cleaned) > 20:
                    return cleaned
        except Exception:
            continue

    # 2. ग्लोबल मिरर नेटवर्क बैकअप
    mirrors = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://yewtu.be",
        "https://invidious.jing.rocks"
    ]
    for base in mirrors:
        try:
            api_url = f"{base}/api/v1/captions/{video_id}"
            res = requests.get(api_url, timeout=4)
            if res.status_code == 200:
                caps = res.json()
                if caps:
                    path = caps[0].get("url")
                    u = base + path if path.startswith("/") else path
                    c_res = requests.get(u, timeout=4)
                    if c_res.status_code == 200:
                        text = clean_subtitle_data(c_res.text)
                        if len(text) > 20:
                            return text
        except Exception:
            continue
            
    raise Exception("इस वीडियो में सबटाइटल/कैप्शन उपलब्ध नहीं हैं। कृपया कोई अन्य वीडियो लिंक दर्ज करें जिसमें सबटाइटल ऑन हों।")

# UI इनपुट
yt_url = st.text_input("YouTube Video URL दर्ज करें:", placeholder="https://youtu.be/... या https://www.youtube.com/watch?v=...")
translate_option = st.selectbox(
    "ट्रांसक्रिप्ट किस भाषा में चाहिए?",
    ["मूल भाषा (Original Transcript)", "हिंदी (Hindi अनुवाद)", "English (अनुवाद)", "ଓଡ଼ିଆ (Odia अनुवाद)"]
)
gemini_key_input = st.text_input("Google Gemini API Key (केवल भाषा बदलने/अनुवाद के लिए):", value=secrets_gemini, type="password")

if st.button("📥 Get Transcript", key="btn_trans_run"):
    if not yt_url.strip():
        st.error("कृपया यूट्यूब वीडियो का लिंक दर्ज करें।")
    else:
        video_id = extract_video_id(yt_url)
        if not video_id:
            st.error("अमान्य YouTube URL! कृपया सही लिंक दर्ज करें।")
        else:
            with st.spinner("वीडियो से टेक्स्ट निकाला जा रहा है..."):
                try:
                    final_text = fetch_bulletproof_transcript(video_id)
                    
                    # यदि अनुवाद चाहिए और Key उपलब्ध है
                    if translate_option != "मूल भाषा (Original Transcript)" and gemini_key_input.strip():
                        with st.spinner("AI द्वारा भाषा अनुवाद किया जा रहा है..."):
                            try:
                                client = genai.Client(api_key=gemini_key_input)
                                target_lang_name = "Hindi" if "हिंदी" in translate_option else ("Odia" if "ଓଡ଼ିଆ" in translate_option else "English")
                                res = client.models.generate_content(
                                    model="gemini-3.6-flash",
                                    contents=f"Translate the following speech cleanly and naturally into {target_lang_name}:\n\n{final_text}"
                                )
                                final_text = res.text
                            except Exception as trans_err:
                                st.warning(f"अनुवाद नहीं हो सका, मूल भाषा में ट्रांसक्रिप्ट दिखाया जा रहा है: {trans_err}")

                    st.success("🎉 ट्रांसक्रिप्ट सफलतापूर्वक प्राप्त हो गया!")
                    st.text_area("वीडियो का पूरा टेक्स्ट (Transcript):", value=final_text, height=270)
                    st.download_button(
                        label="⬇️ Download Transcript (TXT)", 
                        data=final_text, 
                        file_name=f"transcript_{video_id}.txt", 
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"त्रुटि: {e}")
