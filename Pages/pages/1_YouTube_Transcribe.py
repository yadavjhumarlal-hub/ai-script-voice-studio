import streamlit as st
import requests
import re
import html
from urllib.parse import urlparse, parse_qs
from google import genai

st.set_page_config(page_title="YouTube Video Transcribe", page_icon="📝", layout="centered")

st.title("📝 YouTube Video to Transcript")
st.write("यूट्यूब वीडियो का लिंक डालें और उसका पूरा टेक्स्ट प्राप्त करें।")

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

# सबटाइटल क्लीनर
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

yt_url = st.text_input("YouTube Video URL दर्ज करें:", placeholder="https://youtu.be/... या https://www.youtube.com/watch?v=...")
translate_option = st.selectbox(
    "ट्रांसक्रिप्ट किस भाषा में चाहिए?",
    ["मूल भाषा (Original Transcript)", "हिंदी में अनुवाद (Translate to Hindi)", "English में अनुवाद (Translate to English)"]
)
gemini_key_t = st.text_input("Google Gemini API Key (अनुवाद के लिए):", value=secrets_gemini, type="password")

if st.button("📥 Get Transcript"):
    if not yt_url.strip():
        st.error("कृपया यूट्यूब वीडियो का लिंक डालें।")
    else:
        v_id = extract_video_id(yt_url)
        if not v_id:
            st.error("अमान्य YouTube URL!")
        else:
            with st.spinner("वीडियो से टेक्स्ट निकाला जा रहा है..."):
                mirrors = [
                    "https://inv.nadeko.net",
                    "https://invidious.nerdvpn.de",
                    "https://yewtu.be",
                    "https://invidious.jing.rocks"
                ]
                final_text = None
                for base in mirrors:
                    try:
                        res = requests.get(f"{base}/api/v1/captions/{v_id}", timeout=5)
                        if res.status_code == 200:
                            caps = res.json()
                            if caps:
                                path = caps[0].get("url")
                                u = base + path if path.startswith("/") else path
                                c_res = requests.get(u, timeout=5)
                                if c_res.status_code == 200:
                                    final_text = clean_vtt_text(c_res.text)
                                    if final_text:
                                        break
                    except Exception:
                        continue

                if not final_text:
                    st.error("इस वीडियो में सबटाइटल (Captions) उपलब्ध नहीं हैं।")
                else:
                    if translate_option != "मूल भाषा (Original Transcript)" and gemini_key_t.strip():
                        with st.spinner("AI द्वारा अनुवाद किया जा रहा है..."):
                            try:
                                client = genai.Client(api_key=gemini_key_t)
                                lang_t = "Hindi" if "हिंदी" in translate_option else "English"
                                prompt = f"Translate the following text accurately into {lang_t}:\n\n{final_text}"
                                res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
                                final_text = res.text
                            except Exception as e:
                                st.warning(f"अनुवाद में त्रुटि: {e}")

                    st.success("🎉 ट्रांसक्रिप्ट सफलतापूर्वक प्राप्त हो गया!")
                    st.text_area("वीडियो का पूरा टेक्स्ट (Transcript):", value=final_text, height=260)
                    st.download_button("⬇️ Download TXT", data=final_text, file_name=f"transcript_{v_id}.txt", mime="text/plain")
      
