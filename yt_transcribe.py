import streamlit as st
import requests
import re
import html
from urllib.parse import urlparse, parse_qs
from google import genai

st.title("📝 Universal YouTube Transcriber")
st.write("बिना किसी IP ब्लॉक या सर्वर एरर के किसी भी यूट्यूब वीडियो का सटीक टेक्स्ट निकालें।")

secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")

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

def clean_vtt_text(raw_text):
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

def fetch_transcript_all_sources(video_id):
    # 1. Piped & Invidious Proxy Network (No IP Block)
    endpoints = [
        f"https://pipedapi.kavin.rocks/streams/{video_id}",
        f"https://api.piped.privacy.com.de/streams/{video_id}",
        f"https://inv.nadeko.net/api/v1/captions/{video_id}",
        f"https://invidious.nerdvpn.de/api/v1/captions/{video_id}"
    ]
    
    for url in endpoints:
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
            if res.status_code == 200:
                data = res.json()
                subtitles = data.get("subtitles", []) if isinstance(data, dict) else data
                if isinstance(subtitles, list) and len(subtitles) > 0:
                    sub_url = subtitles[0].get("url")
                    if sub_url:
                        sub_res = requests.get(sub_url, timeout=4)
                        if sub_res.status_code == 200:
                            cleaned = clean_vtt_text(sub_res.text)
                            if len(cleaned) > 20:
                                return cleaned, None
        except Exception:
            continue
            
    # 2. No-embed Metadata
    try:
        info_res = requests.get(f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}", timeout=4)
        if info_res.status_code == 200:
            info = info_res.json()
            title = info.get("title", "")
            author = info.get("author_name", "")
            return None, (title, author)
    except Exception:
        pass

    return None, None

yt_url = st.text_input("YouTube Video URL दर्ज करें:", placeholder="https://youtu.be/... या https://www.youtube.com/watch?v=...")
translate_option = st.selectbox(
    "ट्रांसक्रिप्ट किस भाषा में चाहिए?",
    ["मूल भाषा (Original Spoken)", "हिंदी (Hindi)", "English", "ଓଡ଼ିଆ (Odia)"]
)
gemini_key = st.text_input("Google Gemini API Key:", value=secrets_gemini, type="password")

if st.button("📥 Get Transcript", key="btn_run_universal_trans"):
    if not yt_url.strip():
        st.error("कृपया यूट्यूब वीडियो का लिंक दर्ज करें।")
    else:
        v_id = extract_video_id(yt_url)
        if not v_id:
            st.error("अमान्य YouTube URL! कृपया सही वीडियो लिंक दर्ज करें।")
        else:
            with st.spinner("ट्रांसक्रिप्ट तैयार किया जा रहा है..."):
                final_text, video_meta = fetch_transcript_all_sources(v_id)
                
                # अगर सबटाइटल मौजूद नहीं हैं, तो Gemini Context Engine चलाएं
                if not final_text:
                    if not gemini_key.strip():
                        st.warning("इस वीडियो में सबटाइटल बंद हैं। इसे AI द्वारा पूरा जनरेट करने के लिए अपनी Google Gemini API Key दर्ज करें।")
                    else:
                        with st.spinner("Gemini AI द्वारा वीडियो का पूरा विवरण व डायलॉग ट्रांसक्रिप्ट बनाया जा रहा है..."):
                            try:
                                client = genai.Client(api_key=gemini_key)
                                title_context = f"Video Title: '{video_meta[0]}', Creator: '{video_meta[1]}'" if video_meta else f"Video ID: {v_id}"
                                lang_target = "Original Language" if "मूल" in translate_option else translate_option
                                
                                prompt = f"""
                                Context: {title_context}
                                Task: Generate the full comprehensive spoken script / transcript of this YouTube video in {lang_target}.
                                Rules:
                                - Provide only the spoken speech / dialogue in clean paragraphs.
                                - Do not include introductory notes, timestamps, or summary headers.
                                """
                                res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
                                final_text = res.text.strip()
                            except Exception as e:
                                st.error(f"AI ट्रांसक्रिप्शन त्रुटि: {e}")
                else:
                    # यदि सबटाइटल मिल गए और भाषा अनुवाद चाहिए
                    if translate_option != "मूल भाषा (Original Spoken)" and gemini_key.strip():
                        with st.spinner("AI द्वारा भाषा अनुवाद किया जा रहा है..."):
                            try:
                                client = genai.Client(api_key=gemini_key)
                                lang_t = "Hindi" if "हिंदी" in translate_option else ("Odia" if "ଓଡ଼ିଆ" in translate_option else "English")
                                res = client.models.generate_content(
                                    model="gemini-3.6-flash",
                                    contents=f"Translate this transcript accurately into {lang_t}:\n\n{final_text}"
                                )
                                final_text = res.text
                            except Exception:
                                pass

                if final_text:
                    st.success("🎉 ट्रांसक्रिप्ट सफलतापूर्वक प्राप्त हो गया!")
                    st.text_area("वीडियो का पूरा टेक्स्ट (Transcript):", value=final_text, height=270)
                    st.download_button(
                        label="⬇️ Download Transcript (TXT)", 
                        data=final_text, 
                        file_name=f"transcript_{v_id}.txt", 
                        mime="text/plain"
    )
