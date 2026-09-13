import streamlit as st
import requests
import re
import html
from urllib.parse import urlparse, parse_qs
from google import genai

st.set_page_config(page_title="YouTube Video to Transcript", page_icon="📝", layout="centered")

st.title("📝 YouTube Video to Transcript")
st.write("यूट्यूब वीडियो का लिंक डालें और उसका पूरा टेक्स्ट प्राप्त करें।")

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
gemini_key = st.text_input("Google Gemini API Key (अनुवाद के लिए):", value=secrets_gemini, type="password")

if st.button("📥 Get Transcript"):
    if not yt_url.strip():
        st.error("कृपया वीडियो का लिंक दर्ज करें।")
    else:
        video_id = extract_video_id(yt_url)
        if not video_id:
            st.error("अमान्य YouTube URL!")
        else:
            with st.spinner("ट्रांसक्रिप्ट निकाला जा रहा है..."):
                mirror_instances = [
                    "https://inv.nadeko.net",
                    "https://invidious.nerdvpn.de",
                    "https://yewtu.be",
                    "https://invidious.jing.rocks"
                ]
                final_text = None
                for base_url in mirror_instances:
                    try:
                        api_url = f"{base_url}/api/v1/captions/{video_id}"
                        res = requests.get(api_url, timeout=5)
                        if res.status_code == 200:
                            captions = res.json()
                            if captions:
                                cap_path = captions[0].get("url")
                                full_url = base_url + cap_path if cap_path.startswith("/") else cap_path
                                c_res = requests.get(full_url, timeout=5)
                                if c_res.status_code == 200:
                                    final_text = clean_vtt_text(c_res.text)
                                    if final_text:
                                        break
                    except Exception:
                        continue
                
                if not final_text:
                    st.error("इस वीडियो में सबटाइटल (Captions) बंद हैं। YouTube पर जिस वीडियो में Captions ऑन होते हैं, उसी का टेक्स्ट निकाला जा सकता है।")
                else:
                    if translate_option != "मूल भाषा (Original Transcript)" and gemini_key.strip():
                        with st.spinner("अनुवाद किया जा रहा है..."):
                            try:
                                client = genai.Client(api_key=gemini_key)
                                lang_target = "Hindi" if "हिंदी" in translate_option else "English"
                                res = client.models.generate_content(
                                    model="gemini-3.6-flash",
                                    contents=f"Translate the following text accurately into {lang_target}:\n\n{final_text}"
                                )
                                final_text = res.text
                            except Exception as e:
                                st.warning(f"अनुवाद नहीं हो सका: {e}")
                                
                    st.success("🎉 ट्रांसक्रिप्ट प्राप्त हो गया!")
                    st.text_area("वीडियो का पूरा टेक्स्ट:", value=final_text, height=260)
                    st.download_button("⬇️ Download TXT", data=final_text, file_name=f"transcript_{video_id}.txt", mime="text/plain")
      
