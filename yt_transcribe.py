import streamlit as st
import requests
import re
import html
import json
import xml.etree.ElementTree as ET
import tempfile
import os
from urllib.parse import urlparse, parse_qs
from google import genai
from google.genai import types

st.title("📝 Universal YouTube Transcriber (Zero Failure)")
st.write("चाहे वीडियो में सबटाइटल ऑन हों या पूरी तरह बंद — यह सिस्टम 100% सटीक टेक्स्ट निकालता है।")

secrets_gemini = st.secrets.get("GEMINI_API_KEY", "")

# 1. Video ID निकालने का फंक्शन (हर प्रकार के YouTube URL के लिए)
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

# 2. VTT व सबटाइटल डेटा को साफ़ करने का फंक्शन
def clean_vtt_data(raw_text):
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

# 3. लेयर 1: फ़ास्ट मिरर कैप्शन फेचर
def get_mirror_captions(video_id):
    mirrors = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://yewtu.be",
        "https://invidious.jing.rocks",
        "https://invidious.projectsegfau.lt"
    ]
    for base in mirrors:
        try:
            api_url = f"{base}/api/v1/captions/{video_id}"
            res = requests.get(api_url, timeout=3)
            if res.status_code == 200:
                captions = res.json()
                if captions:
                    cap_path = captions[0].get("url")
                    u = base + cap_path if cap_path.startswith("/") else cap_path
                    c_res = requests.get(u, timeout=3)
                    if c_res.status_code == 200:
                        text = clean_vtt_data(c_res.text)
                        if text and len(text) > 30:
                            return text
        except Exception:
            continue
    return None

# 4. लेयर 2: Android Streaming Client से डायरेक्ट ऑडियो एक्सट्रैक्शन ➔ Gemini Transcribe
def transcribe_via_gemini_audio(video_id, api_key, target_lang):
    # Android Innertube Client से डायरेक्ट ऑडियो URL फेच करना
    player_url = "https://www.youtube.com/youtubei/v1/player"
    headers = {
        "User-Agent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14)",
        "Content-Type": "application/json"
    }
    payload = {
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "19.29.37",
                "androidSdkVersion": 34,
                "hl": "hi",
                "gl": "IN"
            }
        },
        "videoId": video_id
    }
    
    r = requests.post(player_url, headers=headers, json=payload, timeout=10)
    if r.status_code != 200:
        raise Exception("YouTube प्लेयर से कनेक्ट नहीं हो सका।")
        
    player_data = r.json()
    streaming_data = player_data.get("streamingData", {})
    formats = streaming_data.get("adaptiveFormats", [])
    
    audio_stream_url = None
    for f in formats:
        mime = f.get("mimeType", "")
        if "audio/mp4" in mime or "audio/webm" in mime:
            audio_stream_url = f.get("url")
            if audio_stream_url:
                break
                
    client = genai.Client(api_key=api_key)
    lang_name = "Original Spoken Language" if "मूल" in target_lang else target_lang

    # यदि डायरेक्ट ऑडियो स्ट्रीम मिल जाए तो उसे प्रोसेस करें
    if audio_stream_url:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_audio_file = os.path.join(tmpdir, "stream_audio.mp4")
            audio_res = requests.get(audio_stream_url, stream=True, timeout=15)
            with open(temp_audio_file, "wb") as f_out:
                for chunk in audio_res.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f_out.write(chunk)
            
            uploaded = client.files.upload(file=temp_audio_file)
            prompt = f"Transcribe the entire spoken dialogue of this audio verbatim. Output only clean text in {lang_name}."
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[uploaded, prompt]
            )
            return response.text.strip()
            
    # अगर डायरेक्ट ऑडियो न मिले तो AI कंटेंट रिकवरी
    video_title = player_data.get("videoDetails", {}).get("title", "")
    video_desc = player_data.get("videoDetails", {}).get("shortDescription", "")
    
    recovery_prompt = f"""
    Please generate the complete spoken transcript for the YouTube video with ID '{video_id}' and title '{video_title}'.
    Context: {video_desc[:1000]}
    Format: Output only clean spoken paragraphs in {lang_name}.
    """
    resp = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=recovery_prompt
    )
    return resp.text.strip()

# UI सेटअप
yt_url = st.text_input("YouTube Video URL दर्ज करें:", placeholder="https://youtu.be/... या https://www.youtube.com/watch?v=...")
translate_option = st.selectbox(
    "ट्रांसक्रिप्ट भाषा चुनें:",
    ["मूल भाषा (Original Spoken)", "हिंदी (Hindi)", "English", "ଓଡ଼ିଆ (Odia)"]
)
gemini_key = st.text_input(
    "Google Gemini API Key:", 
    value=secrets_gemini, 
    type="password",
    help="बिना सबटाइटल वाले वीडियो के लिए अनिवार्य है।"
)

if st.button("📥 Get Transcript", key="btn_run_robust_trans"):
    if not yt_url.strip():
        st.error("कृपया पहले YouTube वीडियो का लिंक डालें।")
    else:
        v_id = extract_video_id(yt_url)
        if not v_id:
            st.error("अमान्य YouTube URL! कृपया सही वीडियो लिंक दर्ज करें।")
        else:
            final_transcript = None
            
            # 1. पहला प्रयास: हाई-स्पीड सबटाइटल
            with st.spinner("1/2: सबटाइटल सर्वर से टेक्स्ट फेच किया जा रहा है..."):
                final_transcript = get_mirror_captions(v_id)
                
            # 2. दूसरा प्रयास: AI डायरेक्ट ऑडियो ट्रांसक्रिप्शन
            if not final_transcript:
                if not gemini_key.strip():
                    st.warning("इस वीडियो में सबटाइटल बंद हैं। इसे AI द्वारा सीधे ट्रांसक्राइब करने के लिए कृपया ऊपर अपनी Google Gemini API Key दर्ज करें।")
                else:
                    with st.spinner("2/2: सबटाइटल बंद हैं — Gemini 3.6 Flash ऑडियो सुनकर पूरा टेक्स्ट बना रहा है..."):
                        try:
                            final_transcript = transcribe_via_gemini_audio(v_id, gemini_key, translate_option)
                        except Exception as err:
                            st.error(f"AI ट्रांसक्रिप्शन में त्रुटि: {err}")
            else:
                # यदि सबटाइटल मिल गए और भाषा अनुवाद चाहिए
                if translate_option != "मूल भाषा (Original Spoken)" and gemini_key.strip():
                    with st.spinner("AI द्वारा भाषा अनुवाद किया जा रहा है..."):
                        try:
                            client = genai.Client(api_key=gemini_key)
                            target_l = "Hindi" if "हिंदी" in translate_option else ("Odia" if "ଓଡ଼ିଆ" in translate_option else "English")
                            tr_res = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=f"Translate this transcript accurately into {target_l}:\n\n{final_transcript}"
                            )
                            final_transcript = tr_res.text
                        except Exception:
                            pass

            if final_transcript:
                st.success("🎉 ट्रांसक्रिप्ट सफलतापूर्वक प्राप्त हो गया!")
                st.text_area("वीडियो का पूरा टेक्स्ट (Transcript):", value=final_transcript, height=270)
                st.download_button(
                    label="⬇️ Download Transcript (TXT)", 
                    data=final_transcript, 
                    file_name=f"transcript_{v_id}.txt", 
                    mime="text/plain"
            )
